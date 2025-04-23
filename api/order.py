import json 
import requests
from flask import Blueprint, request, jsonify, redirect, url_for
from peewee import DoesNotExist
from Services.Order import Order, create_order_table, OrderProduct
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

        # Vérification que l'on a bien un tableau de produits
        if "products" not in data or not isinstance(data["products"], list) or len(data["products"]) == 0:
            return jsonify({
                "errors": {
                    "products": {
                        "code": "missing-fields",
                        "name": "La commande doit inclure une liste de produits avec des quantités."
                    }
                }
            }), 422

        total_price = 0
        products = []

        # Vérification des produits et calcul du total
        for product_data in data["products"]:
            if "id" not in product_data or "quantity" not in product_data:
                return jsonify({
                    "errors": {
                        "product": {
                            "code": "missing-fields",
                            "name": "Chaque produit doit avoir un ID et une quantité."
                        }
                    }
                }), 422

            product_id = product_data["id"]
            quantity = product_data["quantity"]

            if quantity < 1:
                return jsonify({
                    "errors": {
                        "product": {
                            "code": "invalid-quantity",
                            "name": "La quantité d'un produit doit être supérieure ou égale à 1."
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

            # Calcul du prix total pour chaque produit
            product_total = product.price * quantity
            total_price += product_total
            products.append({
                "product_id": product.id,
                "quantity": quantity,
                "total_price": product_total
            })

        # Création de la commande en base de données
        # Création de la commande (vide d'abord, sans produits)
        order = Order.create(
            total_price=total_price,
            paid=False
        )

        # Création des lignes de commande
        for p in products:
            OrderProduct.create(
                order=order,
                product=Product.get_by_id(p["product_id"]),
                quantity=p["quantity"]
            )

        # Retourner l'URL de la commande créée
        return redirect(url_for("order_bp.get_order", order_id=order.id)), 302

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@order_bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    try:
        order = Order.get(Order.id == order_id)
        products = []
        for op in order.order_products:
            products.append({
                "product_id": op.product.id,
                "name": op.product.name,
                "quantity": op.quantity,
                "unit_price": op.product.price,
                "total_price": op.product.price * op.quantity
            })

        # Calculer la taxe et les frais de livraison en fonction des produits
        total_price_tax = order.total_price  # taxe préliminaire (sans calcul de taxe pour le moment)
        shipping_price = 0  # Calcul des frais de livraison

        for product in products:
            # On suppose que chaque produit a un poids, sinon il faut adapter cette logique
            product_obj = Product.get(Product.id == product["product_id"])
            total_weight = product_obj.weight * product["quantity"]
            shipping_price += calculate_shipping(total_weight)

        # Calculer la taxe
        province = "QC"  # Par exemple, peut être dynamique selon l'info de l'utilisateur
        total_price_tax += calculate_tax(province, order.total_price)

        # Retourner les détails de la commande
        return jsonify({
            "order": {
                "id": order.id,
                "total_price": order.total_price,
                "total_price_tax": total_price_tax,
                "email": order.email,
                "shipping_information": json.loads(order.shipping_information) if order.shipping_information else {},
                "paid": order.paid,
                "transaction": order.transaction,
                "products": products,
                "shipping_price": shipping_price
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

    # Mettre à jour les informations de la commande
    if "order" in data:
        order_data = data["order"]

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

        # Mise à jour de la commande
        order.email = order_data["email"]
        order.shipping_information = json.dumps(shipping_info)
        order.save()

        return jsonify({
            "order": {
                "id": order.id,
                "email": order.email,
                "shipping_information": json.loads(order.shipping_information),
            }
        }), 200

    return jsonify({"error": "Requête invalide"}), 400
