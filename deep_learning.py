# -*- coding: utf-8 -*-
"""
EcoSort - Script d'entraînement du modèle de classification des déchets
------------------------------------------------------------------------
Modèle : MobileNetV2 (Transfer Learning + Fine-tuning)
Dataset : Kaggle Garbage Classification (2527 images, 6 classes)
Résultats : val_accuracy ~88.9%, accuracy globale 89%
"""

# ==========================================
# ÉTAPE 1 : Configuration Kaggle et dataset
# ==========================================
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report

print("GPU disponible :", tf.config.list_physical_devices('GPU'))

# ==========================================
# ÉTAPE 2 : Chargement des données
# ==========================================
base_path = "dataset/garbage classification/Garbage classification"
taille_image = (224, 224)
taille_batch = 32

# Jeu d'entraînement (80% des images)
train_ds = tf.keras.utils.image_dataset_from_directory(
    base_path,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=taille_image,
    batch_size=taille_batch
)

# Jeu de validation (20% des images)
val_ds = tf.keras.utils.image_dataset_from_directory(
    base_path,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=taille_image,
    batch_size=taille_batch
)

noms_classes = train_ds.class_names
print("Classes détectées :", noms_classes)

# ==========================================
# ÉTAPE 3 : Rééquilibrage des classes
# ==========================================
# La classe "trash" est sous-représentée (137 images vs 400-600 pour les autres)
# On calcule des poids pour compenser ce déséquilibre
labels_entrainement = []
for images, labels in tf.keras.utils.image_dataset_from_directory(
    base_path, validation_split=0.2, subset="training",
    seed=123, image_size=taille_image, batch_size=taille_batch
):
    labels_entrainement.extend(labels.numpy())

poids_classes = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(labels_entrainement),
    y=labels_entrainement
)
poids_classes_dict = dict(enumerate(poids_classes))

for i, nom in enumerate(noms_classes):
    print(f"{nom} : poids = {poids_classes_dict[i]:.2f}")

# Optimisation du chargement des données
AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# ==========================================
# ÉTAPE 4 : Construction du modèle
# ==========================================
# On utilise MobileNetV2 pré-entraîné sur ImageNet (Transfer Learning)
# On gèle toutes ses couches dans un premier temps
base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)
base_model.trainable = False

model = models.Sequential([
    layers.Input(shape=(224, 224, 3)),
    layers.Rescaling(1./127.5, offset=-1),
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.2),
    layers.Dense(6, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# ==========================================
# ÉTAPE 5 : Entraînement initial (10 epochs)
# ==========================================
historique = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=10,
    class_weight=poids_classes_dict
)

# ==========================================
# ÉTAPE 6 : Fine-tuning avec Early Stopping
# ==========================================
# On dégèle les 54 dernières couches de MobileNetV2 pour affiner
base_model.trainable = True
couche_a_partir_de = 100
for couche in base_model.layers[:couche_a_partir_de]:
    couche.trainable = False

model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

early_stop = EarlyStopping(
    monitor="val_accuracy",
    patience=2,
    restore_best_weights=True
)

historique_finetuning = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=10,
    callbacks=[early_stop],
    class_weight=poids_classes_dict
)

# ==========================================
# ÉTAPE 7 : Sauvegarde du modèle
# ==========================================
model.save("modele_eco_sort.h5")
print("Modèle fine-tuné et rééquilibré sauvegardé !")

# ==========================================
# ÉTAPE 8 : Rapport détaillé par classe
# ==========================================
vraies_classes = []
predictions_classes = []

for images, labels in val_ds:
    preds = model.predict(images, verbose=0)
    predictions_classes.extend(np.argmax(preds, axis=1))
    vraies_classes.extend(labels.numpy())

print(classification_report(vraies_classes, predictions_classes, target_names=noms_classes))

# ==========================================
# ÉTAPE 9 : Test sur une image
# ==========================================
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt

chemin_image_test = "dataset/garbage classification/Garbage classification/plastic/plastic1.jpg"
img = image.load_img(chemin_image_test, target_size=(224, 224))

plt.imshow(img)
plt.axis("off")
plt.show()

img_array = image.img_to_array(img)
img_array = np.expand_dims(img_array, axis=0)

predictions = model.predict(img_array)
classe_predite = noms_classes[np.argmax(predictions)]
confiance = np.max(predictions) * 100

print(f"Le modèle prédit : {classe_predite} (confiance : {confiance:.1f}%)")