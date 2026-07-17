"""
inference.py — Pipeline d'inference reel pour EcoSort-Search.

Remplace le predict_bin() factice de mock_data. Charge le modele CNN
entraine au Jalon 1 (modele_eco_sort.h5) et applique la strategie hybride :

    1. Pre-filtre D3E par mots-cles sur le NOM du produit (fonction
       est_electronique de ta coequipiere) -> si electronique, on retourne
       le bac D3E sans meme appeler le CNN.
    2. Sinon : telechargement de l'image depuis son URL Jumia, preprocessing
       IDENTIQUE a l'entrainement (resize 224x224, PAS de division par 255,
       conformement au deep_learning.py de l'equipe), puis prediction CNN.

CONTRAT D'INTERFACE (identique au mock, remplacement transparent) :

    predict_bin(image_url: str, nom_produit: str = "") -> dict
        Retourne {"classe_matiere": str, "confiance": float}
        - classe_matiere parmi : cardboard, glass, metal, paper, plastic,
          trash, electronic
        - confiance : float entre 0 et 1
"""

import io
import os
import sys

import numpy as np
import requests

# --- Rendre les modules du projet importables (ml/, app/) quel que soit
#     le dossier de lancement de Streamlit ---
_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

# Fonction de detection D3E ecrite par la coequipiere ML (dossier ml/).
# On reutilise SA fonction pour rester coherent avec son travail.
try:
    from ml.d3e_detection import est_electronique
except Exception:  # secours : si l'import echoue, on desactive le pre-filtre
    def est_electronique(nom_produit: str) -> bool:
        return False


# ---------------------------------------------------------------------------
# Configuration (alignee sur deep_learning.py de l'equipe)
# ---------------------------------------------------------------------------
CHEMIN_MODELE = os.path.join(_RACINE, "ml", "models", "modele_eco_sort.h5")
TAILLE_IMAGE = (224, 224)

# Ordre EXACT des classes tel qu'indexe par Keras a l'entrainement
# (ordre alphabetique des dossiers du dataset). NE PAS modifier cet ordre :
# il doit correspondre trait pour trait a celui du modele entraine.
NOMS_CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]

TIMEOUT_IMAGE = 10  # secondes pour telecharger une image


# ---------------------------------------------------------------------------
# Chargement paresseux du modele (une seule fois, au premier appel)
# ---------------------------------------------------------------------------
_modele = None
_erreur_chargement = None


def _charger_modele():
    """
    Charge le modele Keras une seule fois et le met en cache.
    Retourne le modele, ou None si le chargement echoue (fichier absent, etc.).
    """
    global _modele, _erreur_chargement
    if _modele is not None or _erreur_chargement is not None:
        return _modele

    if not os.path.exists(CHEMIN_MODELE):
        _erreur_chargement = (
            f"Modele introuvable : {CHEMIN_MODELE}. Telechargez "
            "modele_eco_sort.h5 (lien dans le README) et placez-le dans ml/models/."
        )
        return None

    try:
        # Import tardif de TensorFlow : evite de le charger si le module est
        # importe sans jamais faire de prediction (ex: tests unitaires).
        import tensorflow as tf
        _modele = tf.keras.models.load_model(CHEMIN_MODELE)
    except Exception as exc:
        _erreur_chargement = f"Echec du chargement du modele : {exc}"
        _modele = None
    return _modele


# ---------------------------------------------------------------------------
# Telechargement + preprocessing de l'image
# ---------------------------------------------------------------------------
def _preparer_image(image_url: str):
    """
    Telecharge l'image depuis son URL et la prepare pour le modele.

    Preprocessing IDENTIQUE a l'entrainement (deep_learning.py) :
      - resize a 224x224
      - conversion en tableau float, SANS division par 255
      - ajout de la dimension batch -> forme (1, 224, 224, 3)

    Retourne le tableau numpy prpt pour predict(), ou None si echec.
    """
    try:
        reponse = requests.get(image_url, timeout=TIMEOUT_IMAGE)
        reponse.raise_for_status()
    except requests.RequestException:
        return None

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(reponse.content)).convert("RGB")
        img = img.resize(TAILLE_IMAGE)
        arr = np.array(img, dtype=np.float32)      # PAS de /255 (cf. entrainement)
        arr = np.expand_dims(arr, axis=0)          # (1, 224, 224, 3)
        return arr
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Fonction principale : predict_bin (meme signature que le mock)
# ---------------------------------------------------------------------------
def predict_bin(image_url: str, nom_produit: str = "") -> dict:
    """
    Predit la classe matiere d'un produit.

    Strategie hybride :
      1. Pre-filtre D3E sur le nom -> electronic (confiance 1.0) sans CNN.
      2. Sinon CNN sur l'image.

    Retourne toujours un dict {"classe_matiere": str, "confiance": float}.
    En cas d'erreur (modele absent, image non telechargeable), retourne une
    confiance de 0.0 -> l'interface affichera l'ecran "resultat incertain".
    """
    # 1) Pre-filtre D3E (mots-cles sur le nom) — identique au vrai pipeline.
    if nom_produit and est_electronique(nom_produit):
        return {"classe_matiere": "electronic", "confiance": 1.0}

    # 2) CNN sur l'image.
    modele = _charger_modele()
    if modele is None:
        # Modele indisponible : echec propre, confiance nulle.
        return {"classe_matiere": "trash", "confiance": 0.0}

    arr = _preparer_image(image_url)
    if arr is None:
        # Image non telechargeable/illisible : echec propre.
        return {"classe_matiere": "trash", "confiance": 0.0}

    try:
        predictions = modele.predict(arr, verbose=0)[0]
        idx = int(np.argmax(predictions))
        classe = NOMS_CLASSES[idx]
        confiance = float(np.max(predictions))
    except Exception:
        return {"classe_matiere": "trash", "confiance": 0.0}

    return {"classe_matiere": classe, "confiance": confiance}


def message_erreur_modele():
    """Expose l'eventuel message d'erreur de chargement, pour l'interface."""
    return _erreur_chargement


# ---------------------------------------------------------------------------
# Test manuel :  python app/inference.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test 1 : pre-filtre D3E (pas besoin du modele ni du reseau)
    r = predict_bin("", nom_produit="Chargeur rapide USB-C 20W")
    print("D3E par mots-cles :", r)
    assert r["classe_matiere"] == "electronic"

    # Test 2 : chargement du modele
    m = _charger_modele()
    if m is None:
        print("ATTENTION :", message_erreur_modele())
    else:
        print("Modele charge avec succes. Classes :", NOMS_CLASSES)
        print("Forme d'entree attendue :", m.input_shape)
