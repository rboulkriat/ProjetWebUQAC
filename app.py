from flask import Flask
from api.product import orders_bp
from api.order import order_bp
from Connexion.DatabaseService import initialize_db

app = Flask(__name__)

# Enregistrer les blueprints
app.register_blueprint(orders_bp)
app.register_blueprint(order_bp)

# Commande pour initialiser la base de données
@app.cli.command('init-db')
def init_db():
    """Initialiser la base de données et créer les tables"""
    initialize_db()

# Lancer l'application Flask
if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.run(debug=True, host="0.0.0.0")
