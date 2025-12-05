// =======================
// Verificar login
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
// Evento de envío
// =======================
document.getElementById("form-subida").addEventListener("submit", async (e) => {
    e.preventDefault();

    const titulo = document.getElementById("titulo").value.trim();
    const descripcion = document.getElementById("descripcion").value.trim();
    const genero = document.getElementById("genero").value;
    const necesita = document.getElementById("necesita").value;
    const archivo = document.getElementById("archivo_audio").files[0];

    if (!archivo) {
        alert("Debe seleccionar un archivo de audio.");
        return;
    }

    // Crear form-data
    const formData = new FormData();
    formData.append("titulo", titulo);
    formData.append("descripcion", descripcion);
    formData.append("genero", genero);
    formData.append("necesita", necesita);
    formData.append("archivo_audio", archivo);

    const resp = await fetch("http://localhost:5000/proyectos", {
        method: "POST",
        credentials: "include",
        body: formData
    });

    const data = await resp.json();

    if (data.ok) {
        alert("Audio subido correctamente");
        window.location.href = "home.html";
    } else {
        alert("Error: " + data.error);
    }
});
