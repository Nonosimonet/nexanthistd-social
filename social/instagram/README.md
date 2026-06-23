# 📣 Publication automatique Instagram — NexanthisTD

Poste automatiquement sur **@nexanthistd** via l'**API officielle Meta**
(*Instagram API with Instagram Login* — méthode « connexion professionnelle Instagram »).
Aucun bot "navigateur" → 100% conforme aux conditions Instagram, zéro risque de bannissement.
**Pas besoin de Page Facebook** avec cette méthode.

## Comment ça marche

```
GitHub Actions (cron quotidien, 18h Paris)
        │
        ▼
  social/instagram/post.py  ──► choisit le post du jour dans content.json (rotation)
        │
        ▼
  API Meta (graph.instagram.com)  ──► 1. crée le conteneur média
                                       (image servie via raw.githubusercontent.com)
                                      2. publie sur Instagram
```

## Arborescence

```
social/
  instagram/
    post.py          # script de publication (lance par GitHub Actions)
    token_tool.py    # verifie le token + le renouvelle tous les 60 jours
    content.json     # banque de contenu (legendes EN + nom du fichier image)
    requirements.txt # (aucune dependance externe : stdlib uniquement)
    README.md        # ce fichier
  media/             # les IMAGES a publier (commitees, servies en URL publique)
.github/workflows/instagram-post.yml
```

---

## Installation (à faire une fois)

### 1. App Meta (déjà faite ✅)
- App de type **Business** sur [developers.facebook.com](https://developers.facebook.com).
- Produit **Instagram** ajouté → *« Configuration de l'API avec la connexion professionnelle Instagram »*.
- Compte `@nexanthistd` ajouté comme **testeur Instagram** (rôle accepté côté Instagram).
- **Section 1 → « Générer un token »** → token longue durée copié.

### 2. Récupérer le token
Le token vient directement du bouton **« Générer un token »** du tableau de bord Meta.
L'`IG_USER_ID` (ex. `17841422025122390`) est **déduit automatiquement** depuis le token,
pas besoin de le fournir.

### 3. Vérifier que le token marche (sur ta machine)
```powershell
$env:IG_ACCESS_TOKEN="<ton token>"
python social/instagram/token_tool.py
```
Ça doit afficher `@nexanthistd` + l'IG_USER_ID. Le token ne quitte pas ta machine.

### 4. Ajouter le secret GitHub
Repo GitHub → **Settings → Secrets and variables → Actions → New repository secret** :
- `IG_ACCESS_TOKEN` = le token

> 🔒 Ne JAMAIS mettre le token dans le code ou un commit. Uniquement dans les Secrets (chiffrés).
> (Optionnel : tu peux aussi ajouter `IG_USER_ID`, mais ce n'est pas nécessaire.)

### 5. Déposer les visuels
Mets les images **JPEG** dans `social/media/` avec **exactement** les noms attendus par
`content.json` (ex. `fusion_pyroglace.jpg`, `tower_voltex.jpg`, `enemy_void_golem.jpg`…).
Format conseillé : carré **1080×1080**. ⚠️ JPEG uniquement (l'API refuse les PNG).

---

## Tester

**Test à blanc** (ne publie rien, vérifie la sélection + la légende + la présence de l'image) :
```powershell
$env:DRY_RUN="1"; python social/instagram/post.py
```

**Test réel via GitHub** : onglet **Actions → Instagram - post auto → Run workflow**
(tu peux forcer un `post_id` précis, ou mettre `dry_run = 1`).

---

## Réglages courants

| Quoi | Où |
|------|-----|
| Heure / fréquence de publication | `cron` dans `.github/workflows/instagram-post.yml` |
| Légendes & posts | `content.json` |
| Forcer un post précis | input `post_id` au lancement manuel |
| Choix de l'image | champ `image` de chaque post (= fichier dans `social/media/`) |

### Changer la fréquence (exemples de cron, en UTC)
- 1×/jour à 18h Paris → `0 16 * * *`
- 2×/jour (12h + 19h Paris) → `0 10,17 * * *`
- 3×/semaine (lun/mer/ven 18h) → `0 16 * * 1,3,5`

---

## ⚠️ Maintenance : renouveler le token tous les ~60 jours
Le token longue durée expire après **60 jours**. Avant l'échéance :
```powershell
$env:IG_ACCESS_TOKEN="<token actuel>"; $env:REFRESH="1"
python social/instagram/token_tool.py
```
Copie le **nouveau token** affiché dans le secret `IG_ACCESS_TOKEN`. (Automatisable plus tard.)

## Limites API à connaître
- **100 publications / 24h** (large pour 1–3 posts/jour).
- Les images doivent être **JPEG** et accessibles via **URL publique** (assuré par GitHub raw).
- Pas de support des **Stories** ; les **Reels** nécessitent une vidéo hébergée (étape future).
