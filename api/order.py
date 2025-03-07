import json 
import requests
from flask import Blueprint, request, jsonify, redirect, url_for
from peewee import DoesNotExist
from Services.Order import Order, create_order_table
from Services.Product import Product
from Connexion.DatabaseService import initialize_db

order_bp = Blueprint('order_bp', __name__)
PAYMENT_API_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"

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

def calculate_shipping(weight):
    """Calcule les frais de livraison en fonction du poids"""
    if weight <= 500:
        return 5  # 5$
    elif weight <= 2000:
        return 10  # 10$
    else:
        return 25  # 25$

def calculate_tax(province, total_price):
    """Calcule la taxe selon la province"""
    tax_rates = {
        "QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14
    }
    return total_price * tax_rates.get(province.upper(), 0.0)

@order_bp.route("/order/<int:order_id>", methods=["PUT"])
def update_or_pay_order(order_id):
    try:
        order = Order.get(Order.id == order_id)
    except DoesNotExist:
        return jsonify({"error": "Commande non trouvée"}), 404

    data = request.get_json()

    # Vérifier si l'on met à jour l'email et l'adresse de livraison
    if "order" in data:
        order_data = data["order"]

        # Vérifier que l'on ne fournit pas "credit_card" avec "shipping_information" ou "email"
        if "credit_card" in data:
            return jsonify({
                "error": {
                    "code": "invalid-fields",
                    "message": "Les informations de paiement doivent être envoyées séparément des informations de livraison et d'email."
                }
            }), 422

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

        # Vérification de l'existence du produit
        try:
            product = Product.get(Product.id == order.product_id)
        except DoesNotExist:
            return jsonify({"errors": {"product": {"code": "not-found", "name": "Produit introuvable"}}}), 404

        # Calcul des frais de livraison
        total_weight = product.weight * order.quantity
        shipping_price = calculate_shipping(total_weight)

        # Calcul des taxes
        province = shipping_info["province"].upper()
        total_price_tax = order.total_price + calculate_tax(province, order.total_price)

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
            }
        }), 200

    # Gérer le paiement
    if "credit_card" in data:
        if not order.email or not order.shipping_information:
            return jsonify({"error": {
                "code": "missing-fields",
                "message": "Les informations du client sont nécessaires avant d'appliquer une carte de crédit."
            }}), 422

        if order.paid:
            return jsonify({"error": {
                "code": "already-paid",
                "message": "La commande a déjà été payée."
            }}), 422

        credit_card = data["credit_card"]
        payload = {
            "credit_card": credit_card,
            "amount_charged": order.total_price_tax + order.shipping_price
        }

        try:
            response = requests.post(PAYMENT_API_URL, json=payload)
            payment_response = response.json()

            if response.status_code == 200 and payment_response.get("transaction", {}).get("success"):
                # Stocker les infos de transaction
                order.paid = True
                order.credit_card_info = json.dumps({
                    "first_digits": payment_response["credit_card"]["first_digits"],
                    "last_digits": payment_response["credit_card"]["last_digits"],
                    "expiration_year": payment_response["credit_card"]["expiration_year"],
                    "expiration_month": payment_response["credit_card"]["expiration_month"]
                })
                order.transaction_id = payment_response["transaction"]["id"]
                order.transaction_details = json.dumps(payment_response["transaction"])
                order.save()

                return jsonify({"order": {
                    "id": order.id,
                    "email": order.email,
                    "shipping_information": json.loads(order.shipping_information),
                    "shipping_price": order.shipping_price,
                    "total_price_tax": order.total_price_tax,
                    "paid": order.paid,
                    "credit_card_info": json.loads(order.credit_card_info),
                    "transaction_details":order.transaction_details,
                }}), 200
            else:
                return jsonify({"error": payment_response}), 422

        except requests.RequestException as e:
            return jsonify({"error": "Service de paiement indisponible", "details": str(e)}), 503

    return jsonify({"error": "Requête invalide"}), 400