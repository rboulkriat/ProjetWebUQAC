import json
import os
import redis
import requests
from Connexion.DatabaseService import Order

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))
PAYMENT_API_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"

def process_payment(order_id, credit_card):
    try:
        order = Order.get(Order.id == order_id)

        response = requests.post(PAYMENT_API_URL, json={
            "amount": order.total_price + order.shipping_price,
            "credit_card": credit_card
        })

        result = response.json()
        order.transaction = json.dumps(result)
        order.paid = result.get("success", False)
        order.save()

        # Enregistrer dans Redis que le paiement est terminé
        redis_client.set(f"order:processing:{order_id}", "done")
        redis_client.set(f"order:{order_id}", json.dumps({
            "id": order.id,
            "total_price": order.total_price,
            "shipping_price": order.shipping_price,
            "email": order.email,
            "shipping_information": json.loads(order.shipping_information or '{}'),
            "paid": order.paid,
            "credit_card": json.loads(order.credit_card or '{}'),
            "transaction": result,
            "products": [
                {
                    "id": item.product.id,
                    "quantity": item.quantity
                }
                for item in order.items
            ]
        }))

    except Exception as e:
        print("Erreur dans process_payment:", e)
