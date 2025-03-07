import os
import requests
from peewee import SqliteDatabase
from Connexion.DatabaseService import initialize_db
from Services.Product import fetch_products


### Vérifie la connexion à la base de données ###
def test_initialize_db():
    """Test si la base de données et la table sont créées correctement."""
    if os.path.exists("orders.db"):
        os.remove("orders.db")

    initialize_db()

    assert os.path.exists("orders.db"), "La base de données n'a pas été créée !"

    db = SqliteDatabase("orders.db")
    tables = db.get_tables()
    assert "product" in tables, "La table 'product' n'existe pas !"
    db.close()
    print("TEST: Test de la base de données réussi !")


### Vérifie la récupération des produits via l’API ###
def test_fetch_products():
    """Test si la fonction récupère bien des produits depuis l'API."""
    result = fetch_products()

    assert "products" in result, "La réponse ne contient pas de produits !"
    assert isinstance(result["products"], list), "Les produits ne sont pas sous forme de liste !"
    assert len(result["products"]) > 0, "Aucun produit récupéré !"

    print(f" {len(result['products'])} produits récupérés avec succès !")


### Vérifie l’insertion des produits dans la BD ###
def test_insert_products():
    """Test l'insertion des produits dans la base de données."""
    db = SqliteDatabase("orders.db")
    fetch_products()

    cursor = db.execute_sql("SELECT COUNT(*) FROM product")
    count = cursor.fetchone()[0]

    assert count > 0, "Aucun produit inséré dans la base !"
    print(f"TEST: {count} produits insérés avec succès dans la base !")

    db.close()


### Vérifie que l'API Flask fonctionne ###
def test_api():
    """Test si l'API Flask retourne bien les produits."""
    url = "http://127.0.0.1:5000/"
    response = requests.get(url)

    assert response.status_code == 200, f"Code HTTP inattendu : {response.status_code}"
    data = response.json()
    assert "products" in data, "Les produits ne sont pas dans la réponse JSON !"

    print("TEST: Test API Flask réussi !")



if __name__ == "__main__":
    test_initialize_db()
    test_fetch_products()
    test_insert_products()
    test_api()
