from flask import Flask

from api.product import orders_bp
from api.order import order_bp

app = Flask(__name__)

# Enregistrer le blueprint
app.register_blueprint(orders_bp)  # Enregistrer sans préfixe
app.register_blueprint(order_bp)  # Enregistrement des routes de commande

@app.route('/')
def home():
    return "Bienvenue sur l'application Flask !"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
