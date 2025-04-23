import json 
import requests
from flask import Blueprint, request, jsonify, redirect, url_for
from peewee import DoesNotExist
import json
from Connexion.DatabaseService import Order, Product, initialize_db

order_bp = Blueprint('order_bp', __name__)
PAYMENT_API_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"

# Initialiser la base de données au lancement du module
initialize_db()

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
        shipping_info = json.loads(order.shipping_information) if order.shipping_information else {}
        shipping_info = json.loads(order.shipping_information) if order.shipping_information else {}
        return jsonify({
            "order": {
                "id": order.id,
                "total_price": order.total_price,
                "total_price_tax": order.total_price_tax,
                "email": order.email,
                "shipping_information": shipping_info,
                "shipping_information": shipping_info,
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

@order_bp.route("/order/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    try:
        order = Order.get(Order.id == order_id)
    except DoesNotExist:
        return jsonify({"error": "Commande non trouvée"}), 404

    data = request.get_json()

    # Validation des champs obligatoires
    if "order" not in data:
        return jsonify({
            "errors": {
                "order": {"code": "missing-fields", "name": "Champs obligatoires manquants"}
            }
        }), 422

    order_data = data["order"]
    required_fields = ["email", "shipping_information"]
    for field in required_fields:
        if field not in order_data:
            return jsonify({
                "errors": {
                    "order": {"code": "missing-fields", "name": f"Champ '{field}' manquant"}
                }
            }), 422

    shipping_info = order_data["shipping_information"]
    required_shipping_fields = ["country", "address", "postal_code", "city", "province"]
    for field in required_shipping_fields:
        if field not in shipping_info:
            return jsonify({
                "errors": {
                    "order": {"code": "missing-fields", "name": f"Champ '{field}' manquant dans shipping_information"}
                }
            }), 422

    # Vérification des champs non autorisés
    allowed_fields = {"email", "shipping_information"}
    for key in order_data:
        if key not in allowed_fields:
            return jsonify({
                "errors": {
                    "order": {"code": "invalid-fields", "name": "Champs non autorisés"}
                }
            }), 422

    # Calcul des frais de livraison
    product = order.product
    total_weight = product.weight * order.quantity
    if total_weight <= 500:
        shipping_price = 500  # 5$
    elif total_weight <= 2000:
        shipping_price = 1000  # 10$
    else:
        shipping_price = 2500  # 25$

    # Calcul de la taxe selon la province
    province = shipping_info["province"].upper()
    tax_rates = {
        "QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14
    }
    tax_rate = tax_rates.get(province, 0.0)
    total_price_tax = order.total_price * (1 + tax_rate)

    # Mise à jour de la commande
    order.email = order_data["email"]
    order.shipping_information = json.dumps(shipping_info)
    order.shipping_price = shipping_price
    order.total_price_tax = total_price_tax
    order.save()

    return jsonify({
        "order": {
            "id": order.id,
            "email": order.email,
            "shipping_information": json.loads(order.shipping_information),
            "shipping_price": order.shipping_price,
            "total_price_tax": order.total_price_tax,
            # ... autres champs
        }
    }), 200
