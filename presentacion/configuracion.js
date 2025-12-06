const API = "http://localhost:5000";

const msg = document.getElementById("mensaje");
const emailText = document.getElementById("user-email");
const logoutBtn = document.getElementById("logout-btn");

// 1) Obtener usuario actual
async function cargarUsuario() {
    try {
        const resp = await fetch(`${API}/auth/me`, { credentials: "include" });
        const data = await resp.json();

        if (!data.autenticado) {
            emailText.textContent = "No estás autenticado.";
            logoutBtn.style.display = "none";
            return;
        }

        emailText.textContent = "Sesión iniciada como: " + data.email;

    } catch (err) {
        emailText.textContent = "Error al cargar usuario.";
    }
}

// 2) Cerrar sesión
logoutBtn.addEventListener("click", async () => {

    try {
        const resp = await fetch(`${API}/auth/logout`, {
            method: "POST",
            credentials: "include"
        });

        const data = await resp.json();

        msg.textContent = data.mensaje || "Sesión cerrada.";
        msg.style.color = "green";

        // Redirigir al login luego de 1 segundo
        setTimeout(() => {
            window.location.href = "login.html";
        }, 1000);

    } catch (err) {
        msg.textContent = "Error al cerrar sesión.";
        msg.style.color = "red";
    }

});

cargarUsuario();
