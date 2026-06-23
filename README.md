# NexanthisTD — bot Instagram

Publication automatique sur **[@nexanthistd](https://instagram.com/nexanthistd)** via l'API officielle Meta
(*Instagram API with Instagram Login*) + **GitHub Actions**.

Ce dépôt est **public** uniquement pour que Meta puisse récupérer les images des posts
(via `raw.githubusercontent.com`). Il ne contient **aucune donnée sensible** :
le token d'accès est stocké dans les **GitHub Secrets** (chiffrés).

👉 Toute la doc d'installation et d'utilisation est dans **[social/instagram/README.md](social/instagram/README.md)**.

## En bref
- `social/instagram/` — le code (publication, gestion du token, banque de contenu)
- `social/media/` — les visuels JPEG des posts
- `.github/workflows/instagram-post.yml` — la planification (cron quotidien)
