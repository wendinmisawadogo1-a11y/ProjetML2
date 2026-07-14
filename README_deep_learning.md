# EcoSort - Module Deep Learning (Jalon 1)
**Branche :** `Deep_learning_Bintou`  
**Responsable :** Bintou

---

## Ce que ce module fait

Ce module contient deux choses :
1. **Un modèle CNN** (`modele_eco_sort.h5`) capable de reconnaître la matière d'un objet à partir de sa photo (plastique, verre, métal, papier, carton, déchets)
2. **Un détecteur D3E** (`d3e_detection.py`) qui détecte les produits électroniques par mots-clés, AVANT d'appeler le CNN

---

## Les 5 catégories de tri final

| Résultat du modèle | Catégorie de tri | Couleur UI |
|---|---|---|
| `plastic`, `metal`, `cardboard` | Poubelle JAUNE | 🟡 |
| `glass` | Poubelle VERTE | 🟢 |
| `paper` | Poubelle BLEUE | 🔵 |
| `trash` | Poubelle MARRON/NOIRE | ⚫ |
| D3E détecté par mots-clés | Bac Électronique | 🎛️ Gris |

---

## Comment utiliser le modèle (pour la personne qui fait l'interface)

```python
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from d3e_detection import est_electronique

# Charger le modèle une seule fois au démarrage de l'appli
model = tf.keras.models.load_model("modele_eco_sort.h5")

# Noms des classes (dans l'ordre alphabétique, comme Keras les a indexées)
noms_classes = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

# Correspondance classe -> catégorie de tri finale
correspondance_tri = {
    'cardboard' : 'JAUNE',
    'glass'     : 'VERTE',
    'metal'     : 'JAUNE',
    'paper'     : 'BLEUE',
    'plastic'   : 'JAUNE',
    'trash'     : 'MARRON',
}

def classifier_produit(nom_produit, chemin_image):
    """
    Classifie un produit dans l'une des 5 catégories de tri.
    
    Args:
        nom_produit (str): nom du produit scrapé sur Jumia
        chemin_image (str): chemin vers l'image du produit (téléchargée depuis Jumia)
    
    Returns:
        dict: {"categorie": "JAUNE", "classe_cnn": "plastic", "confiance": 91.2}
    """
    # Étape 1 : vérifier si c'est de l'électronique (D3E) par mots-clés
    if est_electronique(nom_produit):
        return {
            "categorie" : "D3E",
            "classe_cnn": None,
            "confiance" : 100.0
        }
    
    # Étape 2 : si pas D3E, analyser l'image avec le CNN
    img = image.load_img(chemin_image, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    
    predictions = model.predict(img_array, verbose=0)
    classe_predite = noms_classes[np.argmax(predictions)]
    confiance = float(np.max(predictions) * 100)
    
    return {
        "categorie" : correspondance_tri[classe_predite],
        "classe_cnn": classe_predite,
        "confiance" : round(confiance, 1)
    }
```

---

## Comment utiliser le détecteur D3E (pour la personne qui fait le scraping)

```python
from d3e_detection import est_electronique

# Exemple : après avoir scrapé un produit sur Jumia
nom_produit = "Chargeur rapide USB-C 20W"

if est_electronique(nom_produit):
    print("Ce produit est électronique → Bac D3E")
else:
    print("Ce produit n'est pas électronique → passer l'image au CNN")
```

---

## Performances du modèle

| Classe | F1-score |
|---|---|
| cardboard | 0.94 |
| glass | 0.90 |
| metal | 0.91 |
| paper | 0.92 |
| plastic | 0.82 |
| trash | 0.71 |
| **Global** | **89%** |

> **Limite connue :** la classe `trash` est moins bien reconnue (recall 62%), 
> car elle est sous-représentée dans le dataset (137 images vs 400-600 pour les autres).
> Le rééquilibrage des classes (`class_weight`) a été appliqué pour atténuer ce problème.

---

## Fichiers importants
| Fichier | Description |
|---|---|
| `modele_eco_sort.h5` | Modèle CNN entraîné — [Télécharger depuis Google Drive](https://drive.google.com/file/d/1BNt_8IBORnOEIKzQY44jr9ZsJF5fFdXh/view?usp=drive_link) |
| `d3e_detection.py` | Fonction de détection D3E par mots-clés |
| `deep_learning.py` | Script d'entraînement complet et reproductible |