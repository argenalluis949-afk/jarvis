from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai

app = FastAPI()

# Pega tu API Key directamente entre las comillas
API_KEY = "AQ.Ab8RN6ITAg5KbyR8C_hPa2XIQ106q_qqe72ro43GADTXm0MQng"

try:
    client_gemini = genai.Client(api_key=API_KEY)
except Exception as e:
    client_gemini = None
    print(f"Error al inicializar cliente: {e}")

@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>J.A.R.V.I.S.</title>
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
                padding: 20px;
            }

            .jarvis-widget {
                position: relative;
                width: 220px;
                height: 220px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .reactor-ring {
                position: absolute;
                border-radius: 50%;
                border: 2px dashed rgba(56, 189, 248, 0.3);
            }
            .ring-1 { width: 210px; height: 210px; animation: spin 20s linear infinite; }
            .ring-2 { width: 160px; height: 160px; border: 2px solid rgba(56, 189, 248, 0.5); border-top-color: transparent; animation: spinRev 10s linear infinite; }

            .orb {
                width: 100px;
                height: 100px;
                border-radius: 50%;
                background: radial-gradient(circle, #38bdf8 0%, #0284c7 60%, #0f172a 100%);
                box-shadow: 0 0 40px rgba(56, 189, 248, 0.4);
                animation: float 3.5s ease-in-out infinite;
                transition: all 0.4s ease;
                z-index: 5;
            }
            .orb.speaking { animation: float 1.5s ease-in-out infinite, pulse 0.3s ease-in-out infinite alternate; box-shadow: 0 0 70px #38bdf8; }
            .orb.listening { background: radial-gradient(circle, #f43f5e 0%, #be123c 100%); box-shadow: 0 0 50px #f43f5e; }

            @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-8px); } }
            @keyframes pulse { 0% { transform: scale(0.95); } 100% { transform: scale(1.1); } }
            @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            @keyframes spinRev { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }

            .status-display {
                margin-top: 25px;
                font-size: 0.85rem;
                letter-spacing: 2px;
                color: #94a3b8;
                text-align: center;
            }

            .response-text {
                margin-top: 15px;
                max-width: 550px;
                text-align: center;
                font-size: 1.05rem;
                color: #e0f2fe;
                min-height: 45px;
                line-height: 1.5;
            }

            .btn-start {
                margin-top: 30px;
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

        <div class="jarvis-widget">
            <div class="reactor-ring ring-1"></div>
            <div class="reactor-ring ring-2"></div>
            <div id="orb" class="orb"></div>
        </div>

        <div id="statusText" class="status-display">SISTEMA EN ESPERA</div>
        <div id="responseText" class="response-text">Inicialice el sistema.</div>

        <button id="btnPower" class="btn-start" onclick="iniciarJARVIS()">INICIAR JARVIS</button>

        <script>
            let reconocedorVoz;
            let estaHablando = false;
            let sistemaActivo = false;

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
                    document.getElementById('responseText').innerText = data.respuesta;
                    hablar(data.respuesta);
                } catch (e) {
                    document.getElementById('statusText').innerText = "ERROR DE CONEXIÓN";
                }
            }

            function iniciarJARVIS() {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    alert("Usa Google Chrome para el reconocimiento de voz.");
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
    if not client_gemini or API_KEY == "AQ.Ab8RN6ITAg5KbyR8C_hPa2XIQ106q_qqe72ro43GADTXm0MQng":
        return {"respuesta": "Señor, debe colocar su API Key válida directamente en la variable API_KEY del archivo main.py."}

    prompt = (
        "Eres JARVIS, la Inteligencia Artificial de el señor luis. "
        "Responde brevemente y en español con elegancia. "
        "Concluye diciendo: 'Aquí le doy información que le puede interesar señor, si gusta otra información puedo dársela.' "
        f"El usuario dice: {data.texto}"
    )

    try:
        # CÓDIGO CORREGIDO:
res = client_gemini.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt
)
        return {"respuesta": res.text}
    except Exception as e:
        print(f"Error interno: {e}")
        return {"respuesta": f"Señor, la API devolvió este error exacto: {str(e)}"}
