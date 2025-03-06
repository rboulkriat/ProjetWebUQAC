# conftest.py
import pytest
from peewee import SqliteDatabase
from flask import Flask

from app import app as flask_app
from Services.Product import Product
from Services.Order import Order
from Connexion.DatabaseService import db as main_db

# Configuration de la base de données de test
TEST_DB = SqliteDatabase(':memory:')

@pytest.fixture(scope='module')
def app():
    """Crée une instance de l'application Flask pour les tests"""
    # Configuration spéciale pour les tests
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': TEST_DB
    })
    
    yield flask_app

@pytest.fixture(scope='module')
def client(app):
    """Crée un client de test Flask"""
    with app.test_client() as client:
        with app.app_context():
            # Initialisation de la base de données de test
            TEST_DB.bind([Product, Order])
            TEST_DB.connect(reuse_if_open=True)
            TEST_DB.create_tables([Product, Order])
            
            # Peupler la base avec un produit de test
            Product.create(
                id=1,
                name="Test Product",
                description="Test Description",
                price=28.1,
                in_stock=True,
                weight=400,
                image="test.jpg"
            )
            
        yield client
        
        # Nettoyage après les tests
        with app.app_context():
            TEST_DB.drop_tables([Product, Order])
            TEST_DB.close()

@pytest.fixture(scope='function')
def clean_db(client):
    """Réinitialise la base de données avant chaque test"""
    Order.delete().execute()
    Product.delete().execute()
    
    # Recréer le produit de base
    Product.create(
        id=1,
        name="Test Product",
        description="Test Description",
        price=28.1,
        in_stock=True,
        weight=400,
        image="test.jpg"
    )