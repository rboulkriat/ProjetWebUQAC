#  Projet Web UQAC 

Ce projet est une API REST développée avec Flask, permettant la création, mise à jour et gestion de commandes produits. Il utilise PostgreSQL pour le stockage, Redis pour le cache, et Docker pour l'orchestration.

---

## Les Technologies utilisées

- Python 3.9 + Flask
- PostgreSQL 12
- Redis 6 (alpine)
- Docker / Docker Compose
- RQ (Redis Queue) pour la gestion asynchrone

---

##  Installation et Lancement

service Docker : 
docker compose build
docker compose up

Initialisation de la base de données:
docker exec -it api8inf349-app flask init-db



### Prérequis

- Docker Desktop installé
- Docker en cours d’exécution (`docker info` doit fonctionner)

### Lancer le projet


docker compose build
docker compose up

L’API sera accessible sur  http://localhost:5000

Initialisation de la base de données avec docker exec -it api8inf349-app flask init-db

### L’API comporte plusieurs routes : 
Pour créer une commande : POST /order 
Exemple de JSON accepté : 
{
  "products": [
	{ "id": 1, "quantity": 2 },
	{ "id": 2, "quantity": 1 }
  ]
}

Pour récupérer une commande : GET /order/<id>

Récupère d’abord depuis Redis (résilience)
Sinon, fallback vers PostgreSQL

Pour mettre à jour les infos clients : PUT /order/<id>
Exemple de JSON accepté : 
{
  "order": {
	"email": "test@mail.com",
	"shipping_information": {
  	"country": "Canada",
  	"address": "123 rue Test",
  	"postal_code": "H2X 1A1",
  	"city": "Chicoutimi",
  	"province": "QC"
	}
  }
}

Pour modifier une commande : PUT /order/<id>
Exemple de JSON accepté : 

"order": {
  	"email": "client@test.com",
  	"shipping_information": {
    	"country": "Canada",
    	"address": "123 Rue des Tests",
    	"postal_code": "G7H 1X2",
    	"city": "Chicoutimi",
    	"province": "QC"
  	}
	}
  }'

Pour payer une commande : PUT /order/<id> (Bientôt fonctionnel)
Exemple de JSON accepté : 
credit_card

Pour voir les données stockées dans Redis pour une commande : GET /debug/cache/<id>

