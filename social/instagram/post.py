#!/usr/bin/env python3
"""
Publication automatique d'un post Instagram pour NexanthisTD.

Utilise l'API officielle Meta (Instagram API with Instagram Login - Content Publishing).
Aucune automatisation "navigateur" : 100% conforme aux conditions Meta.

Variables d'environnement requises :
  IG_ACCESS_TOKEN   - Token Instagram longue duree (60 jours)
  GITHUB_REPOSITORY - "owner/repo" (fourni automatiquement par GitHub Actions)

Optionnelles :
  IG_USER_ID        - ID du compte Instagram (ex: 17841422025122390).
                      Si absent, il est deduit automatiquement depuis le token.
  MEDIA_BRANCH      - branche ou sont commitees les images (defaut: main)
  POST_ID           - force un post precis par son "id" (sinon rotation par date)
  DRY_RUN           - "1" pour tout valider SANS publier (test a blanc)
  GRAPH_VERSION     - version de l'API (defaut: v21.0)
"""

import json
import os
import sys
import time
from datetime import date, timezone, datetime
from pathlib import Path
from urllib.parse import quote
import urllib.request
import urllib.error

HERE = Path(__file__).resolve().parent
CONTENT_FILE = HERE / "content.json"
MEDIA_DIR = HERE.parent / "media"  # social/media/

GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v21.0")
# Methode "Instagram login" (Business Login) -> API hebergee sur graph.instagram.com
GRAPH = f"https://graph.instagram.com/{GRAPH_VERSION}"


def fail(msg: str) -> "None":
    print(f"::error::{msg}", file=sys.stderr)
    sys.exit(1)


def http_post(url: str, params: dict) -> dict:
    data = "&".join(f"{k}={quote(str(v))}" for k, v in params.items()).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        fail(f"Erreur API Meta ({e.code}) sur {url}\n{body}")
    except urllib.error.URLError as e:
        fail(f"Erreur reseau sur {url}: {e}")
    return {}


def http_get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        fail(f"Erreur API Meta ({e.code}) sur {url}\n{body}")
    return {}


def pick_post(posts: list) -> dict:
    """Choisit le post du jour. POST_ID force un post precis, sinon rotation par date."""
    forced = os.environ.get("POST_ID")
    if forced:
        for p in posts:
            if p.get("id") == forced:
                return p
        fail(f"POST_ID='{forced}' introuvable dans content.json")
    # Rotation deterministe : cycle sur toute la banque, 1 post / jour, sans repetition
    # tant que la banque n'est pas epuisee.
    idx = date.today().toordinal() % len(posts)
    return posts[idx]


def resolve_user_id(token: str) -> str:
    """Deduit l'ID du compte Instagram a partir du token (evite un 2e secret)."""
    me = http_get(f"{GRAPH}/me?fields=user_id,username&access_token={quote(token)}")
    uid = me.get("user_id") or me.get("id")
    if not uid:
        fail(f"Impossible de deduire l'IG_USER_ID depuis le token : {me}")
    print(f"   Compte detecte : @{me.get('username','?')} (id={uid})")
    return str(uid)


def raw_url_for(image: str, repo: str, branch: str) -> str:
    # Les images committees dans social/media/ sont servies publiquement par GitHub.
    # L'API Meta exige une URL d'image PUBLIQUE accessible (pas un upload de fichier).
    return f"https://raw.githubusercontent.com/{repo}/{branch}/social/media/{image}"


def main() -> None:
    ig_user_id = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    branch = os.environ.get("MEDIA_BRANCH", "main")
    dry_run = os.environ.get("DRY_RUN") == "1"

    if not CONTENT_FILE.exists():
        fail(f"content.json introuvable : {CONTENT_FILE}")
    content = json.loads(CONTENT_FILE.read_text(encoding="utf-8"))
    posts = content.get("posts", [])
    if not posts:
        fail("Aucun post dans content.json")

    post = pick_post(posts)
    image = post["image"]
    caption = post["caption"]

    print(f"-> Post selectionne : id='{post['id']}' ({post.get('category','?')})")
    print(f"   Image : {image}")

    # Verifie que l'image existe localement (evite un post avec image manquante)
    local_img = MEDIA_DIR / image
    if not local_img.exists():
        fail(
            f"Image manquante : {local_img}\n"
            f"Depose le fichier dans social/media/ (voir README) avant de publier."
        )

    if not repo:
        if dry_run:
            repo = "OWNER/REPO"
        else:
            fail("GITHUB_REPOSITORY non defini (necessaire pour l'URL publique de l'image)")
    image_url = raw_url_for(image, repo, branch)
    print(f"   URL publique : {image_url}")

    if dry_run:
        print("\n[DRY_RUN] Tout est valide. Aperçu de la legende :\n")
        print(caption)
        print("\n[DRY_RUN] Rien n'a ete publie.")
        return

    if not token:
        fail("IG_ACCESS_TOKEN est requis pour publier")
    if not ig_user_id:
        ig_user_id = resolve_user_id(token)

    # Etape 1 : creer le conteneur media
    print("\n-> Creation du conteneur media...")
    container = http_post(
        f"{GRAPH}/{ig_user_id}/media",
        {"image_url": image_url, "caption": caption, "access_token": token},
    )
    creation_id = container.get("id")
    if not creation_id:
        fail(f"Pas de creation_id retourne : {container}")
    print(f"   creation_id = {creation_id}")

    # Etape 2 : publier le conteneur
    print("-> Publication...")
    result = http_post(
        f"{GRAPH}/{ig_user_id}/media_publish",
        {"creation_id": creation_id, "access_token": token},
    )
    media_id = result.get("id")
    if not media_id:
        fail(f"Publication echouee : {result}")

    print(f"\n✅ Publie ! media_id = {media_id}")
    print(f"   {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
