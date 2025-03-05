from peewee import *
import requests
import json

# Connexion à la base de données SQLite
db = SqliteDatabase("orders.db")

class BaseModel(Model):
    class Meta:
        database = db


def initialize_db():
        try:
            db.connect(reuse_if_open=True)
            print("Connexion réussie !")

            # Création de la table 'Product' avec une requête SQL brute
            db.execute_sql('CREATE TABLE IF NOT EXISTS product (\n'
                           '                id INTEGER PRIMARY KEY,\n'
                           '                name TEXT NOT NULL,\n'
                           '                description TEXT,\n'
                           '                price REAL,\n'
                           '                in_stock BOOLEAN,\n'
                           '                weight INTEGER,\n'
                           '                image TEXT\n'
                           '            )')
            print("Table 'Product' créée ou déjà existante.")


        except Exception as e:
            print(f"Erreur lors de la connexion à la base de données : {e}")
        finally:
            db.close()


# Récupérer les produits externes et les insérer dans la base de données


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

