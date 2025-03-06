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



