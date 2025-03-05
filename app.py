from flask import Flask

from api.product import orders_bp

app = Flask(__name__)

# Enregistrer le blueprint
app.register_blueprint(orders_bp)  # Enregistrer sans préfixe

@app.route('/')
def home():
    return "Bienvenue sur l'application Flask !"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
