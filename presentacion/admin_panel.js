// ========================================
// MOSTRAR SECCIÓN DEL PANEL
// ========================================
function mostrarSeccion(seccion) {
  document.querySelectorAll(".seccion").forEach(s => s.style.display = "none");

  if (seccion === "auditoria") {
    document.getElementById("seccion-auditoria").style.display = "block";
    cargarAuditoria();
  }
  if (seccion === "metricas") {
    document.getElementById("seccion-metricas").style.display = "block";
    cargarMetricas();
  }
  if (seccion === "rectificaciones") {
    document.getElementById("seccion-rectificaciones").style.display = "block";
    cargarRectificaciones();
  }
  if (seccion === "usuarios") {
    document.getElementById("seccion-usuarios").style.display = "block";
    cargarUsuarios();
  }
}



// ========================================
// 1) AUDITORÍA
// ========================================
async function cargarAuditoria() {
  const res = await fetch("/admin/auditoria/");
  const data = await res.json();

  const tbody = document.getElementById("tabla-auditoria");
  tbody.innerHTML = "";

  if (!data.ok) return;

  data.auditoria.forEach(a => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${a.id}</td>
      <td>${a.usuario_email || "N/A"}</td>
      <td>${a.accion}</td>
      <td>${JSON.stringify(a.detalles)}</td>
      <td>${a.fecha}</td>
      <td>${a.ip}</td>
    `;

    tbody.appendChild(tr);
  });
}



// ========================================
// 2) MÉTRICAS
// ========================================
async function cargarMetricas() {
  const res = await fetch("/admin/metricas/");
  const data = await res.json();

  const cont = document.getElementById("contenedor-metricas");
  cont.innerHTML = "";

  if (!data.ok) return;

  data.metricas.forEach(m => {
    const div = document.createElement("div");
    div.classList.add("bloque-metrica");

    div.innerHTML = `
      <h3>${m.tipo}</h3>
      <pre>${m.valor}</pre>
      <p><b>Fecha:</b> ${m.fecha_calculo}</p>
    `;

    cont.appendChild(div);
  });
}

async function recalcularMetricas() {
  const res = await fetch("/admin/metricas/recalcular", { method: "POST" });
  const data = await res.json();
  alert(data.mensaje || "OK");
  cargarMetricas();
}



// ========================================
// 3) RECTIFICACIONES
// ========================================
async function cargarRectificaciones() {
  const res = await fetch("/admin/rectificaciones/");
  const data = await res.json();

  const tbody = document.getElementById("tabla-rectificaciones");
  tbody.innerHTML = "";

  if (!data.ok) return;

  data.rectificaciones.forEach(r => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${r.id}</td>
      <td>${r.email}</td>
      <td>${r.campo}</td>
      <td>${r.valor_anterior || "-"}</td>
      <td>${r.valor_nuevo || "-"}</td>
      <td>${r.estado}</td>
      <td>
        <button onclick="aprobarRect(${r.id})">Aprobar</button>
        <button onclick="rechazarRect(${r.id})">Rechazar</button>
      </td>
    `;

    tbody.appendChild(tr);
  });
}

async function aprobarRect(id) {
  if (!confirm("¿Aprobar la rectificación?")) return;

  const res = await fetch(`/admin/rectificaciones/aprobar/${id}`, { method: "POST" });
  const data = await res.json();
  alert(data.mensaje);
  cargarRectificaciones();
}

async function rechazarRect(id) {
  if (!confirm("¿Rechazar la rectificación?")) return;

  const res = await fetch(`/admin/rectificaciones/rechazar/${id}`, { method: "POST" });
  const data = await res.json();
  alert(data.mensaje);
  cargarRectificaciones();
}


// ========================================
// 4) USUARIOS
// ========================================
async function cargarUsuarios() {
  const res = await fetch("/admin/usuarios/");
  const data = await res.json();

  const tbody = document.getElementById("tabla-usuarios");
  tbody.innerHTML = "";

  if (!data.ok) return;

  data.usuarios.forEach(u => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${u.id}</td>
      <td>${u.email}</td>
      <td>${u.rol}</td>
      <td>${u.estado}</td>
      <td>
        <button onclick="verInfo(${u.id})">Ver</button>
        <button onclick="bloquearUsuario(${u.id})">Bloquear/Activar</button>
        <button onclick="resetPass(${u.id})">Reset Pass</button>
        <button onclick="cambiarRol(${u.id})">Cambiar Rol</button>
      </td>
    `;

    tbody.appendChild(tr);
  });
}


// === VER DETALLE ===
async function verInfo(id) {
  const res = await fetch(`/admin/usuarios/info/${id}`);

  if (res.status === 404) {
    alert("Usuario no encontrado");
    return;
  }

  const data = await res.json();
  alert(JSON.stringify(data.usuario, null, 2));
}



// === BLOQUEAR ===
async function bloquearUsuario(id) {

  const opcion = confirm("¿Deseas BLOQUEAR a este usuario?\n\nPresiona Cancelar para ACTIVARLO.");

  const nuevoEstado = opcion ? "bloqueado" : "activo";

  const res = await fetch(`/admin/usuarios/bloquear/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ estado: nuevoEstado })
  });

  const data = await res.json();
  alert(data.mensaje || "OK");

  cargarUsuarios();
}



// === ELIMINAR (AÚN NO IMPLEMENTADO EN TU BACKEND) ===
async function eliminarUsuario(id) {
  alert("⚠ Esta función aún no está implementada en tu backend.");
}



// === RESET PASS ===
async function resetPass(id) {
  const nueva = prompt("Nueva contraseña:");

  if (!nueva) return;

  const res = await fetch(`/admin/usuarios/reset_pass/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nueva })
  });

  const data = await res.json();
  alert(data.mensaje);
}



// === CAMBIAR ROL ===
async function cambiarRol(id) {
  const nuevo = prompt("Nuevo rol: (admin / registrado / visitante");

  if (!nuevo) return;

  const res = await fetch(`/admin/usuarios/cambiar_rol/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rol: nuevo })
  });

  const data = await res.json();
  
  alert(data.mensaje);
  cargarUsuarios();
  
  // avisamos a todos los tabs del usuario bloqueado para que cierre sesión
  if (data.forzar_logout) {
    localStorage.setItem("logout_forzado", Date.now());
  }
}
