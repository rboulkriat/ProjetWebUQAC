from peewee import *
from Services.Product import Product  # Import du modèle Product

# Connexion à la base de données
#db = SqliteDatabase("orders.db")

class Order(Model):
    id = AutoField()
    product = ForeignKeyField(Product, backref="orders")
    quantity = IntegerField()
    total_price = FloatField()
    total_price_tax = FloatField(null=True)
    email = CharField(null=True)
    shipping_information = TextField(null=True)
    paid = BooleanField(default=False)
    transaction = TextField(null=True)
    shipping_price = FloatField(null=True)

# Création de la table si elle n'existe pas
def create_order_table():
    db.connect(reuse_if_open=True)
    db.create_tables([Order])
    db.close()
