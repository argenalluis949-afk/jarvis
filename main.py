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

            .hud-grid {
                display: flex;
                gap: 15px;
                margin-bottom: 25px;
                flex-wrap: wrap;
                justify-content: center;
                width: 100%;
                max-width: 800px;
                opacity: 0;
                transform: scale(0.2) translateY(-50px);
                pointer-events: none;
                transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }

            .hud-grid.desplegar {
                opacity: 1;
                transform: scale(1) translateY(0);
                pointer-events: auto;
            }

            .hud-card {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
                padding: 15px 25px;
                text-align: center;
                min-width: 180px;
                backdrop-filter: blur(10px);
                box-shadow: 0 0 25px rgba(56, 189, 248, 0.25);
            }

            .hud-label {
                font-size: 0.75rem;
                color: #94a3b8;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            .hud-value {
                font-size: 1.3rem;
                font-weight: bold;
                color: #38bdf8;
                margin-top: 6px;
                text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
            }

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
                max-width: 550px;
                text-align: center;
                font-size: 1rem;
                color: #e0f2fe;
                min-height: 45px;
                line-height: 1.4;
            }

            .btn-start {
                margin-top: 25px;
                background: transparent;
                border: 1px solid #38bdf8;
                color: #38bdf8;
                padding: 12px 30px;
                border-radius: 20px;
                cursor: pointer;
                letter-spacing: 2px;
                transition: 0.3s;
                font-family: inherit;
            }
            .btn-start:hover { background: #38bdf8; color: #020617; box-shadow: 0 0 15px #38bdf8; }
        </style>
    </head>
    <body>

        <div id="hudPanels" class="hud-grid">
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

        <div id="statusText" class="status-display">SISTEMA EN ESPERA</div>
        <div id="responseText" class="response-text">Inicialice la interfaz neuronal.</div>

        <button id="btnPower" class="btn-start" onclick="iniciarJARVIS()">INICIAR JARVIS</button>

        <script>
            let reconocedorVoz;
            let estaHablando = false;
            let sistemaActivo = false;

            function actualizarReloj() {
                const ahora = new Date();
                document.getElementById('valHora').innerText = ahora.toLocaleTimeString();
            }
            setInterval(actualizarReloj, 1000);
            actualizarReloj();

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
                        document.getElementById('orb').className = "orb";
                        document.getElementById('statusText').innerText = "JARVIS ONLINE | ESCUCHANDO";
                        
                        // Reiniciar la escucha apenas termina de hablar
                        if (sistemaActivo) {
                            try { reconocedorVoz.start(); } catch(e){}
                        }
                    };

                    window.speechSynthesis.speak(utt);
                }
            }

            async function procesarComando(texto) {
                if (!texto || estaHablando) return;

                document.getElementById('responseText').innerText = '"' + texto + '"';
                document.getElementById('orb').className = "orb listening";
                document.getElementById('statusText').innerText = "PROCESANDO...";

                try {
                    const res = await fetch("/procesar", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ texto: texto })
                    });
                    const data = await res.json();

                    document.getElementById('hudPanels').classList.add('desplegar');
                    document.getElementById('responseText').innerText = data.respuesta;
                    
                    hablar(data.respuesta);
                } catch (e) {
                    document.getElementById('statusText').innerText = "ERROR DE CONEXIÓN";
                }
            }

            function iniciarJARVIS() {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    alert("Se requiere Google Chrome para el soporte de voz.");
                    return;
                }

                sistemaActivo = true;
                document.getElementById('btnPower').style.display = 'none';
                document.getElementById('orb').className = "orb";
                document.getElementById('statusText').innerText = "JARVIS ONLINE | ESCUCHANDO";
                document.getElementById('responseText').innerText = "Sistemas listos, señor.";

                reconocedorVoz = new SpeechRecognition();
                reconocedorVoz.lang = 'es-ES';
                reconocedorVoz.continuous = false;
                reconocedorVoz.interimResults = false;

                reconocedorVoz.onstart = () => {
                    if (!estaHablando) {
                        document.getElementById('orb').className = "orb listening";
                        document.getElementById('statusText').innerText = "ESCUCHANDO...";
                    }
                };

                reconocedorVoz.onresult = (event) => {
                    const comando = event.results[0][0].transcript;
                    procesarComando(comando);
                };

                reconocedorVoz.onerror = (event) => {
                    if (sistemaActivo && !estaHablando) {
                        setTimeout(() => { try { reconocedorVoz.start(); } catch(e){} }, 500);
                    }
                };

                reconocedorVoz.onend = () => {
                    if (sistemaActivo && !estaHablando) {
                        try { reconocedorVoz.start(); } catch(e){}
                    }
                };

                hablar("A su servicio, señor. Le escucho.");
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
        print("ERROR: GEMINI_KEY no está configurada.")
        return {"respuesta": "Señor, la clave de API de Gemini no está configurada en el sistema."}

    prompt = (
        "Eres JARVIS, la Inteligencia Artificial sofisticada de Tony Stark. "
        "Responde a la duda o petición del usuario en español con elegancia y concisión. "
        "Al finalizar tu respuesta, concluye SIEMPRE de forma fluida agregando la frase: "
        "'Aquí le doy información que le puede interesar señor, si gusta otra información puedo dársela.' "
        f"El usuario dice: {data.texto}"
    )

    # Nombres de modelos actualizados para la librería google-genai
    modelos = ["gemini-2.5-flash", "gemini-1.5-flash"]

    for modelo in modelos:
        try:
            print(f"Enviando consulta a Gemini ({modelo})...")
            res = client_gemini.models.generate_content(
                model=modelo,
                contents=prompt
            )
            print("Respuesta recibida correctamente.")
            return {"respuesta": res.text}
        except Exception as e:
            print(f"Error en {modelo}: {e}")
            continue

    return {"respuesta": "Señor, los servidores de enlace neuronal están temporalmente saturados. Por favor, reintente en un momento."}
