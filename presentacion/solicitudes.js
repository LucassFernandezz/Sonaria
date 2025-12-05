// ================================
// Obtener id del proyecto
// ================================
const params = new URLSearchParams(window.location.search);
const proyectoId = params.get("proyecto");

if (!proyectoId) {
    alert("No se especificó un proyecto");
    window.location.href = "home.html";
}


// ================================
// Cargar solicitudes
// ================================
async function cargarSolicitudes() {

    const resp = await fetch(`http://localhost:5000/colaboraciones/proyecto/${proyectoId}`, {
        credentials: "include"
    });

    const data = await resp.json();

    if (!data.ok) {
        document.querySelector("main").innerHTML = "<h2>No autorizado o proyecto inexistente</h2>";
        return;
    }

    renderSolicitudes(data.solicitudes);
}


// ================================
// Render UI
// ================================
function renderSolicitudes(lista) {
    const main = document.querySelector("main");
    main.innerHTML = "<h1>Solicitudes recibidas</h1>";

    if (lista.length === 0) {
        main.innerHTML += "<p>No hay solicitudes aún.</p>";
        return;
    }

    lista.forEach(sol => {

        const nombre = sol.nombre_artistico ? sol.nombre_artistico : sol.email;

        const div = document.createElement("div");
        div.classList.add("solicitud-item");

        div.innerHTML = `
            <p><strong>${nombre}</strong> (${sol.estado})</p>
            <button class="btn-aceptar">Aceptar</button>
            <button class="btn-rechazar">Rechazar</button>
            <hr>
        `;

        // listeners
        div.querySelector(".btn-aceptar").onclick = () => aceptar(sol.id);
        div.querySelector(".btn-rechazar").onclick = () => rechazar(sol.id);

        main.appendChild(div);
    });
}


// ================================
// Aceptar solicitud
// ================================
async function aceptar(id) {
    const resp = await fetch(`http://localhost:5000/colaboraciones/aceptar/${id}`, {
        method: "POST",
        credentials: "include"
    });
    const data = await resp.json();

    if (data.ok) {
        cargarSolicitudes();
    } else {
        alert("Error al aceptar solicitud");
    }
}

// ================================
// Rechazar solicitud
// ================================
async function rechazar(id) {
    const resp = await fetch(`http://localhost:5000/colaboraciones/rechazar/${id}`, {
        method: "POST",
        credentials: "include"
    });

    const data = await resp.json();

    if (data.ok) {
        cargarSolicitudes();
    } else {
        alert("Error al rechazar solicitud");
    }
}


// Iniciar
cargarSolicitudes();
