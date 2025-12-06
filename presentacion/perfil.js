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
    document.getElementById("habilidades").value = p.habilidades || "";

    // --- NUEVO: select de género con validación ---
    const generoSelect = document.getElementById("genero_principal");
    const generosValidos = Array.from(generoSelect.options).map(o => o.value);

    if (generosValidos.includes(p.genero_principal)) {
        generoSelect.value = p.genero_principal;
    } else {
        generoSelect.value = "";
    }
}

cargarPerfil();

// =======================
// Cargar proyectos propios
// =======================
async function cargarMisProyectos() {
    const cont = document.getElementById("mis-proyectos");
    cont.innerHTML = "<p>Cargando...</p>";

    const resp = await fetch("http://localhost:5000/proyectos/mios", {
        credentials: "include"
    });

    const data = await resp.json();

    if (!data.ok) {
        cont.innerHTML = "<p>Error al cargar proyectos.</p>";
        return;
    }

    cont.innerHTML = "";

    if (data.proyectos.length === 0) {
        cont.innerHTML = "<p>No tenés proyectos creados aún.</p>";
        return;
    }

    data.proyectos.forEach(p => {
        const card = document.createElement("div");
        card.className = "card-proyecto";
        card.style = `
            background:#fff;
            border:1px solid #ddd;
            padding:12px;
            border-radius:10px;
            cursor:pointer;
        `;
        card.innerHTML = `
            <h3>${p.titulo}</h3>
            <p style="color:#666;">${p.genero || ""}</p>
        `;

        // Click -> ir a colaboración del dueño
        card.onclick = () => {
            window.location.href = `proyecto.html?id=${p.id}`;
        };

        cont.appendChild(card);
    });
}

cargarMisProyectos();


// =======================
// Modo edición
// =======================
const btnEditar = document.getElementById("btn-editar");
const btnGuardar = document.getElementById("btn-guardar");

btnEditar.onclick = () => {
    document.querySelectorAll("input, textarea, select").forEach(i => i.disabled = false);
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
        document.querySelectorAll("input, textarea, select").forEach(i => i.disabled = true);
        btnGuardar.classList.add("oculto");
        btnEditar.classList.remove("oculto");
    }
};

