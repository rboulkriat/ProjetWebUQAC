from flask import Flask
from api.order import order_bp
from api.product import products_bp
from Connexion.DatabaseService import initialize_db

app = Flask(__name__)

# Enregistrer les blueprints
app.register_blueprint(order_bp)
app.register_blueprint(products_bp)

# Commande CLI pour initialiser la base de données
@app.cli.command("init-db")
def init_db():
    """Créer les tables dans la base de données"""
    initialize_db()

# Point d'entrée (non utilisé avec flask run, mais utile en test direct)
if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.run(host="0.0.0.0", port=5000)
