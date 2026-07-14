# ♻️ EcoSort-Search

Application web containerisée d'aide au tri sélectif : l'utilisateur saisit un nom de produit,
l'application le recherche sur Jumia, puis un modèle de Deep Learning identifie la matière du produit
sélectionné pour indiquer la bonne poubelle de tri.

Projet de fin de module — Machine Learning 2.

## Équipe

| Membre | Rôle principal | Branche |
|---|---|---|
| _À compléter_ | ML (entraînement du modèle) | `feature/ml-training` |
| _À compléter_ | Scraping (Jumia) | `feature/scraping` |
| _À compléter_ | Application & Docker | `feature/webapp-docker` |

## Structure du dépôt

```
ecosort-search/
├── ml/                  # Jalon 1 : entraînement du modèle
│   ├── models/          # Modèle sauvegardé + class_indices.json (voir note ci-dessous)
│   └── ...
├── scraping/            # Module de scraping Jumia
├── app/                 # Application Streamlit + pipeline d'inférence
├── docs/                # Rapport, documentation
├── requirements.txt
├── Dockerfile           # Ajouté au Jalon 2
├── docker-compose.yml   # Ajouté au Jalon 2
└── .gitignore
```

## Workflow Git de l'équipe

Ce dépôt suit des règles strictes de collaboration, imposées par l'énoncé du projet :

1. **La branche `main` est protégée.** Aucun push direct n'y est autorisé.
2. **Chaque membre travaille sur sa propre branche** (`feature/...`).
3. **Toute intégration vers `main` passe par une Pull Request**, relue et approuvée par au moins un autre membre de l'équipe avant fusion.
4. **Commits fréquents et explicites**, pas de gros commit unique en fin de semaine — voir [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) pour la convention de nommage.

## Lancer le projet (une fois le Jalon 2 terminé)

```bash
docker build -t ecosort .
docker run -p 8501:8501 ecosort
```

ou

```bash
docker-compose up -d --build
```

## Note sur le modèle entraîné

Le fichier du modèle (`.h5` / `.keras`) n'est pas versionné directement dans Git (voir `.gitignore`)
car il dépasse une taille raisonnable pour un dépôt classique. Une fois le Jalon 1 terminé, ajoutez ici
soit un lien de téléchargement (Google Drive, Kaggle Dataset, etc.), soit basculez sur Git LFS si l'équipe
préfère le versionner directement.

**Lien de téléchargement du modèle :** [modele_eco_sort.h5 — Google Drive](https://drive.google.com/file/d/1BNt_8IBORnOEIKzQY44jr9ZsJF5fFdXh/view?usp=drive_link)