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
                overflow: hidden;
            }

            /* Widget Flotante Estilo Holograma */
            .jarvis-widget {
                position: relative;
                width: 300px;
                height: 300px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }

            .reactor-ring {
                position: absolute;
                border-radius: 50%;
                border: 2px dashed rgba(56, 189, 248, 0.3);
                transition: all 0.5s ease;
            }
            .ring-1 { width: 280px; height: 280px; animation: spin 20s linear infinite; }
            .ring-2 { width: 220px; height: 220px; border: 2px solid rgba(56, 189, 248, 0.5); border-top-color: transparent; animation: spinRev 10s linear infinite; }

            /* Esfera Central Flotante */
            .orb {
                width: 130px;
                height: 130px;
                border-radius: 50%;
                background: radial-gradient(circle, #38bdf8 0%, #0284c7 60%, #0f172a 100%);
                box-shadow: 0 0 50px rgba(56, 189, 248, 0.4);
                animation: float 3.5s ease-in-out infinite;
                transition: all 0.4s ease;
                z-index: 5;
            }

            /* Estados del Orbe */
            .orb.off {
                background: radial-gradient(circle, #334155 0%, #0f172a 100%);
                box-shadow: 0 0 10px rgba(255, 255, 255, 0.05);
            }
            .orb.speaking {
                animation: float 1.5s ease-in-out infinite, pulse 0.3s ease-in-out infinite alternate;
                background: radial-gradient(circle, #bae6fd 0%, #38bdf8 50%, #0284c7 100%);
                box-shadow: 0 0 80px #38bdf8;
            }
            .orb.listening {
                background: radial-gradient(circle, #f43f5e 0%, #be123c 100%);
                box-shadow: 0 0 60px #f43f5e;
            }

            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-15px); }
            }
            @keyframes pulse {
                0% { transform: scale(0.95); }
                100% { transform: scale(1.1); }
            }
            @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            @keyframes spinRev { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }

            .status-display {
                margin-top: 30px;
                font-size: 0.85rem;
                letter-spacing: 2px;
                text-transform: uppercase;
                color: #94a3b8;
                text-align: center;
                height: 20px;
            }

            .response-text {
                margin-top: 15px;
                max-width: 450px;
                text-align: center;
                font-size: 1rem;
                color: #e0f2fe;
                min-height: 50px;
            }

            .btn-start {
                margin-top: 25px;
                background: transparent;
                border: 1px solid #38bdf8;
                color: #38bdf8;
                padding: 10px 20px;
                border-radius: 20px;
                cursor: pointer;
                letter-spacing: 1px;
                transition: 0.3s;
            }
            .btn-start:hover {
                background: #38bdf8;
                color: #020617;
                box-shadow: 0 0 15px #38bdf8;
            }
        </style>
    </head>
    <body>

        <div class="jarvis-widget">
            <div class="reactor-ring ring-1"></div>
            <div class="reactor-ring ring-2"></div>
            <div id="orb" class="orb off"></div>
        </div>

        <div id="statusText" class="status-display">SISTEMA OFFLINE</div>
        <div id="responseText" class="response-text">Presiona "Conectar" para calibrar sensores.</div>

        <button id="btnPower" class="btn-start" onclick="iniciarSistema()">CONECTAR SISTEMA</button>

        <script>
            let audioCtx, analyser, micStream;
            let sistemaConectado = false;
            let jarvisEncendido = false;
            let reconocedorVoz;
            let estaHablando = false;

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
                    document.getElementById('statusText').innerText = "SENSORES ACTIVOS | APLAUDE PARA ENCENDER";
                    document.getElementById('responseText').innerText = "Esperando señal de impacto (aplauso)...";

                    calibrarDeteccionAplausos();
                    prepararReconocimientoVoz();
                } catch (err) {
                    alert("Se requiere acceso al micrófono para operar el sistema.");
                }
            }

            // Detección de aplauso por picos drásticos de sonido (transitorios)
            function calibrarDeteccionAplausos() {
                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);
                let ultimoPico = 0;

                function medir() {
                    if (sistemaConectado && !jarvisEncendido && !estaHablando) {
                        analyser.getByteFrequencyData(dataArray);
                        
                        let suma = 0;
                        for (let i = 0; i < bufferLength; i++) {
                            suma += dataArray[i];
                        }
                        let promedio = suma / bufferLength;

                        // Se requiere un pico de volumen alto repentino (> 85)
                        if (promedio > 85) {
                            let ahora = Date.now();
                            if (ahora - ultimoPico < 600 && ahora - ultimoAplauso > 200) {
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
                jarvisEncendido = true;
                document.getElementById('orb').className = "orb";
                document.getElementById('statusText').innerText = "JARVIS ONLINE | ESCUCHANDO";
                hablar("A su servicio, señor. Sistemas listos.");
                
                if (reconocedorVoz) {
                    try { reconocedorVoz.start(); } catch(e){}
                }
            }

            function apagarJarvis() {
                jarvisEncendido = false;
                if (reconocedorVoz) reconocedorVoz.stop();
                document.getElementById('orb').className = "orb off";
                document.getElementById('statusText').innerText = "MODO ESPERA | APLAUDE PARA REACTIVAR";
                document.getElementById('responseText').innerText = "Sistemas en pausa.";
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
                        } else {
                            apagarJarvis();
                        }
                    };

                    window.speechSynthesis.speak(utt);
                }
            }

            function prepararReconocimientoVoz() {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    document.getElementById('responseText').innerText = "Navegador no compatible con Web Speech. Usa Google Chrome.";
                    return;
                }

                reconocedorVoz = new SpeechRecognition();
                reconocedorVoz.continuous = true;
                reconocedorVoz.lang = 'es-ES';
                reconocedorVoz.interimResults = false;

                reconocedorVoz.onresult = async (event) => {
                    if (!jarvisEncendido || estaHablando) return;

                    const index = event.results.length - 1;
                    const comando = event.results[index][0].transcript.trim().toLowerCase();

                    document.getElementById('responseText').innerText = '"' + comando + '"';

                    // Comando de apagado
                    if (comando.includes("apágate") || comando.includes("apagate") || comando.includes("descansa") || comando.includes("desactívate")) {
                        hablar("Desactivando interfaz. Hasta luego, señor.");
                        jarvisEncendido = false;
                        return;
                    }

                    // Enviar comando a backend
                    document.getElementById('orb').className = "orb listening";
                    document.getElementById('statusText').innerText = "PROCESANDO... ";

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
                    if (jarvisEncendido && !estaHablando) {
                        try { reconocedorVoz.start(); } catch(e){}
                    }
                };
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

    try:
        prompt = (
            "Eres JARVIS, la Inteligencia Artificial sofisticada de Tony Stark. "
            "Responde de forma muy concisa (máximo 2 oraciones), extremadamente elegante, educada, sobria y profesional, en español. "
            f"El usuario dice: {data.texto}"
        )
        res = client_gemini.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return {"respuesta": res.text}
    except Exception as e:
        return {"respuesta": f"Fallo en los circuitos principales: {str(e)}"}
