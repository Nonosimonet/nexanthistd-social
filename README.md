# NexanthisTD Social 📣

Pipeline de publication automatique pour le compte Instagram
**[@nexanthistd](https://instagram.com/nexanthistd)** — le jeu **NEXANTHIS — Tower Defense**,
dispo sur Google Play depuis le 29/07/2026.

API officielle Meta (*Instagram API with Instagram Login*, `graph.instagram.com`) + GitHub Actions.
Pas de Page Facebook requise, aucun bot « navigateur ».

⚠️ Ce repo est **public** : il sert d'hébergement média pour l'API Instagram (Meta télécharge
les vidéos et images via les URLs `raw.githubusercontent.com`). N'y mettre **aucun secret** —
uniquement du contenu destiné à être publié. Le token vit dans les GitHub Secrets (chiffrés).

Même pipeline que `monirate-social`.

## Fonctionnement

```
posts/queue/*.json  ──(cron 14h47 UTC)──►  Instagram Reel/Post  ──►  posts/published/
```

1. Déposer la vidéo dans `media/reels/` (ou l'image dans `media/`), la légende dans `captions/`
2. Créer un fichier dans `posts/queue/` :
   ```json
   {
     "media": "media/reels/ma-video.mp4",
     "cover": "media/reels/ma-video_cover.jpg",
     "caption_file": "captions/ma-legende.txt",
     "type": "REELS",
     "publish_at": "2026-08-04"
   }
   ```
   `cover` et `publish_at` sont optionnels. Sans `cover`, Instagram prend la 1re image du Reel.
3. Commit + push → le workflow tourne chaque jour et publie le prochain post « échu »
   (ordre alphabétique des fichiers → **préfixer par la date**).
4. Lancement manuel : onglet **Actions → Publish to Instagram → Run workflow**.

Un carrousel (2 à 10 images) se déclare avec `{"type": "CAROUSEL", "images": [...]}`.

### Cadence : 1 post tous les 2 jours

Le cron tourne **tous les jours**, mais `publish.mjs` refuse de publier si le dernier post
date de moins de `MIN_DAYS_BETWEEN_POSTS` **jours de calendrier** (**2** depuis le 16 nov. 2026, réglé
dans `publish.yml`). La date du dernier envoi réussi est stockée dans
`posts/last_published.json`, committée par le workflow.

Un `cron: "0 15 */3 * *"` ne suffirait **pas** : le champ jour-du-mois repart à 1 à chaque
mois, donc deux posts se retrouveraient collés après le 31.

Pour forcer une publication hors cadence : lancer le workflow à la main après avoir
supprimé `posts/last_published.json`.

### Heure de publication

Cron à **14h47 UTC** pour viser ~15h UTC = **17h Paris** (heure d'été). On part quelques
minutes plus tôt car GitHub ne garantit pas l'heure des workflows planifiés (file d'attente,
pire aux minutes rondes — d'où `:47`) et Meta doit encore encoder la vidéo.

⏰ **Le cron est en UTC et ne suit pas l'heure d'été.** Fin octobre la publication tombera
à 16h Paris ; passer le cron à `47 15 * * *` pour rester à 17h.

## Arborescence

```
posts/queue/       # les posts a publier (1 fichier JSON = 1 post, prefixe par la date)
posts/published/   # les posts deja publies (deplaces automatiquement par le workflow)
posts/last_published.json   # date du dernier envoi reussi (garde-fou de cadence)
captions/          # les legendes (.txt, UTF-8)
captions/backlog/  # legendes deja ecrites, EN ATTENTE DE VISUEL -> jamais publiees
media/             # images
media/reels/       # videos + vignettes de couverture
scripts/publish.mjs        # publication (lance par le workflow)
scripts/refresh_token.mjs  # renouvellement du token 60 jours
```

`captions/backlog/` contient 24 légendes déjà rédigées (tours, fusions, ennemis, tips) qui
n'ont pas encore leur visuel. Elles ne partent **jamais** toutes seules : pour en publier une,
déposer son image puis créer un fichier dans `posts/queue/`.

## Secrets à configurer (Settings → Secrets → Actions)

| Secret | Contenu |
|---|---|
| `IG_ACCESS_TOKEN` | Token long-lived de l'app Meta « NexanthisTD Bot » (permissions `instagram_business_basic`, `instagram_business_content_publish`) |

⏰ **Le token expire après ~60 jours.** Dashboard Meta → app **NexanthisTD Bot** → Instagram
→ Configuration de l'API → « Générer un token », puis recoller la valeur dans le secret.

## Limites connues de l'API

- 🎵 **Pas de musique Instagram** ajoutable via l'API → un Reel qui vise la portée d'un son
  tendance gagne à être publié à la main depuis l'app.
- 🕐 Quota : max 25 publications API / 24 h (largement suffisant).
- 📐 Reels : MP4 H.264, 9:16, ≤ 90 s recommandé.
- 🚫 Pas de Stories via l'API.

## Test local

```bash
IG_ACCESS_TOKEN=xxx MEDIA_BASE_URL=https://raw.githubusercontent.com/Nonosimonet/nexanthistd-social/main \
  node scripts/publish.mjs
```
