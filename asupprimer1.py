
import json

def test_add_client_info(client):
    order_data = {
        "product": {"id": 1, "quantity": 1}
    }
    post_response = client.post("/order", data=json.dumps(order_data), content_type="application/json")
    order_id = post_response.headers["Location"].split("/")[-1]

    # Ajouter les infos clients
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


