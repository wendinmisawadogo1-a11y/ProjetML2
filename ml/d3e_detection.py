# -*- coding: utf-8 -*-
"""
Module de détection des produits électroniques (D3E)
------------------------------------------------------
Ce module permet de déterminer si un produit doit être classé
dans le Bac Électronique (D3E) en se basant sur son nom,
AVANT d'appeler le modèle de deep learning (CNN).

Le CNN n'a pas été entraîné pour reconnaître l'électronique
(absent du dataset source), donc cette détection se fait
par une simple recherche de mots-clés dans le nom du produit.
"""

MOTS_CLES_D3E = [
    "smartphone", "telephone", "iphone", "samsung", "tablette", "ordinateur",
    "laptop", "pc portable", "souris", "clavier", "ecouteur", "casque audio",
    "chargeur", "cable usb", "powerbank", "batterie externe",
    "mixeur", "blender", "grille-pain", "bouilloire electrique", "fer a repasser",
    "aspirateur", "ventilateur", "climatiseur", "refrigerateur", "micro-onde",
    "rasoir electrique", "seche-cheveux",
    "montre connectee", "smartwatch", "television", "tv led", "enceinte bluetooth",
    "camera", "appareil photo", "console de jeux", "manette", "drone",
    "lampe led", "ampoule connectee", "radio",
]


def est_electronique(nom_produit):
    """
    Vérifie si un nom de produit correspond à un article électronique (D3E).
    """
    nom_produit_minuscule = nom_produit.lower()
    for mot_cle in MOTS_CLES_D3E:
        if mot_cle in nom_produit_minuscule:
            return True
    return False


if __name__ == "__main__":
    exemples = [
        "Chargeur rapide USB-C 20W",
        "Bouteille d'eau Cristaline 1.5L",
        "Ecouteurs Bluetooth sans fil JBL",
        "Cahier de brouillon 100 pages",
    ]
    for exemple in exemples:
        resultat = "D3E (electronique)" if est_electronique(exemple) else "A analyser par le CNN"
        print(f"{exemple} -> {resultat}")