"""
mapping.py — Définitions officielles des catégories de tri EcoSort-Search.

Ce module est la source de vérité unique pour la correspondance entre :
  - les classes matière prédites par le modèle (Jalon 1)
  - les 5 poubelles officielles du cahier des charges
  - les couleurs et pictogrammes affichés dans l'interface

Il est volontairement sans aucune dépendance (pas de Streamlit, pas de TF)
pour pouvoir être importé aussi bien par l'app que par les scripts ML.
"""

# ---------------------------------------------------------------------------
# Les 5 poubelles officielles (cf. tableau du cahier des charges)
# ---------------------------------------------------------------------------
POUBELLES = {
    "JAUNE": {
        "nom": "Poubelle JAUNE",
        "emoji": "🟡",
        "couleur": "#F5C518",          # fond principal de l'écran de résultat
        "couleur_texte": "#3D3000",    # texte lisible sur ce fond
        "description": "Emballages ménagers légers : bouteilles plastique, "
                       "canettes, conserves, briques, cartons.",
    },
    "VERTE": {
        "nom": "Poubelle VERTE",
        "emoji": "🟢",
        "couleur": "#2E8B57",
        "couleur_texte": "#FFFFFF",
        "description": "Verre d'emballage uniquement : bouteilles, bocaux, "
                       "pots. Vaisselle cassée interdite.",
    },
    "BLEUE": {
        "nom": "Poubelle BLEUE",
        "emoji": "🔵",
        "couleur": "#1E6FD9",
        "couleur_texte": "#FFFFFF",
        "description": "Papiers graphiques propres : journaux, magazines, "
                       "cahiers, livres, enveloppes.",
    },
    "D3E": {
        "nom": "Bac Électronique (D3E)",
        "emoji": "🎛️",
        "couleur": "#6E7B8B",
        "couleur_texte": "#FFFFFF",
        "description": "Tout produit à pile, batterie ou prise : smartphones, "
                       "écouteurs, chargeurs, petits appareils.",
    },
    "MARRON": {
        "nom": "Poubelle MARRON / NOIRE",
        "emoji": "⚫",
        "couleur": "#5C4033",
        "couleur_texte": "#FFFFFF",
        "description": "Déchets résiduels non recyclables : restes "
                       "alimentaires, films plastiques, hygiène.",
    },
}

# ---------------------------------------------------------------------------
# Correspondance classe matière (sortie du modèle) → poubelle officielle
# Les clés correspondent exactement aux classes du dataset Kaggle,
# plus la classe "electronic" (stratégie D3E, cf. rapport Jalon 1).
# ---------------------------------------------------------------------------
CLASSE_VERS_POUBELLE = {
    "plastic": "JAUNE",
    "metal": "JAUNE",
    "cardboard": "JAUNE",
    "glass": "VERTE",
    "paper": "BLEUE",
    "electronic": "D3E",
    "trash": "MARRON",
}

# Libellés français des matières, pour l'affichage utilisateur
CLASSE_LABELS_FR = {
    "plastic": "Plastique",
    "metal": "Métal",
    "cardboard": "Carton",
    "glass": "Verre",
    "paper": "Papier",
    "electronic": "Électronique",
    "trash": "Résiduel",
}

# ---------------------------------------------------------------------------
# Mots-clés du pré-filtre D3E (stratégie hybride décidée au Jalon 1) :
# si le NOM du produit contient l'un de ces mots, on route directement
# vers le bac électronique sans passer par le modèle image.
# ---------------------------------------------------------------------------
KEYWORDS_ELECTRONIQUE = [
    "smartphone", "téléphone", "telephone", "phone", "iphone", "samsung",
    "écouteur", "ecouteur", "earbud", "airpod", "casque bluetooth",
    "chargeur", "charger", "câble usb", "cable usb", "batterie", "battery",
    "power bank", "powerbank", "montre connectée", "smartwatch",
    "mixeur", "blender", "tablette", "tablet", "ordinateur", "laptop",
    "clavier", "souris sans fil", "enceinte", "speaker", "télécommande",
    "radio", "ventilateur électrique", "fer à repasser", "bouilloire",
]


def est_electronique(nom_produit: str) -> bool:
    """Pré-filtre D3E : True si le nom du produit évoque un appareil électronique."""
    nom = nom_produit.lower()
    return any(mot in nom for mot in KEYWORDS_ELECTRONIQUE)


def infos_poubelle(classe_matiere: str) -> dict:
    """
    Retourne le dictionnaire complet de la poubelle correspondant à une
    classe matière, enrichi du libellé français de la matière.

    Lève une KeyError explicite si la classe est inconnue — mieux vaut
    échouer clairement qu'afficher une mauvaise consigne de tri.
    """
    if classe_matiere not in CLASSE_VERS_POUBELLE:
        raise KeyError(
            f"Classe matière inconnue : '{classe_matiere}'. "
            f"Classes valides : {sorted(CLASSE_VERS_POUBELLE)}"
        )
    code = CLASSE_VERS_POUBELLE[classe_matiere]
    infos = dict(POUBELLES[code])  # copie pour ne pas muter la source
    infos["code"] = code
    infos["matiere"] = CLASSE_LABELS_FR.get(classe_matiere, classe_matiere)
    return infos
