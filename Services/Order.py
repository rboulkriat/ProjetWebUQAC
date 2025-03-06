from peewee import *
from Services.Product import Product  # Import du modèle Product

# Connexion à la base de données
db = SqliteDatabase("orders.db")

class Order(Model):
    id = AutoField()  # Clé primaire auto-incrémentée
    product = ForeignKeyField(Product, backref="orders")  # Relation avec Product
    quantity = IntegerField()  # Quantité commandée
    total_price = FloatField()  # Prix total (sans taxes ni livraison)
    total_price_tax = FloatField(null=True)  # Prix total avec taxes
    email = CharField(null=True)  # Email du client
    shipping_information = TextField(null=True)  # Adresse de livraison en JSON
    paid = BooleanField(default=False)  # Statut de paiement
    transaction = TextField(null=True)  # Infos de transaction JSON 
    shipping_price = FloatField(null=True)  # Frais de livraison

    class Meta:
        database = db  # Associer le modèle à la base de données

# Création de la table si elle n'existe pas
def create_order_table():
    db.connect(reuse_if_open=True)
    db.create_tables([Order])
    db.close()
