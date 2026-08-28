from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
import os

app = FastAPI()

GEMINI_KEY = os.getenv("GEMINI_KEY")
client_gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>J.A.R.V.I.S. HUD</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { 
                background: #020617; 
                color: #38bdf8; 
                font-family: 'Segoe UI', monospace; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                justify-content: center; 
                min-height: 100vh; 
                overflow-x: hidden;
                padding: 20px;
            }

            /* Dashboard HUD */
            .hud-grid {
                display: flex;
                gap: 15px;
                margin-bottom: 25px;
                flex-wrap: wrap;
                justify-content: center;
                width: 100%;
                max-width: 800px;
            }

            .hud-card {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 12px;
                padding: 12px 20px;
                text-align: center;
                min-width: 160px;
                backdrop-filter: blur(8px);
                box-shadow: 0 0 15px rgba(56, 189, 248, 0.1);
                transition: all 0.3s ease;
            }
            .hud-card:hover {
                border-color: #38bdf8;
                box-shadow: 0 0 20px rgba(56, 189, 248, 0.3);
            }
            .hud-label {
                font-size: 0.7rem;
                color: #64748b;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }
            .hud-value {
                font-size: 1.2rem;
                font-weight: bold;
                color: #38bdf8;
                margin-top: 4px;
            }

            /* Widget Central */
            .jarvis-widget {
                position: relative;
                width: 240px;
                height: 240px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .reactor-ring {
                position: absolute;
                border-radius: 50%;
                border: 2px dashed rgba(56, 189, 248, 0.3);
            }
            .ring-1 { width: 230px; height: 230px; animation: spin 20s linear infinite; }
            .ring-2 { width: 180px; height: 180px; border: 2px solid rgba(56, 189, 248, 0.5); border-top-color: transparent; animation: spinRev 10s linear infinite; }

            .orb {
                width: 110px;
                height: 110px;
                border-radius: 50%;
                background: radial-gradient(circle, #38bdf8 0%, #0284c7 60%, #0f172a 100%);
                box-shadow: 0 0 50px rgba(56, 189, 248, 0.4);
                animation: float 3.5s ease-in-out infinite;
                transition: all 0.4s ease;
                z-index: 5;
            }
            .orb.off { background: radial-gradient(circle, #334155 0%, #0f172a 100%); box-shadow: none; }
            .orb.speaking { animation: float 1.5s ease-in-out infinite, pulse 0.3s ease-in-out infinite alternate; box-shadow: 0 0 80px #38bdf8; }
            .orb.listening { background: radial-gradient(circle, #f43f5e 0%, #be123c 100%); box-shadow: 0 0 60px #f43f5e; }

            @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
            @keyframes pulse { 0% { transform: scale(0.95); } 100% { transform: scale(1.1); } }
            @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            @keyframes spinRev { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }

            .status-display {
                margin-top: 20px;
                font-size: 0.8rem;
                letter-spacing: 2px;
                color: #94a3b8;
                text-align: center;
            }

            .response-text {
                margin-top: 15px;
                max-width: 500px;
                text-align: center;
                font-size: 0.95rem;
                color: #e0f2fe;
                min-height: 45px;
                line-height: 1.4;
            }

            .btn-start {
                margin-top: 20px;
                background: transparent;
                border: 1px solid #38bdf8;
                color: #38bdf8;
                padding: 10px 24px;
                border-radius: 20px;
                cursor: pointer;
                letter-spacing: 1px;
                transition: 0.3s;
            }
            .btn-start:hover { background: #38bdf8; color: #020617; box-shadow: 0 0 15px #38bdf8; }
        </style>
    </head>
    <body>

        <!-- PANELES DE INFORMACIÓN HUD -->
        <div class="hud-grid">
            <div class="hud-card">
                <div class="hud-label">SISTEMA / HORA</div>
                <div id="valHora" class="hud-value">--:--:--</div>
            </div>
            <div class="hud-card">
                <div class="hud-label">USD / HNL</div>
                <div id="valDolar" class="hud-value">L. 25.40</div>
            </div>
            <div class="hud-card">
                <div class="hud-label">ESTADO CLIMA</div>
                <div id="valClima" class="hud-value">28°C HND</div>
            </div>
        </div>

        <div class="jarvis-widget">
            <div class="reactor-ring ring-1"></div>
            <div class="reactor-ring ring-2"></div>
            <div id="orb" class="orb off"></div>
        </div>

        <div id="statusText" class="status-display">SISTEMA OFFLINE</div>
        <div id="responseText" class="response-text">Inicie el enlace para sincronizar módulos.</div>

        <button id="btnPower" class="btn-start" onclick="iniciarSistema()">CONECTAR SISTEMA</button>

        <script>
            let audioCtx, analyser, micStream;
            let sistemaConectado = false;
            let jarvisEncendido = false;
            let reconocedorVoz;
            let estaHablando = false;
            let ultimoPico = 0;

            function actualizarReloj() {
                const ahora = new Date();
                document.getElementById('valHora').innerText = ahora.toLocaleTimeString();
            }
            setInterval(actualizarReloj, 1000);
            actualizarReloj();

            async function iniciarSistema() {
                if (sistemaConectado) return;

                try {
                    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    analyser = audioCtx.createAnalyser();
                    
                    const source = audioCtx.createMediaStreamSource(micStream);
                    analyser.fftSize = 256;
                    source.connect(analyser);

                    sistemaConectado = true;
                    document.getElementById('btnPower').style.display = 'none';
                    document.getElementById('statusText').innerText = "EN ESPERA | DI 'HOLA JARVIS' O APLAUDE";
                    document.getElementById('responseText').innerText = "Escuchando voz y sensores...";

                    iniciarSensorAplausos();
                    iniciarReconocimientoVoz();
                } catch (err) {
                    alert("Se requieren permisos de micrófono para operar.");
                }
            }

            function iniciarSensorAplausos() {
                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);

                function medir() {
                    if (sistemaConectado && !jarvisEncendido && !estaHablando) {
                        analyser.getByteFrequencyData(dataArray);
                        let suma = 0;
                        for (let i = 0; i < bufferLength; i++) suma += dataArray[i];
                        let promedio = suma / bufferLength;

                        if (promedio > 85) {
                            let ahora = Date.now();
                            if (ahora - ultimoPico < 600 && ahora - ultimoPico > 150) {
                                encenderJarvis();
                            }
                            ultimoPico = ahora;
                        }
                    }
                    requestAnimationFrame(medir);
                }
                medir();
            }

            function encenderJarvis() {
                if (jarvisEncendido) return;
                jarvisEncendido = true;
                document.getElementById('orb').className = "orb";
                document.getElementById('statusText').innerText = "JARVIS ONLINE | TE ESCUCHO";
                hablar("A su servicio, señor. ¿En qué le puedo asistir?");
            }

            function apagarJarvis() {
                jarvisEncendido = false;
                document.getElementById('orb').className = "orb off";
                document.getElementById('statusText').innerText = "MODO ESPERA | DI 'HOLA JARVIS' O APLAUDE";
                document.getElementById('responseText').innerText = "Sistemas en reposo.";
            }

            function hablar(texto) {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    const utt = new SpeechSynthesisUtterance(texto);
                    utt.lang = 'es-ES';
                    utt.rate = 1.0;
                    utt.pitch = 0.8;

                    utt.onstart = () => {
                        estaHablando = true;
                        document.getElementById('orb').className = "orb speaking";
                    };

                    utt.onend = () => {
                        estaHablando = false;
                        if (jarvisEncendido) {
                            document.getElementById('orb').className = "orb";
                            document.getElementById('statusText').innerText = "JARVIS ONLINE | ESCUCHANDO";
                        } else {
                            apagarJarvis();
                        }
                    };

                    window.speechSynthesis.speak(utt);
                }
            }

            function iniciarReconocimientoVoz() {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    document.getElementById('responseText').innerText = "Navegador no compatible. Use Google Chrome.";
                    return;
                }

                reconocedorVoz = new SpeechRecognition();
                reconocedorVoz.continuous = true;
                reconocedorVoz.lang = 'es-ES';
                reconocedorVoz.interimResults = false;

                reconocedorVoz.onresult = async (event) => {
                    if (estaHablando) return;

                    const index = event.results.length - 1;
                    const comando = event.results[index][0].transcript.trim().toLowerCase();

                    if (!jarvisEncendido) {
                        if (comando.includes("hola jarvis") || comando.includes("jarvis") || comando.includes("despierta") || comando.includes("actívate") || comando.includes("activate")) {
                            encenderJarvis();
                        }
                        return;
                    }

                    if (comando.includes("apágate") || comando.includes("apagate") || comando.includes("descansa") || comando.includes("desactívate")) {
                        hablar("Desactivando interfaz. Hasta luego, señor.");
                        jarvisEncendido = false;
                        return;
                    }

                    document.getElementById('responseText').innerText = '"' + comando + '"';
                    document.getElementById('orb').className = "orb listening";
                    document.getElementById('statusText').innerText = "PROCESANDO...";

                    try {
                        const res = await fetch("/procesar", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ texto: comando })
                        });
                        const data = await res.json();
                        
                        document.getElementById('responseText').innerText = data.respuesta;
                        hablar(data.respuesta);
                    } catch (e) {
                        document.getElementById('statusText').innerText = "ERROR DE CONEXIÓN";
                    }
                };

                reconocedorVoz.onend = () => {
                    if (sistemaConectado) {
                        try { reconocedorVoz.start(); } catch(e){}
                    }
                };

                reconocedorVoz.start();
            }
        </script>
    </body>
    </html>
    """

class EntradaTexto(BaseModel):
    texto: str

@app.post("/procesar")
async def procesar(data: EntradaTexto):
    if not client_gemini:
        return {"respuesta": "Clave API no configurada."}

    prompt = (
        "Eres JARVIS, la Inteligencia Artificial sofisticada de Tony Stark. "
        "Responde a lo que pregunta el usuario en español con elegancia, precisión y profesionalismo. "
        "Al finalizar tu respuesta, concluye SIEMPRE exactamente con la frase: "
        "'Aquí le dejo información que puede gustarle señor, si gusta otra información puedo dársela.' "
        f"El usuario dice: {data.texto}"
    )

    modelos = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]

    for modelo in modelos:
        try:
            res = client_gemini.models.generate_content(
                model=modelo,
                contents=prompt
            )
            return {"respuesta": res.text}
        except Exception:
            continue

    return {"respuesta": "Señor, los servidores de enlace neuronal están temporalmente saturados. Por favor, reintente en un momento."}
