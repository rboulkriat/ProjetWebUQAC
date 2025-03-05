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
