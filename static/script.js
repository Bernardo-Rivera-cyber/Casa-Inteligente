// =========================
// SONIDOS RETRO
// =========================
const reproducirSonidoRetro = (tipoSonido) => {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        const t = ctx.currentTime;

        if (tipoSonido === 'click') {
            osc.type = 'square';
            osc.frequency.setValueAtTime(400, t);
            osc.frequency.exponentialRampToValueAtTime(120, t + 0.08);
            gain.gain.setValueAtTime(0.15, t);
            gain.gain.linearRampToValueAtTime(0.01, t + 0.08);
            osc.start(); osc.stop(t + 0.08);
        } else if (tipoSonido === 'pop') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(300, t);
            osc.frequency.exponentialRampToValueAtTime(800, t + 0.12);
            gain.gain.setValueAtTime(0.2, t);
            gain.gain.linearRampToValueAtTime(0.01, t + 0.12);
            osc.start(); osc.stop(t + 0.12);
        }
    } catch (e) { console.warn(e); }
};

// =========================
// CONTROL DE VISTAS Y LOGIN
// =========================
let intervaloLogin = null;

function verificarSesion() {
    fetch('/api/auth_status')
    .then(res => res.json())
    .then(data => {
        if (data.authenticated) {
            document.getElementById('login-view').style.display = 'none';
            document.getElementById('assistant-view').style.display = 'flex';
            iniciarEscucha();
        } else {
            document.getElementById('login-view').style.display = 'flex';
            document.getElementById('assistant-view').style.display = 'none';
        }
    });
}

function iniciarFaceID() {
    reproducirSonidoRetro('pop');
    document.getElementById('login-status').textContent = "Abriendo cámara...";
    document.getElementById('login-status').style.color = "#94a3b8";
    
    fetch('/api/face_login', { method: 'POST' })
    .then(r => r.json()).then(d => {
        if (d.status === 'ok') {
            document.getElementById('login-status').textContent = "Buscando rostro...";
            
            if (intervaloLogin) clearInterval(intervaloLogin);
            
            intervaloLogin = setInterval(() => {
                fetch('/api/auth_status')
                .then(res => res.json())
                .then(auth => {
                    if (auth.authenticated) {
                        clearInterval(intervaloLogin);
                        verificarSesion();
                    }
                });
            }, 1000);

            setTimeout(() => {
                if (intervaloLogin) {
                    clearInterval(intervaloLogin);
                    document.getElementById('login-status').textContent = "Acceso Denegado o Tiempo agotado.";
                    document.getElementById('login-status').style.color = "#ef4444";
                }
            }, 20000);
        }
    });
}

// =========================
// REGISTRO DE NUEVO ROSTRO (desde el asistente)
// =========================
function registrarNuevoRostro() {
    reproducirSonidoRetro('pop');

    const input = document.getElementById('nuevo-nombre');
    const status = document.getElementById('admin-status');
    if (!input || !status) return;

    const nombre = input.value.trim();
    if (!nombre) {
        status.textContent = "❌ Escribe un nombre válido.";
        status.style.color = "#ef4444";
        return;
    }

    // Pausar la escucha mientras se capturan fotos
    escuchaActiva = false;

    status.textContent = "Abriendo cámara para capturar fotos...";
    status.style.color = "#facc15";

    fetch('/api/add_face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: nombre })
    })
    .then(r => r.json())
    .then(d => {
        status.textContent = d.mensaje;
        status.style.color = d.status === "ok" ? "#22c55e" : "#ef4444";
        input.value = "";
    })
    .catch(() => {
        status.textContent = "Error al conectar con el servidor.";
        status.style.color = "#ef4444";
    })
    .finally(() => {
        // Reanudar la escucha después de un momento
        setTimeout(() => {
            escuchaActiva = true;
            bucleEscucha();
        }, 2000);
    });
}

function entrenarModelo() {
    reproducirSonidoRetro('pop');
    const status = document.getElementById('admin-status');
    if (!status) return;

    status.textContent = "Entrenando modelo...";
    status.style.color = "#facc15";

    fetch('/api/entrenar', { method: 'POST' })
    .then(r => r.json())
    .then(d => {
        status.textContent = d.mensaje;
        status.style.color = d.status === "ok" ? "#22c55e" : "#ef4444";
    })
    .catch(() => {
        status.textContent = "Error al conectar con el servidor.";
        status.style.color = "#ef4444";
    });
}

function cerrarSesion() {
    reproducirSonidoRetro('close');
    escuchaActiva = false; // detener la escucha al cerrar sesión
    fetch('/api/logout', { method: 'POST' }).then(() => verificarSesion());
}

// =========================
// CONTROL DE LA CASA
// =========================
function controlarGaraje(abrir) {
    reproducirSonidoRetro('click');
    const accion = abrir ? 'abrir_garaje' : 'cerrar_garaje';
    fetch('/api/house', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accion: accion })
    }).then(r => r.json()).then(d => {
        if (d.status === 'ok' && d.mensaje) {
            mostrarRespuestaEnBarra(d.mensaje);
        }
    });
}

function controlarCasa(accion) {
    reproducirSonidoRetro('click');
    fetch('/api/house', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accion: accion })
    }).then(r => r.json()).then(d => {
        if (d.status === 'ok' && d.mensaje) {
            mostrarRespuestaEnBarra(d.mensaje);
        }
    });
}

function controlarHab(habitacion, encender) {
    reproducirSonidoRetro('click');
    const accion = encender ? 'encender_habitacion' : 'apagar_habitacion';
    fetch('/api/house', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accion: accion, habitacion: habitacion })
    }).then(r => r.json()).then(d => {
        if (d.status === 'ok' && d.mensaje) {
            mostrarRespuestaEnBarra(d.mensaje);
        }
    });
}

// =========================
// MOSTRAR RESPUESTA EN LA BARRA
// =========================
let timeoutBarra = null;

function mostrarRespuestaEnBarra(mensaje, color = "#38bdf8") {
    const etiqueta = document.getElementById('listening-text');
    if (!etiqueta) return;
    
    etiqueta.textContent = `Steve: ${mensaje}`;
    etiqueta.style.color = color; 
    
    clearTimeout(timeoutBarra);
    timeoutBarra = setTimeout(() => {
        etiqueta.textContent = "Escuchando...";
        etiqueta.style.color = "#38bdf8";
    }, 5000);
}

// =========================
// SUB-PANELES (Apps)
// =========================
async function cargarApps() {
    try {
        const res = await fetch('/api/apps');
        const datos = await res.json();
        const panel = document.getElementById('apps-panel');
        if (!panel) return;
        panel.innerHTML = '';
        datos.apps.forEach(app => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'boton-app';
            btn.textContent = app.charAt(0).toUpperCase() + app.slice(1);
            btn.onclick = () => ejecutarApp(app);
            panel.appendChild(btn);
        });
    } catch (e) { console.warn(e); }
}

function togglePanel(id) {
    reproducirSonidoRetro('click');
    const paneles = document.querySelectorAll('.sub-panel');
    paneles.forEach(p => {
        if (p.id === id) {
            p.classList.toggle('visible');
        } else {
            p.classList.remove('visible');
        }
    });
}

function ejecutarApp(nombre) {
    reproducirSonidoRetro('pop');
    document.getElementById('apps-panel').classList.remove('visible');
    fetch('/api/accion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accion: 'abrir_app', app: nombre })
    }).then(r => r.json()).then(d => {
        if (d.status === 'ok' && d.mensaje) {
            mostrarRespuestaEnBarra(d.mensaje);
        }
    }).catch(e => console.warn(e));
}

// =========================
// ACCIONES GENERALES
// =========================
function ejecutarAccion(nombreAccion) {
    reproducirSonidoRetro('pop');
    const etiqueta = document.getElementById('listening-text');
    if (etiqueta) etiqueta.textContent = "Procesando...";

    fetch('/api/accion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accion: nombreAccion })
    }).then(r => r.json()).then(d => {
        if (d.status === 'ok' && d.mensaje) {
            mostrarRespuestaEnBarra(d.mensaje);
        }
    }).catch(e => {
        console.error(e);
        mostrarRespuestaEnBarra("Error de comunicación.");
    });
}

function enviarComandoTexto() {
    const input = document.getElementById('text-input');
    if (!input) return;
    const texto = input.value.trim();
    if (!texto) {
        reproducirSonidoRetro('click');
        return;
    }
    reproducirSonidoRetro('pop');
    const etiqueta = document.getElementById('listening-text');
    if (etiqueta) etiqueta.textContent = "Procesando...";

    fetch('/api/texto', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto })
    }).then(r => r.json()).then(d => {
        if (d.status === 'ok') {
            mostrarRespuestaEnBarra(d.mensaje);
            input.value = '';
        }
    }).catch(e => console.error(e));
}

function manejarTeclaTexto(event) {
    if (event.key === 'Enter') { event.preventDefault(); enviarComandoTexto(); }
}

// =========================
// ESCUCHA CONTINUA
// =========================
let escuchaActiva = false;
let enProceso = false;

function iniciarEscucha() {
    if (escuchaActiva) return;
    escuchaActiva = true;
    bucleEscucha();
}

async function bucleEscucha() {
    if (!escuchaActiva) return;
    if (enProceso) { setTimeout(bucleEscucha, 200); return; }

    enProceso = true;
    const etiqueta = document.getElementById('listening-text');
    
    if (etiqueta && !etiqueta.textContent.includes("Steve:")) {
        etiqueta.textContent = "Escuchando...";
    }

    try {
        const res = await fetch('/api/voz', { method: 'POST' });
        const datos = await res.json();
        
        if (datos.status === 'ok' && datos.escuchado) {
            mostrarRespuestaEnBarra(datos.mensaje);
        }
    } catch (e) {
        console.warn("Reconectando escucha...");
    } finally {
        enProceso = false;
        const tiempoEspera = (typeof datos !== 'undefined' && datos.escuchado) ? 3000 : 500;
        if (escuchaActiva) setTimeout(bucleEscucha, tiempoEspera); 
    }
}

// =========================
// BURBUJAS (Fondo)
// =========================
function generarBurbujasFondo() {
    const cont = document.getElementById('bubbles-container');
    if (!cont) return;
    for (let i = 0; i < 14; i++) {
        const b = document.createElement('div');
        b.className = 'bubble';
        const tam = Math.random() * 18 + 8;
        b.style.width = `${tam}px`;
        b.style.height = `${tam}px`;
        b.style.left = `${Math.random() * 100}%`;
        b.style.animationDuration = `${Math.random() * 6 + 6}s`;
        b.style.animationDelay = `${Math.random() * 5}s`;
        cont.appendChild(b);
    }
}

// =========================
// INICIO
// =========================
document.addEventListener('DOMContentLoaded', () => {
    generarBurbujasFondo();
    fetch('/api/reset_auth', { method: 'POST' }).then(() => {
        cargarApps();
        verificarSesion();
    });
});