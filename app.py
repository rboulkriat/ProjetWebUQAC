from flask import Flask, request, jsonify
from peewee import *
import requests


app = Flask(__name__)

# Connexion à la base de données SQLite
db = SqliteDatabase("orders.db")

class BaseModel(Model):
    class Meta:
        database = db

class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = CharField()
    description = CharField()
    price = FloatField()
    in_stock = BooleanField()
    weight = IntegerField()
    image = CharField()

class Order(BaseModel):
    id = AutoField()
    product_id = ForeignKeyField(Product, backref='orders')
    quantity = IntegerField()
    total_price = FloatField()
    total_price_tax = FloatField()
    email = CharField(null=True)
    shipping_information = TextField(null=True)
    paid = BooleanField(default=False)
    transaction = TextField(null=True)



# Initialisation de la base de données
def initialize_db():
    db.connect(reuse_if_open=True)
    db.drop_tables([Product, Order])  # Supprime les tables si elles existent
    db.create_tables([Product, Order])  # Recrée les tables
    db.close()
    print("Base de données et tables créées avec succès !")


# Récupérer les produits externes une seule fois
def fetch_products():
    url = "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    response = requests.get(url)
    if response.status_code == 200:
        products = response.json().get("products", [])
        with db.atomic():
            for prod in products:
                Product.get_or_create(
                    id=prod["id"],
                    defaults={
                        "name": prod["name"],
                        "description": prod["description"],
                        "price": prod["price"],
                        "in_stock": prod["in_stock"],
                        "weight": prod["weight"],
                        "image": prod["image"]
                    }
                )

@app.route("/", methods=["GET"])
def get_products():
    products = [product.__data__ for product in Product.select()]
    return jsonify({"products": products})


if __name__ == "__main__":
    initialize_db()  # CA MARCHE PASSSS
    fetch_products()
    app.run(debug=True)
