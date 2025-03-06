# tests/test_order_c.py
import pytest
import json
from Services.Product import Product
from Services.Order import Order

# --------------------------
# Scénarios de test principaux
# --------------------------

def test_update_order_success(client):
    """Teste la mise à jour réussie des informations clients"""
    # Créer un produit et une commande
    product = Product.create(id=1, name="Test",description="Description de test", image="img", price=28.1, weight=400, in_stock=True)
    order = Order.create(product=product, quantity=2, total_price=56.2)
    
    data = {
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
    
    response = client.put(f"/order/{order.id}", json=data)
    
    # Vérifications
    assert response.status_code == 200
    response_data = response.json["order"]
    
    assert response_data["email"] == "test@qc.ca"
    assert response_data["shipping_information"]["province"] == "QC"
    assert response_data["shipping_price"] == 10.0  # 800g → 10$
    assert response_data["total_price_tax"] == pytest.approx(64.63)  # 56.2 * 1.15

def test_missing_shipping_field(client):
    """Teste l'absence d'un champ obligatoire dans shipping_information"""
    product = Product.create(id=2, name="Test2",description="Description de test",image="img", price=30.0, weight=500, in_stock=True)
    order = Order.create(product=product, quantity=1, total_price=30.0)
    
    data = {
        "order": {
            "email": "test@on.ca",
            "shipping_information": {
                "country": "Canada",
                "address": "456 Rue Sec",
                "postal_code": "M5V 3L9",
                "city": "Toronto"
                # Province manquante
            }
        }
    }
    
    response = client.put(f"/order/{order.id}", json=data)
    
    assert response.status_code == 422
    assert "province" in response.json["errors"]["order"]["name"]

# --------------------------
# Tests de calcul des frais
# --------------------------

@pytest.mark.parametrize("weight,qty,expected", [
    (400, 1, 5.0),    # 400g → 5$
    (600, 1, 10.0),   # 600g → 10$
    (2500, 1, 25.0),  # 2500g → 25$
    (300, 2, 5.0),    # 600g → 10$ → Erreur? Non, 600g <500g?
])
def test_shipping_calculation(client, weight, qty, expected):
    """Teste le calcul des frais de livraison pour différents poids"""
    product = Product.create(id=3, name="PoidsTest",description="Description de test",image="img", price=10.0, weight=weight, in_stock=True)
    order = Order.create(product=product, quantity=qty, total_price=10.0*qty)
    
    data = {
        "order": {
            "email": "test@bc.ca",
            "shipping_information": {
                "country": "Canada",
                "address": "789 Ave",
                "postal_code": "V6B 1A1",
                "city": "Vancouver",
                "province": "BC"
            }
        }
    }
    
    response = client.put(f"/order/{order.id}", json=data)
    
    assert response.status_code == 200
    assert response.json["order"]["shipping_price"] == expected



# --------------------------
# Tests de calcul des taxes
# --------------------------

@pytest.mark.parametrize("province,rate", [
    ("QC", 1.15),
    ("ON", 1.13),
    ("AB", 1.05),
    ("BC", 1.12),
    ("NS", 1.14),
    ("XX", 1.00)  # Province invalide
])
def test_tax_calculation(client, province, rate):
    """Teste le calcul des taxes pour différentes provinces"""
    product = Product.create(id=4, name="TaxTest",description="Description de test",image="img", price=100.0, weight=100, in_stock=True)
    order = Order.create(product=product, quantity=1, total_price=100.0)
    
    data = {
        "order": {
            "email": "test@tax.ca",
            "shipping_information": {
                "country": "Canada",
                "address": "123 Tax St",
                "postal_code": "X0X 0X0",
                "city": "TaxCity",
                "province": province
            }
        }
    }
    
    response = client.put(f"/order/{order.id}", json=data)
    
    assert response.status_code == 200
    assert response.json["order"]["total_price_tax"] == pytest.approx(100.0 * rate)

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

# --------------------------
# Tests de validation
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