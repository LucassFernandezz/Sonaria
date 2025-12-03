document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const mensaje = document.getElementById("mensaje");

    mensaje.textContent = "";

    try {
        const resp = await fetch("http://localhost:5000/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ email, password })
        });

        const data = await resp.json();

        if (!data.ok) {
            mensaje.textContent = data.error;
            return;
        }

        // LOGIN OK → redirigir
        window.location.href = "home.html";

    } catch (error) {
        mensaje.textContent = "Error de conexión con el servidor.";
    }
});
