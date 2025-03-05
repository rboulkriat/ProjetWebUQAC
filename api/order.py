from flask import Blueprint, request, jsonify, redirect, url_for
from peewee import DoesNotExist
from Services.Order import Order, create_order_table
from Services.Product import Product
from Connexion.DatabaseService import initialize_db

order_bp = Blueprint('order_bp', __name__)

# Initialiser la base de données au lancement du module
initialize_db()
create_order_table()

@order_bp.route("/order", methods=["POST"])
def create_order():
    try:
        data = request.get_json()

        # Vérification de l'objet product
        if "product" not in data or "id" not in data["product"] or "quantity" not in data["product"]:
            return jsonify({
                "errors": {
                    "product": {
                        "code": "missing-fields",
                        "name": "La création d'une commande nécessite un produit avec un ID et une quantité."
                    }
                }
            }), 422

        product_id = data["product"]["id"]
        quantity = data["product"]["quantity"]

        # Vérification de la quantité
        if quantity < 1:
            return jsonify({
                "errors": {
                    "product": {
                        "code": "missing-fields",
                        "name": "La quantité doit être supérieure ou égale à 1."
                    }
                }
            }), 422

        # Vérification si le produit existe
        try:
            product = Product.get(Product.id == product_id)
        except DoesNotExist:
            return jsonify({
                "errors": {
                    "product": {
                        "code": "not-found",
                        "name": "Le produit spécifié n'existe pas."
                    }
                }
            }), 422

        # Vérification si le produit est en stock
        if not product.in_stock:
            return jsonify({
                "errors": {
                    "product": {
                        "code": "out-of-inventory",
                        "name": "Le produit demandé n'est pas en inventaire."
                    }
                }
            }), 422

        # Calcul du total sans taxes
        total_price = product.price * quantity

        # Création de la commande en base de données
        order = Order.create(
            product=product,
            quantity=quantity,
            total_price=total_price
        )

        # Retourner l'URL de la commande créée
        return redirect(url_for("order_bp.get_order", order_id=order.id)), 302

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@order_bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    try:
        order = Order.get(Order.id == order_id)

        return jsonify({
            "order": {
                "id": order.id,
                "total_price": order.total_price,
                "total_price_tax": order.total_price_tax,
                "email": order.email,
                "shipping_information": order.shipping_information,
                "paid": order.paid,
                "transaction": order.transaction,
                "product": {
                    "id": order.product.id,
                    "quantity": order.quantity
                },
                "shipping_price": order.shipping_price
            }
        }), 200

    except DoesNotExist:
        return jsonify({"error": "Commande non trouvée"}), 404
