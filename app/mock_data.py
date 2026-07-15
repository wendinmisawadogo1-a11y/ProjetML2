"""
mock_data.py — Données factices pour développer l'interface sans dépendre
des branches feature/scraping et feature/ml-training.

CONTRAT D'INTERFACE (à respecter par les vraies implémentations) :

  search_jumia(keyword: str, max_results: int = 5) -> list[dict]
      Chaque dict contient : {"nom": str, "prix": str, "image_url": str, "lien": str}

  predict_bin(image_url: str, nom_produit: str = "") -> dict
      Retourne : {"classe_matiere": str, "confiance": float}
      (le mapping vers la poubelle/couleur est fait par mapping.py, pas ici)

Quand les vraies fonctions seront livrées, il suffira de remplacer dans
main.py la ligne  `from mock_data import ...`  par les vrais imports.

Le catalogue ci-dessous est volontairement large (~45 produits) et couvre
les 5 poubelles, pour permettre de repérer les incohérences de l'interface.
"""

import random
import time

from mapping import est_electronique


def _img(bg: str, fg: str, texte: str) -> str:
    """Construit une URL d'image placeholder lisible (placehold.co)."""
    t = texte.replace(" ", "+").replace("\n", "%0A")
    return f"https://placehold.co/400x400/{bg}/{fg}?text={t}"


# ---------------------------------------------------------------------------
# Catalogue factice — chaque entrée : nom, prix (FCFA), remise (%), image,
# classe matière réelle (pour que le mock 'prédise' juste).
# ---------------------------------------------------------------------------
_CATALOGUE = [
    # ---------- JAUNE : plastic / metal / cardboard ----------
    {"nom": "Bouteille d'eau minérale Awa 1.5L (pack de 6)", "prix": "2 500 FCFA", "remise": 15,
     "image_url": _img("EAF4FF", "1E6FD9", "Bouteille\nplastique"), "classe_reelle": "plastic"},
    {"nom": "Pack de 12 bouteilles de soda Planet 33cl", "prix": "3 600 FCFA", "remise": 20,
     "image_url": _img("EAF4FF", "1E6FD9", "Soda\nplastique"), "classe_reelle": "plastic"},
    {"nom": "Flacon de shampoing antipelliculaire 400ml", "prix": "2 100 FCFA", "remise": 0,
     "image_url": _img("EAF4FF", "1E6FD9", "Flacon\nshampoing"), "classe_reelle": "plastic"},
    {"nom": "Bidon d'huile de tournesol Dinor 5L", "prix": "6 900 FCFA", "remise": 10,
     "image_url": _img("EAF4FF", "1E6FD9", "Bidon\nhuile"), "classe_reelle": "plastic"},
    {"nom": "Seau plastique alimentaire 10L avec couvercle", "prix": "1 800 FCFA", "remise": 25,
     "image_url": _img("EAF4FF", "1E6FD9", "Seau\nplastique"), "classe_reelle": "plastic"},
    {"nom": "Gourde reutilisable en plastique 750ml", "prix": "1 500 FCFA", "remise": 0,
     "image_url": _img("EAF4FF", "1E6FD9", "Gourde"), "classe_reelle": "plastic"},
    {"nom": "Canette de boisson gazeuse 33cl", "prix": "600 FCFA", "remise": 0,
     "image_url": _img("F2F2F2", "888888", "Canette\naluminium"), "classe_reelle": "metal"},
    {"nom": "Boite de conserve tomate pelee 400g", "prix": "750 FCFA", "remise": 5,
     "image_url": _img("F2F2F2", "888888", "Conserve\nmetal"), "classe_reelle": "metal"},
    {"nom": "Boite de thon a l'huile 140g (lot de 3)", "prix": "2 250 FCFA", "remise": 12,
     "image_url": _img("F2F2F2", "888888", "Thon\nboite"), "classe_reelle": "metal"},
    {"nom": "Canette de lait concentre sucre 170g", "prix": "900 FCFA", "remise": 0,
     "image_url": _img("F2F2F2", "888888", "Lait\nconcentre"), "classe_reelle": "metal"},
    {"nom": "Bombe aerosol desodorisant 300ml", "prix": "1 950 FCFA", "remise": 18,
     "image_url": _img("F2F2F2", "888888", "Aerosol\nmetal"), "classe_reelle": "metal"},
    {"nom": "Carton de demenagement double cannelure 55x35cm", "prix": "1 200 FCFA", "remise": 0,
     "image_url": _img("F7EBD8", "9C6B2F", "Carton\ndemenagement"), "classe_reelle": "cardboard"},
    {"nom": "Boite a pizza kraft 33cm (lot de 10)", "prix": "2 800 FCFA", "remise": 30,
     "image_url": _img("F7EBD8", "9C6B2F", "Boite\npizza"), "classe_reelle": "cardboard"},
    {"nom": "Brique de lait UHT demi-ecreme 1L", "prix": "800 FCFA", "remise": 0,
     "image_url": _img("F7EBD8", "9C6B2F", "Brique\nlait"), "classe_reelle": "cardboard"},
    {"nom": "Boite de cereales petit-dejeuner 500g", "prix": "3 100 FCFA", "remise": 8,
     "image_url": _img("F7EBD8", "9C6B2F", "Boite\ncereales"), "classe_reelle": "cardboard"},
    {"nom": "Rouleau d'essuie-tout 2 plis (lot de 6)", "prix": "2 400 FCFA", "remise": 15,
     "image_url": _img("F7EBD8", "9C6B2F", "Essuie-tout\ncarton"), "classe_reelle": "cardboard"},

    # ---------- VERTE : glass ----------
    {"nom": "Bocal de confiture de mangue 370g", "prix": "1 800 FCFA", "remise": 0,
     "image_url": _img("EAF7EF", "2E8B57", "Bocal\nverre"), "classe_reelle": "glass"},
    {"nom": "Bouteille de jus d'ananas en verre 25cl", "prix": "1 000 FCFA", "remise": 10,
     "image_url": _img("EAF7EF", "2E8B57", "Jus\nverre"), "classe_reelle": "glass"},
    {"nom": "Bouteille de vin rouge Bordeaux 75cl", "prix": "5 500 FCFA", "remise": 5,
     "image_url": _img("EAF7EF", "2E8B57", "Vin\nverre"), "classe_reelle": "glass"},
    {"nom": "Pot de miel pur en verre 500g", "prix": "3 200 FCFA", "remise": 0,
     "image_url": _img("EAF7EF", "2E8B57", "Miel\nverre"), "classe_reelle": "glass"},
    {"nom": "Bocal de cornichons au vinaigre 340g", "prix": "1 650 FCFA", "remise": 12,
     "image_url": _img("EAF7EF", "2E8B57", "Cornichons\nbocal"), "classe_reelle": "glass"},
    {"nom": "Bouteille d'huile d'olive extra vierge 50cl", "prix": "4 800 FCFA", "remise": 20,
     "image_url": _img("EAF7EF", "2E8B57", "Huile\nolive+verre"), "classe_reelle": "glass"},
    {"nom": "Flacon de parfum en verre vide 100ml", "prix": "2 000 FCFA", "remise": 0,
     "image_url": _img("EAF7EF", "2E8B57", "Flacon\nverre"), "classe_reelle": "glass"},

    # ---------- BLEUE : paper ----------
    {"nom": "Cahier 200 pages grands carreaux", "prix": "900 FCFA", "remise": 0,
     "image_url": _img("EEF3FB", "1E6FD9", "Cahier\npapier"), "classe_reelle": "paper"},
    {"nom": "Ramette de papier A4 blanc 500 feuilles", "prix": "3 500 FCFA", "remise": 10,
     "image_url": _img("EEF3FB", "1E6FD9", "Ramette\nA4"), "classe_reelle": "paper"},
    {"nom": "Magazine mensuel d'actualite (n142)", "prix": "1 500 FCFA", "remise": 0,
     "image_url": _img("EEF3FB", "1E6FD9", "Magazine"), "classe_reelle": "paper"},
    {"nom": "Bloc-notes spirale 100 feuilles A5", "prix": "1 100 FCFA", "remise": 15,
     "image_url": _img("EEF3FB", "1E6FD9", "Bloc-notes"), "classe_reelle": "paper"},
    {"nom": "Lot de 50 enveloppes blanches format DL", "prix": "1 350 FCFA", "remise": 0,
     "image_url": _img("EEF3FB", "1E6FD9", "Enveloppes"), "classe_reelle": "paper"},
    {"nom": "Roman broche 320 pages", "prix": "4 200 FCFA", "remise": 5,
     "image_url": _img("EEF3FB", "1E6FD9", "Livre\nbroche"), "classe_reelle": "paper"},
    {"nom": "Journal quotidien (edition du jour)", "prix": "300 FCFA", "remise": 0,
     "image_url": _img("EEF3FB", "1E6FD9", "Journal"), "classe_reelle": "paper"},

    # ---------- D3E : electronic ----------
    {"nom": "Ecouteurs Bluetooth sans fil TWS", "prix": "7 500 FCFA", "remise": 40,
     "image_url": _img("ECEFF3", "6E7B8B", "Ecouteurs\nBluetooth"), "classe_reelle": "electronic"},
    {"nom": "Chargeur rapide USB-C 25W", "prix": "4 000 FCFA", "remise": 30,
     "image_url": _img("ECEFF3", "6E7B8B", "Chargeur\nUSB-C"), "classe_reelle": "electronic"},
    {"nom": "Smartphone Tecno Spark 10 128Go", "prix": "89 900 FCFA", "remise": 22,
     "image_url": _img("ECEFF3", "6E7B8B", "Smartphone\nTecno"), "classe_reelle": "electronic"},
    {"nom": "Montre connectee sport etanche", "prix": "12 500 FCFA", "remise": 55,
     "image_url": _img("ECEFF3", "6E7B8B", "Montre\nconnectee"), "classe_reelle": "electronic"},
    {"nom": "Mixeur electrique 500W bol 1.5L", "prix": "15 900 FCFA", "remise": 18,
     "image_url": _img("ECEFF3", "6E7B8B", "Mixeur\nelectrique"), "classe_reelle": "electronic"},
    {"nom": "Power bank 20000mAh charge rapide", "prix": "9 800 FCFA", "remise": 35,
     "image_url": _img("ECEFF3", "6E7B8B", "Power+bank"), "classe_reelle": "electronic"},
    {"nom": "Cable USB-C vers Lightning 1m", "prix": "2 500 FCFA", "remise": 0,
     "image_url": _img("ECEFF3", "6E7B8B", "Cable\nUSB"), "classe_reelle": "electronic"},
    {"nom": "Enceinte Bluetooth portable etanche", "prix": "11 000 FCFA", "remise": 28,
     "image_url": _img("ECEFF3", "6E7B8B", "Enceinte\nBluetooth"), "classe_reelle": "electronic"},

    # ---------- MARRON : trash (residuel, souple, multicouche) ----------
    {"nom": "Sachet de lingettes nettoyantes x72", "prix": "1 500 FCFA", "remise": 0,
     "image_url": _img("F4EFEB", "5C4033", "Lingettes"), "classe_reelle": "trash"},
    {"nom": "Film alimentaire etirable 30m", "prix": "1 100 FCFA", "remise": 12,
     "image_url": _img("F4EFEB", "5C4033", "Film\nalimentaire"), "classe_reelle": "trash"},
    {"nom": "Rouleau de sacs poubelle 30L (x30)", "prix": "1 300 FCFA", "remise": 0,
     "image_url": _img("F4EFEB", "5C4033", "Sacs\npoubelle"), "classe_reelle": "trash"},
    {"nom": "Paquet de couches bebe taille 4 (x40)", "prix": "6 500 FCFA", "remise": 20,
     "image_url": _img("F4EFEB", "5C4033", "Couches\nbebe"), "classe_reelle": "trash"},
    {"nom": "Brosse a dents manuelle souple (lot de 4)", "prix": "1 800 FCFA", "remise": 0,
     "image_url": _img("F4EFEB", "5C4033", "Brosses\na+dents"), "classe_reelle": "trash"},
    {"nom": "Eponge de vaisselle double face (x6)", "prix": "1 200 FCFA", "remise": 15,
     "image_url": _img("F4EFEB", "5C4033", "Eponges"), "classe_reelle": "trash"},
    {"nom": "Rasoir jetable 3 lames (lot de 10)", "prix": "2 100 FCFA", "remise": 0,
     "image_url": _img("F4EFEB", "5C4033", "Rasoirs\njetables"), "classe_reelle": "trash"},
    {"nom": "Sachet de chips saveur barbecue 150g", "prix": "1 400 FCFA", "remise": 0,
     "image_url": _img("F4EFEB", "5C4033", "Chips\nsachet"), "classe_reelle": "trash"},
]


def search_jumia(keyword: str, max_results: int = 5) -> list[dict]:
    """Version factice du scraper Jumia."""
    time.sleep(0.7)  # latence simulee

    if keyword.strip().lower() == "rien":
        return []

    kw = keyword.strip().lower()
    pertinents = [p for p in _CATALOGUE if kw and kw in p["nom"].lower()]
    autres = [p for p in _CATALOGUE if p not in pertinents]
    random.shuffle(autres)

    n = max(3, min(max_results, 5))
    selection = (pertinents + autres)[:n]

    return [
        {
            "nom": p["nom"],
            "prix": p["prix"],
            "remise": p["remise"],
            "image_url": p["image_url"],
            "lien": "https://www.jumia.ci/produit-factice",
            "_classe_reelle": p["classe_reelle"],
        }
        for p in selection
    ]


def predict_bin(image_url: str, nom_produit: str = "") -> dict:
    """Version factice du pipeline d'inference (strategie hybride Jalon 1)."""
    time.sleep(1.0)  # latence simulee

    if nom_produit and est_electronique(nom_produit):
        return {"classe_matiere": "electronic", "confiance": 0.99}

    for p in _CATALOGUE:
        if p["image_url"] == image_url:
            return {
                "classe_matiere": p["classe_reelle"],
                "confiance": round(random.uniform(0.72, 0.97), 2),
            }

    classe = random.choice(["plastic", "metal", "glass", "paper", "trash"])
    return {"classe_matiere": classe, "confiance": round(random.uniform(0.30, 0.54), 2)}


TOUS_LES_NOMS = [p["nom"] for p in _CATALOGUE]
