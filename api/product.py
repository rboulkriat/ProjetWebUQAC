from flask import Blueprint, jsonify
from Connexion.DatabaseService import initialize_db
from Services import Product

products_bp = Blueprint('products_bp', __name__)

@orders_bp.route("/", methods=["GET"])
def get_products():
    try:

        # Récupérer les produits depuis la fonction fetch_products
        products_json = Product.fetch_products()

        # Si des produits sont récupérés, on les retourne directement
        return jsonify(products_json), 200  # Flask s'occupe de la conversion en JSON

    except Exception as e:
        # En cas d'erreur, retourner un message d'erreur avec le statut 500
        print(f"Erreur lors de la récupération des produits: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
