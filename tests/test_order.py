
import pytest
import json
from Services.Product import Product
from Services.Order import Order


def test_add_client_info(client):
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
    assert response.status_code == 200
    assert response.get_json()["order"]["email"] == "client@example.com"


def test_add_client_info_missing_fields(client):
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
                "province": "QC"
            }
        }
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_data), content_type="application/json")
    assert response.status_code == 422  # Devrait échouer car l'adresse est incomplète


def test_update_order_success(client, clean_db):
    # Créer une commande
    order_data = {
        "product": {"id": 1, "quantity": 1}  # Utilise le produit existant (id=1)
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    # Ajouter les infos clients
    client_data = {
        "order": {
            "email": "test@qc.ca",
            "shipping_information": {
                "country": "Canada",
                "address": "201 Rue Principale",
                "postal_code": "G1A 0A1",
                "city": "Québec",
                "province": "QC"
            }
        }
    }
    response = client.put(f"/order/{order_id}", data=json.dumps(client_data), content_type="application/json")
    
    # Vérifications
    assert response.status_code == 200
    response_data = response.get_json()["order"]
    
    assert response_data["email"] == "test@qc.ca"
    assert response_data["shipping_information"]["province"] == "QC"
    assert response_data["shipping_price"] == 500  # 400g → 5$
    assert response_data["total_price_tax"] == pytest.approx(28.1 * 1.15)  # 28.1 est le prix du produit avec id=1

    
# --------------------------

def test_order_not_found(client):
    """Teste la réponse pour une commande inexistante"""
    response = client.put("/order/9999", json={"order": {}})
    assert response.status_code == 404
    assert "non trouvée" in response.json["error"]

def test_modify_restricted_field(client):
    """Teste la modification d'un champ protégé"""
    product = Product.create(id=5, name="RestrictTest",description="Description de test",image="img", price=50.0, weight=100, in_stock=True)
    order = Order.create(product=product, quantity=1, total_price=50.0)
    
    data = {
        "order": {
            "email": "test@restrict.ca",
            "shipping_information": {
                "country": "Canada",
                "address": "321 Protect St",
                "postal_code": "H0H 0H0",
                "city": "Montreal",
                "province": "QC"
            },
            "total_price": 10.0  # Champ interdit
        }
    }
    
    response = client.put(f"/order/{order.id}", json=data)
    
    assert response.status_code == 422
    assert "non autorisés" in response.json["errors"]["order"]["name"]

# --------------------------
# tests validation
# --------------------------

def test_missing_email(client):
    """Teste l'absence de l'email"""
    product = Product.create(id=6, name="EmailTest",description="Description de test",image="img", price=75.0, weight=100, in_stock=True)
    order = Order.create(product=product, quantity=1, total_price=75.0)
    
    data = {
        "order": {
            "shipping_information": {
                "country": "Canada",
                "address": "123 Email St",
                "postal_code": "E0E 0E0",
                "city": "EmailCity",
                "province": "QC"
            }
        }
    }
    
    response = client.put(f"/order/{order.id}", json=data)
    
    assert response.status_code == 422
    assert "email" in response.json["errors"]["order"]["name"]


# -------
# --------------------------
# Tests d'erreurs
# --------------------------

def test_order_not_found(client):
    """Teste la réponse pour une commande inexistante"""
    response = client.put("/order/9999", json={"order": {}})
    assert response.status_code == 404
    assert "non trouvée" in response.json["error"]

def test_modify_restricted_field(client):
    """Teste la modification d'un champ protégé"""
    product = Product.create(id=5, name="RestrictTest",description="Description de test",image="img", price=50.0, weight=100, in_stock=True)
    order = Order.create(product=product, quantity=1, total_price=50.0)
    
    data = {
        "order": {
            "email": "test@restrict.ca",
            "shipping_information": {
                "country": "Canada",
                "address": "321 Protect St",
                "postal_code": "H0H 0H0",
                "city": "Montreal",
                "province": "QC"
            },
            "total_price": 10.0  # Champ interdit
        }
    }
    
    response = client.put(f"/order/{order.id}", json=data)
    
    assert response.status_code == 422
    assert "non autorisés" in response.json["errors"]["order"]["name"]


