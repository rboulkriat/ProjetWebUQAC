from peewee import *
import os
import redis
from dotenv import load_dotenv
import requests

load_dotenv()

# Connexion Redis
redis_conn = redis.from_url(os.getenv("REDIS_URL"))

# Connexion PostgreSQL avec Peewee
db = PostgresqlDatabase(
    os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT"))
)

# Définir un modèle de base
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

def initialize_db():
    """Initialiser la base de données et créer les tables"""
    db.connect(reuse_if_open=True)
    db.create_tables([Product], safe=True)
    print("Tables créées avec succès !")

# Fonction pour récupérer les produits via l'API
def fetch_products():
    url = "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            products = response.json().get("products", [])
            if not products:
                print("Aucun produit trouvé dans la réponse.")
            else:
                print(f"{len(products)} produits récupérés.")
                with db.atomic():
                    for prod in products:
                        Product.insert(**prod).on_conflict(
                            conflict_target=[Product.id],
                            preserve=[Product.name, Product.description, Product.price,
                                      Product.in_stock, Product.weight, Product.image]
                        ).execute()
                print("Les produits ont été insérés dans la base de données.")
            return {"products": products}
        else:
            print(f"Erreur lors de la récupération des produits : {response.status_code}")
            return {"error": f"Erreur {response.status_code}", "message": response.text}
    except requests.RequestException as e:
        print(f"Une exception est survenue lors de la récupération des produits : {e}")
        return {"error": "Exception", "message": str(e)}
