from peewee import *
from Services.Product import Product

# Connexion à la base de données PostgreSQL
from Connexion.DatabaseService import db

class Order(Model):
    id = AutoField()
    total_price = FloatField()
    total_price_tax = FloatField(null=True)
    email = CharField(null=True)
    shipping_information = TextField(null=True)
    paid = BooleanField(default=False)
    transaction = TextField(null=True)
    shipping_price = FloatField(null=True)

    class Meta:
        database = db

class OrderProduct(Model):
    order = ForeignKeyField(Order, backref='order_products')
    product = ForeignKeyField(Product, backref='product_orders')
    quantity = IntegerField()

    class Meta:
        database = db

def create_order_table():
    db.connect(reuse_if_open=True)
    db.create_tables([Order, OrderProduct])
    db.close()
