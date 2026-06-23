#!/usr/bin/env python3
"""
Outil de gestion du token Instagram (methode "Instagram login" / Business Login).

Deux usages :

  1) VERIFIER que le token marche (et afficher le compte + l'ID) :
       $env:IG_ACCESS_TOKEN="<ton token>"; python social/instagram/token_tool.py

  2) RENOUVELER le token longue duree (a faire avant l'echeance des 60 jours) :
       $env:IG_ACCESS_TOKEN="<ton token actuel>"; $env:REFRESH="1"; python social/instagram/token_tool.py
     -> affiche un NOUVEAU token valable 60 jours (a recopier dans le secret GitHub).

Aucune cle secrete requise : le renouvellement utilise grant_type=ig_refresh_token.
"""

import json
import os
import ssl
import sys
from urllib.parse import quote
import urllib.request
import urllib.error

GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v21.0")
GRAPH = f"https://graph.instagram.com/{GRAPH_VERSION}"
GRAPH_ROOT = "https://graph.instagram.com"


def _read(url: str, context=None) -> dict:
    with urllib.request.urlopen(url, timeout=60, context=context) as resp:
        return json.loads(resp.read().decode())


def get(url: str) -> dict:
    try:
        return _read(url)
    except urllib.error.HTTPError as e:
        print(f"Erreur API ({e.code}):\n{e.read().decode(errors='replace')}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        # Cas Windows + antivirus/proxy qui inspecte le HTTPS avec un certificat non conforme.
        # Repli SANS verification : TEST LOCAL UNIQUEMENT (la prod tourne sur GitHub Actions/Linux,
        # qui n'a pas ce souci et reste 100% verifiee via post.py).
        if "CERTIFICATE_VERIFY_FAILED" not in str(getattr(e, "reason", e)):
            print(f"Erreur reseau : {getattr(e, 'reason', e)}", file=sys.stderr)
            sys.exit(1)
        print("   [!] SSL bloque en local (antivirus/proxy qui inspecte le HTTPS).")
        print("   [!] Nouvelle tentative SANS verification du certificat -- test local uniquement.")
        print("   [!] Aucun impact sur la prod : GitHub Actions n'a pas ce probleme.")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            return _read(url, context=ctx)
        except urllib.error.HTTPError as e2:
            print(f"Erreur API ({e2.code}):\n{e2.read().decode(errors='replace')}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        print("Definis IG_ACCESS_TOKEN (voir docstring).", file=sys.stderr)
        sys.exit(1)

    # 1) Verification : qui est-ce ?
    print("-> Verification du token...")
    me = get(f"{GRAPH}/me?fields=user_id,username&access_token={quote(token)}")
    uid = me.get("user_id") or me.get("id")
    if not uid:
        print(f"Token invalide ou compte introuvable : {me}", file=sys.stderr)
        sys.exit(1)
    print(f"   OK -> @{me.get('username','?')}  (IG_USER_ID = {uid})")

    if os.environ.get("REFRESH") != "1":
        print("\nToken valide. (Ajoute REFRESH=1 pour generer un token frais de 60 jours.)")
        return

    # 2) Renouvellement (token longue duree -> +60 jours)
    print("-> Renouvellement du token longue duree...")
    refreshed = get(
        f"{GRAPH_ROOT}/refresh_access_token?grant_type=ig_refresh_token"
        f"&access_token={quote(token)}"
    )
    new_token = refreshed.get("access_token")
    if not new_token:
        print(f"Echec du renouvellement : {refreshed}", file=sys.stderr)
        sys.exit(1)
    days = int(refreshed.get("expires_in", 0)) // 86400
    print("\n" + "=" * 60)
    print(f"NOUVEAU token (valide ~{days} jours) -> a coller dans le secret GitHub IG_ACCESS_TOKEN :")
    print("=" * 60)
    print(new_token)


if __name__ == "__main__":
    main()
