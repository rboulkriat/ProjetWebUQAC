
import os
import redis
from flask import Blueprint, request, jsonify, redirect, url_for
from peewee import DoesNotExist
import json

from rq import Queue

from Connexion.DatabaseService import db ,Order, Product, initialize_db, OrderItem
from Services.tasks import process_payment



order_bp = Blueprint('order_bp', __name__)
PAYMENT_API_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))
q = Queue(connection=redis)



@order_bp.route("/order", methods=["POST"])
def create_order():
    try:
        data = request.get_json()

        # Compatibilité avec l'ancien format
        if "product" in data:
            data["products"] = [data["product"]]

        products_data = data.get("products", [])
        if not products_data:
            return jsonify({
                "error": "Aucun produit fourni dans la commande."
            }), 422

        with db.atomic():
            order = Order.create(total_price=0)
            total_price = 0
            total_weight = 0
            product_summary = []

            for item in products_data:
                product_id = item.get("id")
                quantity = item.get("quantity", 1)

                if not product_id or quantity < 1:
                    return jsonify({
                        "error": f"Produit invalide ou quantité incorrecte : {item}"
                    }), 422

                product = Product.get_or_none(Product.id == product_id)
                if not product:
                    return jsonify({
                        "error": f"Produit ID {product_id} non trouvé."
                    }), 404

                if not product.in_stock:
                    return jsonify({
                        "error": f"Produit ID {product_id} hors stock."
                    }), 422

                OrderItem.create(order=order, product=product, quantity=quantity)
                total_price += (product.price or 0) * quantity
                total_weight += (product.weight or 0) * quantity

                product_summary.append({
                    "id": product.id,
                    "name": product.name,
                    "quantity": quantity
                })

            if total_weight <= 500:
                shipping_price = 500
            elif total_weight <= 2000:
                shipping_price = 1000
            else:
                shipping_price = 2500

            order.total_price = total_price
            order.shipping_price = shipping_price
            order.save()

        return jsonify({
            "order_id": order.id,
            "total_price": total_price,
            "shipping_price": shipping_price,
            "products": product_summary,
            "status": "pending"
        }), 201

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500



@order_bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    try:
        key = f"order:{order_id}"
        cached_order = redis_client.get(key)

        if cached_order:
            print("Commande récupérée depuis Redis")
            return jsonify({"order": json.loads(cached_order)}), 200

        # Sinon, récupérer depuis Postgres
        order = Order.get(Order.id == order_id)
        products = [
            {
                "id": item.product.id,
                "quantity": item.quantity
            }
            for item in order.items
        ]

        order_data = {
            "id": order.id,
            "total_price": order.total_price,
            "shipping_price": order.shipping_price,
            "email": order.email,
            "shipping_information": {} if not order.shipping_information else json.loads(order.shipping_information),
            "paid": order.paid,
            "credit_card": {},
            "transaction": {} if not order.transaction else json.loads(order.transaction),
            "products": products
        }

        return jsonify({"order": order_data}), 200

    except DoesNotExist:
        return jsonify({"error": "Commande non trouvée"}), 404

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@order_bp.route("/order/<int:order_id>", methods=["PUT"])
def update_and_pay_order(order_id):
    try:
        order = Order.get(Order.id == order_id)
    except DoesNotExist:
        return jsonify({"error": "Commande non trouvée"}), 404

    data = request.get_json()

    # Si la commande est déjà payée, on bloque les modifications
    if order.paid:
        return jsonify({"error": "Commande déjà payée"}), 409

    order_data = data.get("order", {})
    credit_card = data.get("credit_card")

    # --- Traitement des infos client ---
    if order_data:
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

        # Frais de livraison (calcul basé sur tous les OrderItems)
        total_weight = sum(item.product.weight * item.quantity for item in order.items if item.product.weight)

        if total_weight <= 500:
            shipping_price = 500
        elif total_weight <= 2000:
            shipping_price = 1000
        else:
            shipping_price = 2500

        # Calcul taxe
        province = shipping_info["province"].upper()
        tax_rates = {"QC": 0.15, "ON": 0.13, "AB": 0.05, "BC": 0.12, "NS": 0.14}
        tax_rate = tax_rates.get(province, 0.0)
        total_price_tax = order.total_price * (1 + tax_rate)

        order.email = order_data["email"]
        order.shipping_information = json.dumps(shipping_info)
        order.shipping_price = shipping_price
        order.total_price_tax = total_price_tax
        order.save()

    # --- Traitement du paiement ---
    if credit_card:
        redis_client.set(f"order:processing:{order_id}", "processing")
        q.enqueue(process_payment, order_id, credit_card)
        return "", 202

    return jsonify({
        "order": {
            "id": order.id,
            "email": order.email,
            "shipping_information": json.loads(order.shipping_information) if order.shipping_information else {},
            "shipping_price": order.shipping_price,
            "total_price_tax": order.total_price_tax,
            "paid": order.paid
        }
    }), 200

def cache_order(order):
    key = f"order:{order.id}"
    order_data = {
        "id": order.id,
        "total_price": order.total_price,
        "shipping_price": order.shipping_price,
        "email": order.email,
        "shipping_information": json.loads(order.shipping_information) if order.shipping_information else {},
        "paid": order.paid,
        "credit_card": {},
        "transaction": json.loads(order.transaction) if order.transaction else {},
        "products": [
            {
                "id": item.product.id,
                "quantity": item.quantity
            }
            for item in order.items
        ]
    }
    redis_client.set(key, json.dumps(order_data), ex=3600)  # 1h

