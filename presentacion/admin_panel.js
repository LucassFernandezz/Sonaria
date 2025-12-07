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

  const contenedor = document.getElementById("contenedor-metricas");
  contenedor.innerHTML = "";

  if (!data.ok) return;

  data.metricas.forEach(m => {
    const div = document.createElement("div");
    div.classList.add("bloque-metrica");

    div.innerHTML = `
      <h3>${m.tipo}</h3>
      <pre>${m.valor}</pre>
      <p><b>Fecha:</b> ${m.fecha_calculo}</p>
    `;

    contenedor.appendChild(div);
  });
}


// Recalcular métricas
async function recalcularMetricas() {
  const res = await fetch("/admin/metricas/recalcular", {
    method: "POST"
  });

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
  const res = await fetch(`/admin/rectificaciones/aprobar/${id}`, {
    method: "POST"
  });

  const data = await res.json();
  alert(data.mensaje || "OK");

  cargarRectificaciones();
}

async function rechazarRect(id) {
  const res = await fetch(`/admin/rectificaciones/rechazar/${id}`, {
    method: "POST"
  });

  const data = await res.json();
  alert(data.mensaje || "OK");

  cargarRectificaciones();
}
