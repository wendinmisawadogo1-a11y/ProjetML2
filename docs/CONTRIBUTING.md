# Guide de contribution — EcoSort-Search

Ce document fixe les règles de travail en équipe sur ce dépôt. Elles ne sont pas optionnelles :
elles répondent directement aux consignes de l'énoncé du projet, qui évalue explicitement
la qualité de l'historique Git et le respect du processus de revue.

## 1. Branches

Chaque membre travaille exclusivement sur sa branche dédiée, jamais directement sur `main` :

| Branche | Responsable | Contenu |
|---|---|---|
| `feature/ml-training` | Personne A | Dataset, script d'entraînement, modèle, évaluation |
| `feature/scraping` | Personne B | Module de scraping Jumia |
| `feature/webapp-docker` | Personne C | Interface, pipeline d'inférence, Dockerfile |

Créer sa branche localement puis la pousser :

```bash
git checkout -b feature/ml-training
git push -u origin feature/ml-training
```

Si votre travail dépend d'une avancée sur une autre branche, mettez à jour la vôtre régulièrement :

```bash
git checkout feature/webapp-docker
git fetch origin
git merge origin/main
```

## 2. Commits

- Un commit = un changement logique cohérent, pas un mélange de plusieurs sujets.
- Message au format : `type(scope): description courte`

```
feat(ml): ajoute la phase de fine-tuning MobileNetV2
fix(scraping): corrige le sélecteur CSS après changement de structure Jumia
docs(readme): ajoute les instructions de build Docker
chore(git): initialise le .gitignore du projet
```

Types courants : `feat` (nouvelle fonctionnalité), `fix` (correction de bug), `docs` (documentation),
`chore` (maintenance/config), `refactor` (réorganisation sans changement de comportement),
`test` (ajout/modification de tests).

- Committez régulièrement (à chaque étape franchie), pas uniquement en fin de semaine.
  L'historique de commits est un critère d'évaluation individuelle explicite de l'énoncé.

## 3. Pull Requests — processus obligatoire

1. Une fois une sous-tâche terminée sur votre branche, ouvrez une PR vers `main`.
2. Titre clair, description qui répond à : *quoi* (ce qui a été fait), *pourquoi*, *comment tester*.
3. Un autre membre de l'équipe relit le code, laisse au moins un commentaire ou approuve directement.
4. **La fusion n'est possible qu'après approbation** (la protection de branche l'impose techniquement).
5. Résolvez les commentaires avant de fusionner ; en cas de désaccord, en discuter en équipe plutôt
   que de forcer la fusion.

### Checklist avant d'ouvrir une PR

- [ ] Le code s'exécute sans erreur en local
- [ ] Aucun fichier volumineux (dataset, `.venv`) n'a été ajouté par erreur (vérifiez `git status`)
- [ ] Les noms de variables/fonctions sont clairs
- [ ] La description de la PR permet à un coéquipier de comprendre le changement sans lire tout le diff

## 4. Ce qu'il ne faut jamais pousser

Couvert par `.gitignore`, mais à vérifier manuellement en cas de doute (`git status` avant `git add`) :
dataset Kaggle (`data/`, `dataset/`), environnements virtuels (`.venv/`), fichiers de modèle lourds
(`*.h5`, `*.keras`) sauf décision explicite de l'équipe de les versionner (voir README).
