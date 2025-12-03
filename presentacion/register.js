const form = document.getElementById("registerForm");
const msg = document.getElementById("mensaje");
const msgOk = document.getElementById("mensaje-ok");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    msg.textContent = "";
    msgOk.textContent = "";

    const email = document.getElementById("email").value.trim();
    const pass1 = document.getElementById("password").value.trim();
    const pass2 = document.getElementById("password2").value.trim();

    // === Validaciones del lado del cliente ===
    if (!email.includes("@") || !email.includes(".")) {
        msg.textContent = "Ingresa un email válido.";
        return;
    }

    if (pass1.length < 6) {
        msg.textContent = "La contraseña debe tener al menos 6 caracteres.";
        return;
    }

    if (pass1 !== pass2) {
        msg.textContent = "Las contraseñas no coinciden.";
        return;
    }

    // === Enviar al backend ===
    try {
        const resp = await fetch("http://localhost:5000/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password: pass1 })
        });

        const data = await resp.json();

        if (!data.ok) {
            msg.textContent = data.error;
            return;
        }

        // OK
        msgOk.textContent = "Registro exitoso. Redirigiendo...";
        setTimeout(() => {
            window.location.href = "login.html";
        }, 1200);

    } catch (e) {
        msg.textContent = "Error de conexión con el servidor.";
    }
});

