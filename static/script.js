let selectedProducts = [];

function fetchProducts() {
  fetch("/produits")
    .then(response => response.json())
    .then(data => {
      const products = data.products || [];
      const container = document.getElementById("product-list");
      container.innerHTML = "";

      products.forEach(prod => {
        const div = document.createElement("div");
        div.classList.add("product-card");
        div.innerHTML = `
          <label>
            <input type="number" min="0" id="qty-${prod.id}" value="0">
            ${prod.name} - ${prod.price}$
          </label>
        `;
        container.appendChild(div);
      });
    });
}

function createOrder() {
  const inputs = document.querySelectorAll('input[type="number"]');
  const products = [];

  inputs.forEach(input => {
    const qty = parseInt(input.value);
    if (qty > 0) {
      const id = parseInt(input.id.split("-")[1]);
      products.push({ id, quantity: qty });
    }
  });

  if (products.length === 0) {
    alert("Veuillez sélectionner au moins un produit.");
    return;
  }

  fetch("/order", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ products })
  })
    .then(response => response.json())
    .then(result => {
      if (result.order_id) {
        alert("Commande créée ! ID: " + result.order_id);
      } else {
        alert("Erreur : " + JSON.stringify(result));
      }
    });
}

function fetchOrder() {
  const id = document.getElementById("order-id").value;
  if (!id) {
    alert("Veuillez entrer un ID de commande.");
    return;
  }

  fetch(`/order/${id}`)
    .then(res => res.json())
    .then(data => {
      const resultDiv = document.getElementById("order-result");
      resultDiv.innerHTML = "";

      if (!data.order) {
        resultDiv.innerHTML = `<p class="error">Erreur : ${data.error || "Commande introuvable."}</p>`;
        return;
      }

      const order = data.order;

      resultDiv.innerHTML = `
        <h3>Commande #${order.id}</h3>
        <p><strong>Total :</strong> ${order.total_price} $</p>
        <p><strong>Frais de livraison :</strong> ${order.shipping_price} $</p>
        <p><strong>Payée :</strong> ${order.paid ? " Oui" : " Non"}</p>
        <h4>Produits :</h4>
        <ul>
        ${order.products.map(p => `<li> (ID ${p.id}) — Quantité : ${p.quantity}</li>`).join("")}
        </ul>
      `;

      if (!order.paid) {
        const hasEmail = order.email && order.email.trim() !== "";
        const hasShipping = order.shipping_information && Object.keys(order.shipping_information).length > 0;

        resultDiv.innerHTML += `
          <div class="section-card">
            <h4>Compléter la commande</h4>
            <input type="email" id="order-email" value="${order.email || ""}" placeholder="Email"><br>
            <input type="text" id="shipping-country" placeholder="Pays" value="${order.shipping_information.country || ""}"><br>
            <input type="text" id="shipping-address" placeholder="Adresse" value="${order.shipping_information.address || ""}"><br>
            <input type="text" id="shipping-city" placeholder="Ville" value="${order.shipping_information.city || ""}"><br>
            <input type="text" id="shipping-province" placeholder="Province" value="${order.shipping_information.province || ""}"><br>
            <input type="text" id="shipping-postal" placeholder="Code postal" value="${order.shipping_information.postal_code || ""}"><br>

            <h4>Paiement</h4>
            <input type="text" id="cc-name" placeholder="Nom sur la carte"><br>
            <input type="text" id="cc-number" placeholder="Numéro de carte"><br>
            <input type="number" id="cc-month" placeholder="Mois expiration"><br>
            <input type="number" id="cc-year" placeholder="Année expiration"><br>
            <input type="text" id="cc-cvv" placeholder="CVV"><br>
            <button onclick="updateAndPayOrder(${order.id})">Valider et Payer</button>
            <div id="update-result"></div>
          </div>
        `;
      }
    })
    .catch(err => {
      console.error(err);
      document.getElementById("order-result").innerHTML =
        `<p class="error">Erreur lors de la récupération de la commande.</p>`;
    });
}

function updateAndPayOrder(id) {
  const email = document.getElementById("order-email").value;

  const shipping = {
    country: document.getElementById("shipping-country").value,
    address: document.getElementById("shipping-address").value,
    city: document.getElementById("shipping-city").value,
    province: document.getElementById("shipping-province").value,
    postal_code: document.getElementById("shipping-postal").value
  };

  const credit_card = {
    name: document.getElementById("cc-name").value,
    number: document.getElementById("cc-number").value,
    expiration_month: parseInt(document.getElementById("cc-month").value),
    expiration_year: parseInt(document.getElementById("cc-year").value),
    cvv: document.getElementById("cc-cvv").value
  };

  const missingField = Object.entries({ ...shipping, ...credit_card }).find(([_, v]) => !v);
  if (!email || missingField) {
    alert("Tous les champs doivent être remplis.");
    return;
  }

  fetch(`/order/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      order: {
        email: email,
        shipping_information: shipping
      },
      credit_card: credit_card
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.order || data.message) {
        document.getElementById("update-result").innerHTML =
          `<p class="success">Commande #${id} complétée et payée ✅</p>`;
        fetchOrder();
      } else {
        document.getElementById("update-result").innerHTML =
          `<p class="error">Erreur : ${data.error || "paiement échoué"}</p>`;
      }
    })
    .catch(err => {
      console.error(err);
      document.getElementById("update-result").innerHTML =
        `<p class="error">Erreur réseau</p>`;
    });
}

window.onload = fetchProducts;
