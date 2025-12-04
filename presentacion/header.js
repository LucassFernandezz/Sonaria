// ==========================
// Cargar el header
// ==========================
async function cargarHeader() {
    const cont = document.getElementById("header-container");
    if (!cont) return;

    const resp = await fetch("header.html");
    const html = await resp.text();
    cont.innerHTML = html;

    configurarHeader();
}

cargarHeader();


// ==========================
// Lógica del header dinámico
// ==========================
async function configurarHeader() {

    // ---- botones ----
    const btnLogin = document.getElementById("btn-login");
    const btnRegister = document.getElementById("btn-register");

    const btnSubir = document.getElementById("btn-subir");
    const btnPerfil = document.getElementById("btn-perfil");
    const btnSettings = document.getElementById("btn-settings");

    const btnAdmin = document.getElementById("btn-admin");

    // SUBIR AUDIO
    document.getElementById("btn-subir")?.addEventListener("click", () => {
        window.location.href = "subir.html";
    });

    // CONFIGURACIÓN
    document.getElementById("btn-settings")?.addEventListener("click", () => {
        window.location.href = "configuracion.html";
    });

    // PERFIL
    document.getElementById("btn-perfil")?.addEventListener("click", () => {
        window.location.href = "perfil.html";
    });

    // PANEL ADMIN
    document.getElementById("btn-admin")?.addEventListener("click", () => {
        window.location.href = "admin_panel.html";
    });

    // Consulta al backend
    const resp = await fetch("http://localhost:5000/auth/me", {
        credentials: "include"
    });

    const data = await resp.json();


    // ==========================
    // Visitante (no logueado)
    // ==========================
    if (!data.autenticado) {
        btnLogin.classList.remove("oculto");
        btnRegister.classList.remove("oculto");
        return; // No mostramos más
    }


    // ==========================
    // Usuario logueado
    // ==========================
    btnSubir.classList.remove("oculto");
    btnPerfil.classList.remove("oculto");
    btnSettings.classList.remove("oculto");

    // ==========================
    // Es ADMIN
    // ==========================
    if (data.rol === "admin") {
        btnAdmin.classList.remove("oculto");
    }
}
