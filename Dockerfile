# =============================================================================
# Dockerfile — EcoSort-Search
# Construit une image autonome de l'application Streamlit, telecharge le
# modele CNN depuis Google Drive au moment du build, et expose le port 8501.
#
# Usage :
#   docker build -t ecosort .
#   docker run -p 8501:8501 ecosort
# =============================================================================

# Image de base Python legere (Debian slim)
FROM python:3.11-slim

# Dependances systeme minimales requises par Pillow / OpenCV-like et TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Couche dependances (mise en cache tant que requirements.txt ne change pas) ---
# On copie d'abord requirements.txt seul : Docker ne relance 'pip install' que
# si ce fichier change, pas a chaque modification du code -> builds plus rapides.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gdown

# --- Telechargement automatique du modele depuis Google Drive ---
# Le modele .h5 n'est pas versionne dans Git (trop lourd). On le recupere ici.
# Remplacer GDRIVE_FILE_ID par l'identifiant du fichier Drive public.
ARG GDRIVE_FILE_ID=1BNt_8IBORnOEIKzQY44jr9ZsJF5fFdXh
RUN mkdir -p /app/ml/models \
    && gdown "https://drive.google.com/uc?id=${GDRIVE_FILE_ID}" \
        -O /app/ml/models/modele_eco_sort.h5

# --- Copie du reste du code applicatif (apres les deps, pour le cache) ---
COPY . .

# Port par defaut de Streamlit
EXPOSE 8501

# Lancement de l'application, accessible depuis l'exterieur du conteneur
CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
