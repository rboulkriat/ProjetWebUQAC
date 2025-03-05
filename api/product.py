from flask import Blueprint, jsonify
from Connexion.DatabaseService import fetch_products
from Connexion.DatabaseService import initialize_db
from Services import Product
from peewee import fn  # Importer les fonctions de peewee, au cas où vous en auriez besoin

orders_bp = Blueprint('toto', __name__)

@orders_bp.route("/toto", methods=["GET"])
def get_products():
    # Initialiser la base de données et récupérer les produits externes
    initialize_db()
    fetch_products()  # Cette fonction récupère et insère les produits dans la base

    try:
        # Utiliser SQL brut pour récupérer les produits
        query = "SELECT * FROM product"  # Requête brute pour obtenir tous les produits
        products = Product.raw(query)  # Exécuter la requête SQL

        # Créer une liste des produits récupérés
        products_list = [{"id": p.id, "name": p.name, "description": p.description,
                          "price": p.price, "in_stock": p.in_stock,
                          "weight": p.weight, "image": p.image} for p in products]

        # Si la liste est vide, retourner le message 'Aucun produit trouvé'
        if not products_list:
            return jsonify({"message": "Aucun produit trouvé."}), 404

        # Retourner la liste des produits sous format JSON
        return jsonify({"products": products_list})

    except Exception as e:
        # En cas d'erreur lors de la récupération des produits
        return jsonify({"error": str(e)}), 500
