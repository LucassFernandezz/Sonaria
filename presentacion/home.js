document.addEventListener("DOMContentLoaded", () => {
    cargarAudios();
});

async function cargarAudios() {
    const contenedor = document.getElementById("contenedor-audios");
    contenedor.innerHTML = "<p>Cargando audios...</p>";

    try {
        const resp = await fetch("http://localhost:5000/proyectos/all", {
            credentials: "include"
        });

        const data = await resp.json();

        if (!data.ok) {
            contenedor.innerHTML = "<p>Error al cargar audios.</p>";
            return;
        }

        const audios = data.audios;

        if (audios.length === 0) {
            contenedor.innerHTML = "<p>No hay audios subidos todavía.</p>";
            return;
        }

        contenedor.innerHTML = "";

        audios.forEach(audio => {
            const card = document.createElement("div");
            card.classList.add("tarjeta-audio");

            card.dataset.id = audio.id;

            card.innerHTML = `
                <h3>${audio.titulo}</h3>
                <p>${audio.descripcion || ""}</p>

                <audio controls>
                    <source src="http://localhost:5000/uploads/${audio.archivo_audio}" type="audio/mpeg">
                    Tu navegador no soporta audio.
                </audio>

                <div class="meta-row">
                    <small class="autor">Subido por: ${audio.nombre_artistico && !audio.nombre_artistico.startsWith("gAAAAA") 
                        ? audio.nombre_artistico 
                        : audio.email}
                    </small>
                    <small><strong>Se necesita:</strong> ${audio.necesita || "—"}</small>
                </div>
            `;

            card.style.cursor = "pointer"; // opcional, mejora UX

            card.addEventListener("click", () => {
                window.location.href = `proyecto.html?id=${audio.id}`;
            });


            contenedor.appendChild(card);
        });

    } catch (err) {
        console.error(err);
        contenedor.innerHTML = "<p>Error de conexión.</p>";
    }
}
