const API = "http://localhost:5000";

const msg = document.getElementById("mensaje");
const emailText = document.getElementById("user-email");
const logoutBtn = document.getElementById("logout-btn");

// Campos del formulario
const form = document.getElementById("rectificacion-form");
const campoInput = document.getElementById("campo-input");
const valorViejoInput = document.getElementById("valor-viejo-input");
const valorNuevoInput = document.getElementById("valor-nuevo-input");
const rectMsg = document.getElementById("rectificacion-msg");

// ==========================
// 1) Cargar usuario
// ==========================
async function cargarUsuario() {
    try {
        const resp = await fetch(`${API}/auth/me`, { credentials: "include" });
        const data = await resp.json();

        if (!data.autenticado) {
            emailText.textContent = "No estás autenticado.";
            logoutBtn.style.display = "none";
            form.style.display = "none";
            return;
        }

        emailText.textContent = "Sesión iniciada como: " + data.email;

    } catch (err) {
        emailText.textContent = "Error al cargar usuario.";
    }
}

// ==========================
// 2) Logout
// ==========================
logoutBtn.addEventListener("click", async () => {

    try {
        const resp = await fetch(`${API}/auth/logout`, {
            method: "POST",
            credentials: "include"
        });

        const data = await resp.json();

        msg.textContent = data.mensaje || "Sesión cerrada.";
        msg.style.color = "green";

        setTimeout(() => {
            window.location.href = "login.html";
        }, 1000);

    } catch (err) {
        msg.textContent = "Error al cerrar sesión.";
        msg.style.color = "red";
    }

});

// ==========================
// 3) Enviar rectificación
// ==========================
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    rectMsg.textContent = "";
    rectMsg.style.color = "black";

    const campo = campoInput.value;
    const viejo = valorViejoInput.value.trim();
    const nuevo = valorNuevoInput.value.trim();

    if (!campo || !viejo || !nuevo) {
        rectMsg.textContent = "Completa todos los campos.";
        rectMsg.style.color = "red";
        return;
    }

    try {
        const resp = await fetch(`${API}/rectificaciones/solicitar`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ campo, valor_nuevo: nuevo })
        });

        const data = await resp.json();

        if (data.ok) {
            rectMsg.textContent = "Solicitud enviada correctamente.";
            rectMsg.style.color = "green";

            campoInput.value = "";
            valorViejoInput.value = "";
            valorNuevoInput.value = "";

        } else {
            rectMsg.textContent = data.error || "Error al enviar solicitud.";
            rectMsg.style.color = "red";
        }

    } catch (err) {
        rectMsg.textContent = "Error de conexión con el servidor.";
        rectMsg.style.color = "red";
    }
});

// Iniciar
cargarUsuario();
