from flask import Blueprint, jsonify
from Connexion.DatabaseService import fetch_products, initialize_db

orders_bp = Blueprint('orders_bp', __name__)

@orders_bp.route("/toto", methods=["GET"])
def get_products():
    try:
        # Initialiser la base de données
        initialize_db()

        # Récupérer les produits depuis la fonction fetch_products
        products_json = fetch_products()

        # Si des produits sont récupérés, on les retourne directement
        return jsonify(products_json), 200  # Flask s'occupe de la conversion en JSON

    except Exception as e:
        # En cas d'erreur, retourner un message d'erreur avec le statut 500
        print(f"Erreur lors de la récupération des produits: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
