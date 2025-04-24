import os
from dotenv import load_dotenv
from peewee import *
import redis
import requests

load_dotenv()

# Connexion PostgreSQL
db = PostgresqlDatabase(
    os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432))
)

# Connexion Redis
redis_conn = redis.from_url(os.getenv("REDIS_URL"))

# Modèle de base
class BaseModel(Model):
    class Meta:
        database = db

# Modèle Product
class Product(BaseModel):
    id = IntegerField(primary_key=True)
    name = TextField()
    description = TextField(null=True)
    price = FloatField(null=True)
    in_stock = BooleanField(null=True)
    weight = IntegerField(null=True)
    image = TextField(null=True)

# Modèle Order
class Order(BaseModel):
    id = AutoField()
    total_price = FloatField(null=True)
    total_price_tax = FloatField(null=True)
    email = CharField(null=True)
    shipping_information = TextField(null=True)
    paid = BooleanField(default=False)
    transaction = TextField(null=True)
    shipping_price = FloatField(null=True)

class OrderItem(BaseModel):
    order = ForeignKeyField(Order, backref="items")
    product = ForeignKeyField(Product)
    quantity = IntegerField()


# Création des tables
def initialize_db():
   

    if db.is_closed():
        db.connect()
    db.drop_tables([OrderItem, Order, Product], cascade=True)
    db.create_tables([Product, Order, OrderItem], safe=True)
    print("Tables créées avec succès.")

# Nettoyage de texte (caractère nul)
def clean_text(value):
    if isinstance(value, str):
        return value.replace('\x00', '')
    return value

# Récupération des produits depuis l’API
def fetch_products():
    url = "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    try:
        response = requests.get(url)
        print(f"Statut de la requête : {response.status_code}")

        if response.status_code == 200:
            products = response.json().get("products", [])
            print(f"{len(products)} produits récupérés")

            with db.atomic():
                for prod in products:
                    Product.insert(
                        id=prod["id"],
                        name=clean_text(prod["name"]),
                        description=clean_text(prod.get("description")),
                        price=prod.get("price"),
                        in_stock=prod.get("in_stock"),
                        weight=prod.get("weight"),
                        image=clean_text(prod.get("image"))
                    ).on_conflict(
                        conflict_target=[Product.id],
                        preserve=[
                            Product.name,
                            Product.description,
                            Product.price,
                            Product.in_stock,
                            Product.weight,
                            Product.image
                        ]
                    ).execute()

            return {"products": products}

        else:
            return {"error": f"Erreur {response.status_code}", "message": response.text}

    except requests.RequestException as e:
        return {"error": "Exception", "message": str(e)}
