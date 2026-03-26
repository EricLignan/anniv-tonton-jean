# Page interactive "Parcours Surprise"

Page web interactive pour offrir des messages audio/vidéo de proches sous forme de cadeaux à ouvrir un par un, avec confettis, musique de fond jazz et finale festive.

**Démo live** : https://ericlignan.github.io/famille-2026/

---

## Fonctionnalités

- **Page d'accueil** sobre et mystérieuse (pas de spoiler)
- **Grille de cadeaux** colorés (tuiles pastel en quinconce)
- **Clic = ouverture** : confettis + modal avec lecteur audio ou vidéo
- **Prénoms cachés** : révélés uniquement après ouverture du cadeau
- **Musique jazz** en fond avec fondu sonore automatique (pause pendant l'écoute d'un message)
- **Compteur** de progression ("X / N surprises découvertes")
- **Finale** : feu d'artifice + souhaits qui apparaissent en cascade + message collectif
- **Mobile-first** : fonctionne sur iPhone (Safari) et Android (Chrome)
- **Zéro backend** : page HTML statique, pas de serveur

---

## Prérequis

| Outil | Usage | Installation |
|-------|-------|-------------|
| **Python 3.10+** | Conversion audio | [python.org](https://www.python.org/downloads/) |
| **ffmpeg** | Encodage .ogg/.aac → .mp3 | `winget install ffmpeg` (Windows) ou `brew install ffmpeg` (Mac) |
| **Git** | Versionning + déploiement | [git-scm.com](https://git-scm.com/) |
| **GitHub CLI (gh)** | Création repo + GitHub Pages | `winget install GitHub.cli` ou [cli.github.com](https://cli.github.com/) |

---

## Guide pas à pas

### Étape 1 — Collecter les messages

1. Demander aux proches d'envoyer leurs messages (audio, vidéo, photo) via WhatsApp ou un formulaire
2. Télécharger tous les fichiers dans un dossier local (ex: `Downloads/Anniv/`)
3. Créer un fichier d'identification pour associer chaque fichier à une personne :

```markdown
| # | Fichier | Personne | Type |
|---|---------|----------|------|
| 1 | WhatsApp Audio ... .ogg | Prénom | Audio |
| 2 | WhatsApp Video ... .mp4 | Prénom et Prénom | Vidéo |
```

Écouter chaque fichier et remplir la colonne "Personne".

### Étape 2 — Convertir les fichiers audio

iOS Safari ne lit pas les fichiers `.ogg`. Il faut les convertir en `.mp3`.

**Option A — Script Python (recommandé)**

Adapter le script `scripts/convert_media.py` avec vos fichiers :

```python
# Modifier ces 2 variables :
SOURCE_DIR = Path(r"chemin/vers/votre/dossier/messages")
OUTPUT_DIR = Path(r"chemin/vers/le/projet/assets")

# Modifier cette liste avec vos fichiers :
MEDIA_MAP = [
    ("nom-fichier-source.ogg", "prenom.mp3", "audio"),
    ("nom-fichier-source.mp4", "prenom.mp4", "video"),
    ("nom-fichier-source.jpeg", "prenom.jpeg", "image"),
]
```

Puis exécuter :

```bash
python scripts/convert_media.py
```

**Option B — ffmpeg en ligne de commande**

```bash
# Convertir un fichier .ogg en .mp3
ffmpeg -y -i message.ogg -codec:a libmp3lame -b:a 128k message.mp3

# Convertir un fichier .aac en .mp3
ffmpeg -y -i message.aac -codec:a libmp3lame -b:a 128k message.mp3
```

Les fichiers `.mp4` (vidéo) et `.jpeg` (image) n'ont pas besoin de conversion.

### Étape 3 — Ajouter une musique de fond

1. Aller sur [Pixabay Music](https://pixabay.com/music/) (gratuit, sans compte, sans attribution)
2. Chercher "lounge jazz", "soft jazz" ou "chill background"
3. Télécharger un morceau
4. Le convertir en 96kbps pour le web :

```bash
ffmpeg -y -i musique-telechargee.mp3 -codec:a libmp3lame -b:a 96k assets/background-jazz.mp3
```

### Étape 4 — Personnaliser la page

Ouvrir `index.html` et modifier la section `GIFTS` dans le JavaScript :

```javascript
const GIFTS = [
    { id: 1,  name: "Prénom",           type: "audio", file: "assets/prenom.mp3",  image: "assets/prenom.jpeg" },
    { id: 2,  name: "Prénom",           type: "audio", file: "assets/prenom.mp3",  image: null },
    { id: 3,  name: "Prénom et Prénom", type: "video", file: "assets/prenom.mp4",  image: null },
    // Ajouter autant de cadeaux que nécessaire
];
```

Pour chaque cadeau :
- `name` : le prénom ou la description qui apparaîtra après ouverture
- `type` : `"audio"` ou `"video"`
- `file` : chemin vers le fichier dans `assets/`
- `image` : chemin vers une photo (ou `null` si pas de photo)

**Autres personnalisations :**

| Élément | Où le modifier |
|---------|---------------|
| Titre page d'accueil | Balise `<h1>` dans la section `#welcome` |
| Sous-titre | Balise `<p class="subtitle">` |
| Message final | Section `#finale` (balises `<h2>` et `<p>`) |
| Souhaits en cascade | Tableau `WISHES` dans le JavaScript |
| Couleurs | Variables CSS dans `:root` (début du `<style>`) |
| Volume musique | Variable `BG_VOLUME` dans le JavaScript (0.15 = 15%) |

### Étape 5 — Tester localement

Ouvrir `index.html` dans un navigateur. Tout fonctionne en local (pas besoin de serveur).

Vérifier :
- [ ] Tous les audios se lisent
- [ ] Les vidéos se lisent
- [ ] Les confettis apparaissent
- [ ] La musique de fond démarre au clic "Découvrir"
- [ ] La musique se met en pause (fondu) quand on ouvre un cadeau
- [ ] La finale se déclenche quand tous les cadeaux sont ouverts
- [ ] Le rendu est correct sur mobile (réduire la fenêtre du navigateur)

### Étape 6 — Déployer sur GitHub Pages (gratuit)

```bash
# 1. Se connecter à GitHub
gh auth login

# 2. Créer le repo (choisir un nom neutre pour ne pas gâcher la surprise)
gh repo create votre-nom/nom-neutre --public --description "Page interactive"

# 3. Initialiser git et pousser
cd chemin/vers/le/projet
git init
git remote add origin https://github.com/votre-nom/nom-neutre.git
git branch -M main
git add index.html assets/
git commit -m "feat: page interactive"
git push -u origin main

# 4. Activer GitHub Pages
gh api repos/votre-nom/nom-neutre/pages --method POST \
  --input - <<< '{"build_type":"legacy","source":{"branch":"main","path":"/"}}'
```

Le site sera accessible en 1-2 minutes à :
**https://votre-nom.github.io/nom-neutre/**

### Étape 7 — Partager

Envoyer le lien par WhatsApp, SMS ou email. C'est tout.

---

## Structure du projet

```
├── index.html              # La page complète (HTML + CSS + JS, tout-en-un)
├── assets/
│   ├── prenom.mp3          # Messages audio convertis
│   ├── prenom.mp4          # Messages vidéo
│   ├── prenom.jpeg         # Photos (optionnel)
│   └── background-jazz.mp3 # Musique de fond
├── scripts/
│   └── convert_media.py    # Script de conversion audio
└── README.md               # Ce fichier
```

---

## Adapter pour un autre événement

Cette page peut être réutilisée pour tout événement collectif :
- Anniversaire, mariage, départ à la retraite, naissance
- Remplacer les textes, les couleurs, les souhaits
- Ajouter ou retirer des cadeaux dans le tableau `GIFTS`

**Couleurs** : modifier les variables CSS dans `:root` pour changer toute la palette en un seul endroit.

---

## Contraintes techniques

| Contrainte | Solution |
|------------|----------|
| iOS Safari ne lit pas .ogg | Convertir en .mp3 avant déploiement |
| Navigateurs bloquent l'autoplay audio | La musique démarre après le premier clic (bouton "Découvrir") |
| Fichiers lourds (vidéos) | GitHub Pages supporte jusqu'à 100 Mo par fichier, 1 Go par repo |
| Pas de backend | Tout est statique, pas besoin de serveur |

---

## Licence

Page créée pour un usage personnel/familial. Musique de fond sous licence Pixabay (libre de droits).
