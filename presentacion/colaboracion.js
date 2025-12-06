// colaboracion.js
// Maneja la vista de una colaboración (reproducir, descargar, subir takes)

const params = new URLSearchParams(window.location.search);
const colabId = params.get("id") || params.get("colaboracion") || params.get("proyecto"); 
// Algunos links usan ?id=..., otros ?proyecto=..; aceptamos varias variantes.
if (!colabId) {
    alert("ID de colaboración no especificado.");
    window.location.href = "home.html";
}

const API_BASE = "http://localhost:5000";

const el = {
    mensaje: document.getElementById("mensaje"),
    titulo: document.getElementById("titulo-proyecto"),
    dueno: document.getElementById("dueno"),
    colaborador: document.getElementById("colaborador"),
    estado: document.getElementById("estado"),
    audioOriginalPlayer: document.getElementById("audio-original-player"),
    listaTakes: document.getElementById("lista-takes"),
    subirBlock: document.getElementById("subir-block"),
    formSubir: document.getElementById("form-subir"),
    archivoInput: document.getElementById("archivo"),
    comentarioInput: document.getElementById("comentario"),
    btnSubir: document.getElementById("btn-subir"),
    btnCancelar: document.getElementById("btn-cancelar")
};

let detalle = null; // guardamos el JSON de /detalle
let takes = [];     // lista de takes

// Helper: mostrar mensaje breve
function mostrarMensaje(text, tipo = "info", timeout = 4000) {
    el.mensaje.textContent = text;
    el.mensaje.style.color = tipo === "error" ? "crimson" : (tipo === "success" ? "green" : "black");
    if (timeout) setTimeout(() => { if (el.mensaje.textContent === text) el.mensaje.textContent = ""; }, timeout);
}

// Cargar detalle (usa /colaboraciones/detalle/<id>)
async function cargarDetalle() {
    try {
        const resp = await fetch(`${API_BASE}/colaboraciones/detalle/${colabId}`, {
            credentials: "include"
        });
        if (!resp.ok) {
            const data = await resp.json().catch(()=>({}));
            if (resp.status === 401) {
                mostrarMensaje("Debes iniciar sesión para ver la colaboración.", "error", 6000);
                return window.location.href = "login.html";
            }
            mostrarMensaje(data.error || "No se pudo cargar la colaboración.", "error", 5000);
            return;
        }
        const data = await resp.json();
        detalle = data.colaboracion;
        takes = data.takes || [];
        renderDetalle();
        renderTimeline();
        configurarAccesoSubida();
    } catch (err) {
        console.error("Error cargarDetalle:", err);
        mostrarMensaje("Error de conexión al servidor.", "error", 5000);
    }
}

// Cargar sólo takes (usa /colaboraciones/takes/<id>) — útil para refrescar después de subir
async function refrescarTakes() {
    try {
        const resp = await fetch(`${API_BASE}/colaboraciones/takes/${colabId}`, { credentials: "include" });
        if (!resp.ok) { console.error("Error al pedir takes", resp.status); return; }
        const data = await resp.json();
        takes = data.takes || [];
        renderTimeline();
    } catch (err) {
        console.error("Error refrescarTakes:", err);
    }
}

// Render del bloque de detalle (titulo, participantes, audio original)
function renderDetalle() {
    el.titulo.textContent = detalle.titulo || "Proyecto sin título";
    el.dueno.textContent = detalle.dueno_artistico || detalle.dueno_email || "Desconocido";
    el.colaborador.textContent = detalle.colaborador_artistico || detalle.colaborador_email || "Desconocido";
    el.estado.textContent = detalle.estado || "—";

    // audio original
    el.audioOriginalPlayer.innerHTML = "";
    if (detalle.audio_original) {
        const audioWrap = document.createElement("div");
        audioWrap.style.display = "flex";
        audioWrap.style.flexDirection = "column";
        audioWrap.style.gap = "6px";

        const audioEl = document.createElement("audio");
        audioEl.controls = true;
        audioEl.src = `${API_BASE}/uploads/${detalle.audio_original}`;
        audioEl.setAttribute("preload", "metadata");
        audioEl.style.width = "100%";

        const btnRow = document.createElement("div");
        btnRow.style.marginTop = "6px";
        // descargar
        const aDownload = document.createElement("a");
        aDownload.href = `${API_BASE}/uploads/${detalle.audio_original}`;
        aDownload.download = detalle.audio_original;
        aDownload.textContent = "Descargar audio original";
        aDownload.className = "btn-accion";
        aDownload.style.marginRight = "8px";

        btnRow.appendChild(aDownload);

        audioWrap.appendChild(audioEl);
        audioWrap.appendChild(btnRow);

        el.audioOriginalPlayer.appendChild(audioWrap);
    } else {
        el.audioOriginalPlayer.innerHTML = "<p>No hay audio original disponible.</p>";
    }
}

// Render de la timeline: arriba el primero (original) y luego los takes en orden cronológico ascendente
function renderTimeline() {
    el.listaTakes.innerHTML = "";

    // Si no hay takes, mostramos un texto
    if (!takes || takes.length === 0) {
        el.listaTakes.innerHTML = "<p>No hay audios colaborativos todavía. Sé el primero en subir uno.</p>";
        return;
    }

    // Mostramos cada take (ordenado asc por fecha_subida)
    // tus endpoints ya devuelven orden asc, pero nos aseguramos:
    takes.sort((a,b) => new Date(a.fecha_subida) - new Date(b.fecha_subida));

    takes.forEach(t => {
        const wrap = document.createElement("div");
        wrap.style.background = "#fff";
        wrap.style.border = "1px solid #eee";
        wrap.style.padding = "12px";
        wrap.style.borderRadius = "10px";
        wrap.style.marginBottom = "10px";

        const meta = document.createElement("div");
        meta.style.display = "flex";
        meta.style.justifyContent = "space-between";
        meta.style.alignItems = "center";
        meta.style.marginBottom = "8px";

        const left = document.createElement("div");
        left.innerHTML = `<strong>Take #${t.id}</strong> <small style="color:#666;margin-left:8px;">${formatFecha(t.fecha_subida)}</small>`;

        const right = document.createElement("div");
        // download
        const a = document.createElement("a");
        a.href = `${API_BASE}/uploads/${t.archivo_audio}`;
        a.download = t.archivo_audio;
        a.textContent = "Descargar";
        a.className = "btn-accion";
        a.style.marginLeft = "8px";

        right.appendChild(a);

        meta.appendChild(left);
        meta.appendChild(right);

        const audioEl = document.createElement("audio");
        audioEl.controls = true;
        audioEl.src = `${API_BASE}/uploads/${t.archivo_audio}`;
        audioEl.style.width = "100%";
        audioEl.setAttribute("preload", "metadata");

        const comentario = document.createElement("div");
        comentario.style.marginTop = "8px";
        comentario.style.color = "#333";
        comentario.textContent = t.comentarios ? `Comentario: ${t.comentarios}` : "";

        wrap.appendChild(meta);
        wrap.appendChild(audioEl);
        wrap.appendChild(comentario);

        el.listaTakes.appendChild(wrap);
    });
}

// Formulario subida
async function handleSubir(ev) {
    ev.preventDefault();

    const file = el.archivoInput.files[0];
    if (!file) {
        mostrarMensaje("Seleccioná un archivo de audio antes de subir.", "error");
        return;
    }

    // FormData
    const fd = new FormData();
    fd.append("archivo", file);
    fd.append("comentario", el.comentarioInput.value || "");

    el.btnSubir.disabled = true;
    mostrarMensaje("Subiendo take...", "info");

    try {
        const resp = await fetch(`${API_BASE}/colaboraciones/subir_take/${colabId}`, {
            method: "POST",
            credentials: "include",
            body: fd
        });

        const data = await resp.json().catch(()=>({ok:false}));

        if (!resp.ok || !data.ok) {
            if (resp.status === 401) {
                mostrarMensaje("Debes iniciar sesión.", "error", 5000);
                return window.location.href = "login.html";
            }
            mostrarMensaje(data.error || "Ocurrió un error al subir el take.", "error", 6000);
            console.error("Respuesta subir:", resp.status, data);
            return;
        }

        mostrarMensaje("Take subido correctamente.", "success", 4000);
        el.formSubir.reset();
        await refrescarTakes();
    } catch (err) {
        console.error("Error subir:", err);
        mostrarMensaje("Error de conexión al subir archivo.", "error", 5000);
    } finally {
        el.btnSubir.disabled = false;
    }
}

function handleCancelar() {
    el.formSubir.reset();
}

// Determina si el usuario actual es parte de esta colaboración (dueño o colaborador)
// y muestra el bloque de subida si corresponde.
function configurarAccesoSubida() {
    // Para comprobar el usuario actual pedimos /auth/me (ya lo usás en otras páginas).
    fetch(`${API_BASE}/auth/me`, { credentials: "include" })
        .then(r => r.json())
        .then(data => {
            if (!data.autenticado) {
                // no mostrar formulario
                el.subirBlock.style.display = "none";
                return;
            }
            const uid = data.usuario_id;
            const esDueno = uid === detalle.dueno_id;
            const esColab = uid === detalle.colaborador_id;

            if (esDueno || esColab) {
                el.subirBlock.style.display = "block";
            } else {
                el.subirBlock.style.display = "none";
            }
        })
        .catch(err => {
            console.error("Error auth/me", err);
            el.subirBlock.style.display = "none";
        });
}

// utility: formato fecha legible
function formatFecha(iso) {
    if (!iso) return "";
    try {
        const d = new Date(iso);
        return d.toLocaleString();
    } catch (e) {
        return iso;
    }
}

// Iniciar
el.formSubir && el.formSubir.addEventListener("submit", handleSubir);
el.btnCancelar && el.btnCancelar.addEventListener("click", handleCancelar);

// Carga inicial
cargarDetalle();
