
import pytest
import json
from Services.Product import Product
from Services.Order import Order
import pytest
from app import app


# -------
# --------------------------
# Tests paiement 
# --------------------------
def test_add_client_credit_card(client):
    order_data = {
        "product": {"id": 1, "quantity": 1}
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    client_data = {
        "order": {
            "email": "client@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 rue Centrale",
                "postal_code": "G7X 1A1",
                "city": "Chicoutimi",
                "province": "QC"
            }
        }
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_data), content_type="application/json")

    client_credit_card = { 
        "credit_card" : { 
        "name" : "John Doe", 
        "number" : "4242 4242 4242 4242", 
        "expiration_year" : 2025, 
        "cvv" : "123", 
        "expiration_month" : 9 
        } 
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_credit_card), content_type="application/json")
    assert response.status_code == 200


def test_missing_client_data(client):
    order_data = {
        "product": {"id": 1, "quantity": 1}
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    client_credit_card = { 
        "credit_card" : { 
        "name" : "John Doe", 
        "number" : "4242 4242 4242 4242", 
        "expiration_year" : 2025, 
        "cvv" : "123", 
        "expiration_month" : 9 
        } 
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_credit_card), content_type="application/json")
    assert response.status_code == 422
    assert response.json== {'error': {'code': 'missing-fields', 'message': "Les informations du client sont nécessaires avant d'appliquer une carte de crédit."}}



#test paiement déjà effectué
def test_already_paid(client):
    order_data = {
        "product": {"id": 1, "quantity": 1}
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    client_data = {
        "order": {
            "email": "client@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 rue Centrale",
                "postal_code": "G7X 1A1",
                "city": "Chicoutimi",
                "province": "QC"
            }
        }
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_data), content_type="application/json")

    client_credit_card = { 
        "credit_card" : { 
        "name" : "John Doe", 
        "number" : "4242 4242 4242 4242", 
        "expiration_year" : 2025, 
        "cvv" : "123", 
        "expiration_month" : 9 
        } 
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_credit_card), content_type="application/json")
    response = client.put(f"/order/{order_id}", data=json.dumps(client_credit_card), content_type="application/json")
    assert response.status_code == 422
    assert response.json =={"error": {
                "code": "already-paid",
                "message": "La commande a déjà été payée."
            }}



def test_declined_card(client):
    order_data = {
        "product": {"id": 1, "quantity": 1}
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    client_data = {
        "order": {
            "email": "client@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 rue Centrale",
                "postal_code": "G7X 1A1",
                "city": "Chicoutimi",
                "province": "QC"
            }
        }
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_data), content_type="application/json")

    client_credit_card = {
        "credit_card" : { 
        "name" : "John Doe", 
        "number" : "4000 0000 0000 0002", 
        "expiration_year" : 2024, 
        "cvv" : "123", 
        "expiration_month" : 9 
   } 
}

    response = client.put(f"/order/{order_id}", data=json.dumps(client_credit_card), content_type="application/json")
    assert response.status_code == 422
    assert response.get_json()["error"]["errors"]["credit_card"]["code"]=="card-declined"


def test_expired_card(client):
    order_data = {
        "product": {"id": 1, "quantity": 1}
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    client_data = {
        "order": {
            "email": "client@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 rue Centrale",
                "postal_code": "G7X 1A1",
                "city": "Chicoutimi",
                "province": "QC"
            }
        }
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_data), content_type="application/json")

    client_credit_card = { 
        "credit_card" : { 
        "name" : "John Doe", 
        "number" : "4242 4242 4242 4242", 
        "expiration_year" : 2024, 
        "cvv" : "123", 
        "expiration_month" : 9 
        } 
    }

    response = client.put(f"/order/{order_id}", data=json.dumps(client_credit_card), content_type="application/json")
    assert response.status_code == 422
    assert response.get_json()["error"]["errors"]["credit_card"]["code"]=="card-expired"


def test_wrong_cvs(client):
    order_data = {
        "product": {"id": 1, "quantity": 1}
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    client_data = {
        "order": {
            "email": "client@example.com",
            "shipping_information": {
                "country": "Canada",
                "address": "123 rue Centrale",
                "postal_code": "G7X 1A1",
                "city": "Chicoutimi",
                "province": "QC"
            }
        }
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_data), content_type="application/json")

    client_credit_card = { 
        "credit_card" : { 
        "name" : "John Doe", 
        "number" : "4242 4242 4242 4242", 
        "expiration_year" : 2025, 
        "cvv" : "1223", 
        "expiration_month" : 9 
        } 
    }

    response = client.put(f"/order/{order_id}", data=json.dumps(client_credit_card), content_type="application/json")
    assert response.status_code == 422
    assert response.get_json()["error"]["errors"]["credit_card"]["code"]=="card-declined"



if __name__ == "__main__":
    client = app.test_client()
    test_add_client_credit_card(client)
    test_missing_client_data(client)
    test_already_paid(client)
    test_declined_card(client)
    test_expired_card(client)
    test_wrong_cvs(client)
