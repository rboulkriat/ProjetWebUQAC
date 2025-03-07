import requests
from peewee import *

# Connexion à la base de données SQLite
db = SqliteDatabase('orders.db')

class Product(Model):  # Hérite de `peewee.Model`
    id = IntegerField(primary_key=True)
    name = CharField()
    description = CharField()
    price = FloatField()
    in_stock = BooleanField()
    weight = IntegerField()
    image = CharField()

    class Meta:
        database = db  # Spécifie la base de données pour ce modèle


def fetch_products():
    url = "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    try:
        response = requests.get(url)
        print(f"Statut de la requête : {response.status_code}")

        if response.status_code == 200:
            products = response.json().get("products", [])
            print(f"{len(products)} produits récupérés")

            # Insérer les produits dans la base de données si nécessaire
            with db.atomic():
                for prod in products:
                    db.execute_sql('''
                        INSERT OR REPLACE INTO product (id, name, description, price, in_stock, weight, image)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (prod["id"], prod["name"], prod["description"], prod["price"],
                          prod["in_stock"], prod["weight"], prod["image"]))
                    print(f"Produit ajouté ou mis à jour : {prod['name']}")

            # Retourner les produits sous forme de dictionnaire
            return {"products": products}

        else:
            print(f"Erreur lors de la récupération des produits, statut : {response.status_code}")
            return {"error": f"Erreur {response.status_code}", "message": response.text}

    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des produits : {e}")
        return {"error": "Exception", "message": str(e)}

