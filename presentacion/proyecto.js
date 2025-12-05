// ==========================================================
//   OBTENER ID DEL PROYECTO DESDE LA URL
// ==========================================================
const params = new URLSearchParams(window.location.search);
const proyectoId = params.get("id");

if (!proyectoId) {
    alert("ID de proyecto no encontrado.");
    window.location.href = "home.html";
}

// ==========================================================
//   CARGAR INFO DEL PROYECTO
// ==========================================================
async function cargarProyecto() {
    try {
        const resp = await fetch(`http://localhost:5000/proyectos/${proyectoId}`, {
            credentials: "include"
        });

        const data = await resp.json();

        if (!data.ok) {
            throw new Error("Proyecto no encontrado");
        }

        renderProyecto(data.proyecto);

    } catch (err) {
        console.error("Error cargando proyecto:", err);
        document.getElementById("titulo-proyecto").textContent = "Proyecto no encontrado";
    }
}

// ==========================================================
//   RENDERIZAR PROYECTO
// ==========================================================
function renderProyecto(p) {

    document.getElementById("titulo-proyecto").textContent = p.titulo;
    document.getElementById("descripcion").textContent = p.descripcion;
    document.getElementById("genero").textContent = p.genero;
    document.getElementById("necesita").textContent = p.necesita;

    // FIX AUDIO
    document.getElementById("audio-proyecto").src = 
        `http://localhost:5000/uploads/${p.archivo_audio}`;

    const autorSpan = document.getElementById("autor");
    autorSpan.textContent = p.autor_nombre;
    renderBotonAccion(p);

}


// ==========================================================
//   RENDER DEL BOTÓN SEGÚN SITUACIÓN
// ==========================================================
function renderBotonAccion(p) {

    const cont = document.getElementById("acciones");
    cont.innerHTML = ""; // reseteo

    const boton = document.createElement("button");
    boton.classList.add("btn-accion");

    // Caso 1: soy el dueño
    if (p.es_duenio) {
        boton.textContent = "Ver solicitudes";
        boton.onclick = () => window.location.href = `solicitudes.html?proyecto=${proyectoId}`;
        cont.appendChild(boton);
        return;
    }

    // Caso 2: ya tengo solicitud pendiente
    if (p.solicitud_estado === "pendiente") {
        boton.textContent = "Solicitud enviada ✔";
        boton.disabled = true;
        cont.appendChild(boton);
        return;
    }

    // Caso 3: ya fui aceptado
    if (p.solicitud_estado === "aceptada") {
        boton.textContent = "Entrar a la colaboración";
        boton.onclick = () =>
            window.location.href = `colaboracion.html?id=${p.colaboracion_id}`;
        cont.appendChild(boton);
        return;
    }

    if (p.solicitud_estado === "rechazada") {
        const msg = document.createElement("p");
        msg.textContent = "Tu solicitud fue rechazada ❌ Busca otros proyectos.";
        msg.style.color = "red";
        msg.style.fontWeight = "bold";
        cont.appendChild(msg);
        return;
    }

    // Caso 4: puedo enviar solicitud
    boton.textContent = "Quiero colaborar";
    boton.onclick = enviarSolicitud;

    cont.appendChild(boton);
}

// ==========================================================
//   ENVIAR SOLICITUD DE COLABORACIÓN
// ==========================================================
async function enviarSolicitud() {

    try {
        const resp = await fetch(`http://localhost:5000/proyectos/${proyectoId}/solicitar`, {
            method: "POST",
            credentials: "include"
        });

        if (!resp.ok) {
            if (resp.status === 401) {
                alert("Debes iniciar sesión para colaborar.");
                return window.location.href = "login.html";
            }
            throw new Error("Error al enviar la solicitud.");
        }

        alert("Solicitud enviada correctamente.");
        cargarProyecto(); // refresh del estado

    } catch (err) {
        console.error("Error:", err);
        alert("Ocurrió un error al enviar la solicitud.");
    }
}

// ==========================================================
cargarProyecto();
