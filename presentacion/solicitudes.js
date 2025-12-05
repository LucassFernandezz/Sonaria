// ================================
// Obtener ID del proyecto desde la URL
// ================================
const params = new URLSearchParams(window.location.search);
const proyectoId = params.get("proyecto");

if (!proyectoId) {
    alert("No se especificó un proyecto");
    window.location.href = "home.html";
}


// ================================
// Cargar solicitudes del servidor
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
            <div class="acciones"></div>
            <hr>
        `;

        const acciones = div.querySelector(".acciones");

        // ---------------------------
        // ESTADO PENDIENTE
        // ---------------------------
        if (sol.estado === "pendiente") {
            acciones.innerHTML = `
                <button class="btn-aceptar">Aceptar</button>
                <button class="btn-rechazar">Rechazar</button>
            `;

            acciones.querySelector(".btn-aceptar").onclick = () => aceptar(sol.colaboracion_id);
            acciones.querySelector(".btn-rechazar").onclick = () => rechazar(sol.colaboracion_id);

        }

        // ---------------------------
        // ESTADO ACEPTADO
        // ---------------------------
        if (sol.estado === "aceptada") {

            if (!sol.colaboracion_id) {
                acciones.innerHTML = `<p style="color:red;">Error: falta colaboracion_id</p>`;
            } else {
                acciones.innerHTML = `
                    <button class="btn-entrar">Entrar a la colaboración</button>
                `;

                acciones.querySelector(".btn-entrar").onclick = () => {
                    window.location.href = `colaboracion.html?id=${sol.colaboracion_id}`;
                };
            }
        }

        // ---------------------------
        // ESTADO RECHAZADO
        // ---------------------------
        if (sol.estado === "rechazado") {
            acciones.innerHTML = `<p style="color:red;">Solicitud rechazada</p>`;
        }

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
