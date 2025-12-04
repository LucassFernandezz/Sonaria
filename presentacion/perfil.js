// =======================
// Redirige si no está logueado
// =======================
async function verificarLogin() {
    const resp = await fetch("http://localhost:5000/auth/me", {
        credentials: "include"
    });

    const data = await resp.json();

    if (!data.autenticado) {
        window.location.href = "login.html";
    }
}

verificarLogin();


// =======================
// Cargar datos del perfil
// =======================
async function cargarPerfil() {
    const resp = await fetch("http://localhost:5000/perfiles/me", {
        credentials: "include"
    });

    const data = await resp.json();

    if (!data.ok) return;

    const p = data.perfil;

    document.getElementById("nombre_artistico").value = p.nombre_artistico || "";
    document.getElementById("descripcion").value = p.descripcion || "";
    document.getElementById("genero_principal").value = p.genero_principal || "";
    document.getElementById("habilidades").value = p.habilidades || "";
}

cargarPerfil();


// =======================
// Modo edición
// =======================
const btnEditar = document.getElementById("btn-editar");
const btnGuardar = document.getElementById("btn-guardar");

btnEditar.onclick = () => {
    document.querySelectorAll("input, textarea").forEach(i => i.disabled = false);
    btnEditar.classList.add("oculto");
    btnGuardar.classList.remove("oculto");
};


// =======================
// Guardar cambios
// =======================
btnGuardar.onclick = async () => {

    const datos = {
        nombre_artistico: document.getElementById("nombre_artistico").value,
        descripcion: document.getElementById("descripcion").value,
        genero_principal: document.getElementById("genero_principal").value,
        habilidades: document.getElementById("habilidades").value
    };

    const resp = await fetch("http://localhost:5000/perfiles/me", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(datos)
    });

    const data = await resp.json();

    if (data.ok) {
        alert("Perfil actualizado");

        // bloquear campos
        document.querySelectorAll("input, textarea").forEach(i => i.disabled = true);
        btnGuardar.classList.add("oculto");
        btnEditar.classList.remove("oculto");
    }
};
