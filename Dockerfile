# Utilisation d'une image de base Python
FROM python:3.9-slim

# Définir un répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers requirements.txt et l'ensemble du projet
COPY requirements.txt /app/

# Installer les dépendances nécessaires
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le reste du projet dans le conteneur
COPY . /app/

# Exposer le port de l'application
EXPOSE 5000

# Définir la commande pour démarrer l'application Flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
