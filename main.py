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
        <title>JARVIS SYSTEM</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { 
                background-color: #030712; 
                color: #e0f2fe; 
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                justify-content: center; 
                min-height: 100vh; 
                overflow: hidden;
            }

            .container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                z-index: 10;
            }

            h1 { 
                font-size: 2.2rem; 
                letter-spacing: 6px; 
                color: #38bdf8; 
                text-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
                margin-bottom: 6px;
            }

            .status-text {
                font-size: 0.95rem;
                color: #94a3b8;
                margin-bottom: 30px;
                height: 24px;
                letter-spacing: 1px;
            }

            /* Núcleo Holográfico / Esfera JARVIS */
            .jarvis-container {
                position: relative;
                width: 220px;
                height: 220px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 35px;
            }

            /* Anillo Exterior Giratorio */
            .ring-outer {
                position: absolute;
                width: 210px;
                height: 210px;
                border-radius: 50%;
                border: 2px dashed rgba(56, 189, 248, 0.4);
                animation: rotateRight 18s linear infinite;
            }

            /* Anillo Intermedio */
            .ring-inner {
                position: absolute;
                width: 170px;
                height: 170px;
                border-radius: 50%;
                border: 2px solid transparent;
                border-top: 2px solid #38bdf8;
                border-bottom: 2px solid #38bdf8;
                animation: rotateLeft 10s linear infinite;
            }

            /* Esfera Flotante Principal */
            .orb {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: radial-gradient(circle, #38bdf8 0%, #0284c7 50%, #0369a1 100%);
                box-shadow: 0 0 40px #0284c7, inset 0 0 15px #e0f2fe;
                animation: float 4s ease-in-out infinite;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            }

            /* Animación cuando JARVIS está hablando */
            .orb.speaking {
                animation: float 2s ease-in-out infinite, pulseTalk 0.4s ease-in-out infinite alternate;
                background: radial-gradient(circle, #7dd3fc 0%, #38bdf8 50%, #0284c7 100%);
                box-shadow: 0 0 60px #38bdf8, inset 0 0 25px #ffffff;
            }

            /* Estado Apagado / Standby */
            .orb.off {
                background: radial-gradient(circle, #334155 0%, #1e293b 100%);
                box-shadow: 0 0 10px rgba(255,255,255,0.05);
                animation: float 6s ease-in-out infinite;
            }
            .ring-outer.off, .ring-inner.off {
                border-color: rgba(255,255,255,0.1);
            }

            /* Estado Escuchando Instrucción */
            .orb.listening {
                background: radial-gradient(circle, #f43f5e 0%, #e11d48 70%);
                box-shadow: 0 0 50px #f43f5e;
            }

            @keyframes float {
                0%, 100% { transform: translateY(0px) scale(1); }
                50% { transform: translateY(-12px) scale(1.02); }
            }

            @keyframes pulseTalk {
                0% { transform: translateY(-6px) scale(1); }
                100% { transform: translateY(-6px) scale(1.18); }
            }

            @keyframes rotateRight {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }

            @keyframes rotateLeft {
                from { transform: rotate(0deg); }
                to { transform: rotate(-360deg); }
            }

            .response-box {
                max-width: 500px;
                padding: 15px 25px;
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 12px;
                backdrop-filter: blur(8px);
                min-height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.05rem;
                color: #7dd3fc;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            }

            .btn-power {
                margin-top: 30px;
                background: transparent;
                border: 1px solid #38bdf8;
                color: #38bdf8;
                padding: 10px 24px;
                border-radius: 30px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                letter-spacing: 1px;
            }
            .btn-power:hover {
                background: #38bdf8;
                color: #030712;
                box-shadow: 0 0 15px #38bdf8;
            }

            .voice-select-box { margin-top: 20px; text-align: center; }
            select { 
                padding: 6px 12px; 
                border-radius: 6px; 
                background: #0f172a; 
                color: #94a3b8; 
                border: 1px solid #334155; 
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>J.A.R.V.I.S.</h1>
            <div id="status" class="status-text">Haz clic para iniciar el sensor...</div>

            <div class="jarvis-container">
                <div id="ringOuter" class="ring-outer off"></div>
                <div id="ringInner" class="ring-inner off"></div>
                <div id="orb" class="orb off"></div>
            </div>

            <div id="responseBox" class="response-box">
                Esperando activación...
            </div>

            <button id="btnPower" class="btn-power" onclick="toggleSensor()">INICIAR SISTEMA</button>

            <div class="voice-select-box">
                <select id="voiceSelect"></select>
            </div>
        </div>

        <script>
            let audioContext, analyser, microphone;
            let isAudioInitialized = false;
            let isJarvisActive = false;
            let isSpeaking = false;
            let voices = [];
            let recognition;

            function cargarVoces() {
                voices = window.speechSynthesis.getVoices();
                const select = document.getElementById('voiceSelect');
                select.innerHTML = '';
                voices.forEach((voice, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = `${voice.name} (${voice.lang})`;
                    if (voice.lang.includes('es') && (voice.name.toLowerCase().includes('male') || voice.name.toLowerCase().includes('pablo') || voice.name.toLowerCase().includes('jorge') || voice.name.toLowerCase().includes('raul'))) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            }

            if ('speechSynthesis' in window) {
                window.speechSynthesis.onvoiceschanged = cargarVoces;
                cargarVoces();
            }

            function hablar(texto) {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    const utterance = new SpeechSynthesisUtterance(texto);
                    
                    const select = document.getElementById('voiceSelect');
                    if (voices[select.value]) {
                        utterance.voice = voices[select.value];
                    }

                    utterance.lang = 'es-ES';
                    utterance.rate = 1.0;     
                    utterance.pitch = 0.75; // Tono grave masculino

                    utterance.onstart = () => {
                        isSpeaking = true;
                        document.getElementById('orb').className = "orb speaking";
                    };

                    utterance.onend = () => {
                        isSpeaking = false;
                        if (isJarvisActive) {
                            document.getElementById('orb').className = "orb";
                            document.getElementById('status').innerText = "🔊 JARVIS Activo | Esperando tu voz u orden de apagar...";
                        } else {
                            apagarJarvisUI();
                        }
                    };

                    window.speechSynthesis.speak(utterance);
                }
            }

            async function toggleSensor() {
                if (!isAudioInitialized) {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        analyser = audioContext.createAnalyser();
                        microphone = audioContext.createMediaStreamSource(stream);

                        analyser.fftSize = 512;
                        microphone.connect(analyser);

                        isAudioInitialized = true;
                        document.getElementById('btnPower').innerText = "DESCONECTAR SENSORES";
                        document.getElementById('status').innerText = "🔊 Sensores listos. Aplaude para encender a JARVIS.";
                        document.getElementById('responseBox').innerText = "En espera de aplausos...";

                        iniciarDeteccionAplausos(stream);
                    } catch (e) {
                        document.getElementById('status').innerText = "Error: Acceso al micrófono denegado.";
                    }
                } else {
                    location.reload();
                }
            }

            let ultimoAplauso = 0;

            function iniciarDeteccionAplausos(stream) {
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                
                function loop() {
                    if (isAudioInitialized && !isJarvisActive && !isSpeaking) {
                        analyser.getByteFrequencyData(dataArray);
                        let suma = 0;
                        for (let i = 0; i < dataArray.length; i++) suma += dataArray[i];
                        let promedio = suma / dataArray.length;

                        if (promedio > 65) {
                            const ahora = Date.now();
                            if (ahora - ultimoAplauso > 120 && ahora - ultimoAplauso < 800) {
                                encenderJarvis(stream);
                                ultimoAplauso = 0;
                            } else {
                                ultimoAplauso = ahora;
                            }
                        }
                    }
                    requestAnimationFrame(loop);
                }
                loop();
            }

            function encenderJarvis(stream) {
                isJarvisActive = true;
                document.getElementById('orb').className = "orb";
                document.getElementById('ringOuter').className = "ring-outer";
                document.getElementById('ringInner').className = "ring-inner";
                document.getElementById('status').innerText = "🟢 JARVIS Encendido | Escuchando constantemente...";
                document.getElementById('responseBox').innerText = "A su servicio, señor.";

                hablar("A su servicio, señor. ¿En qué puedo ayudarle?");
                iniciarEscuchaContinua(stream);
            }

            function apagarJarvisUI() {
                isJarvisActive = false;
                document.getElementById('orb').className = "orb off";
                document.getElementById('ringOuter').className = "ring-outer off";
                document.getElementById('ringInner').className = "ring-inner off";
                document.getElementById('status').innerText = "🔊 JARVIS Apagado | Da dos aplausos para reactivar.";
                document.getElementById('responseBox').innerText = "Sistemas en pausa.";
            }

            function iniciarEscuchaContinua(stream) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                
                if (!SpeechRecognition) {
                    document.getElementById('responseBox').innerText = "Se recomienda Google Chrome para el soporte de voz continuo.";
                    return;
                }

                recognition = new SpeechRecognition();
                recognition.continuous = true;
                recognition.lang = 'es-ES';
                recognition.interimResults = false;

                recognition.onresult = async (event) => {
                    if (!isJarvisActive || isSpeaking) return;

                    const lastResultIndex = event.results.length - 1;
                    const textoEscuchado = event.results[lastResultIndex][0].transcript.trim().toLowerCase();

                    // Comando de Apagado
                    if (textoEscuchado.includes("apágate") || textoEscuchado.includes("apagate") || textoEscuchado.includes("descansa") || textoEscuchado.includes("desactívate")) {
                        recognition.stop();
                        isJarvisActive = false;
                        hablar("Entendido, señor. Desactivando sistemas.");
                        return;
                    }

                    document.getElementById('status').innerText = "⚙️ Procesando: " + textoEscuchado;
                    document.getElementById('orb').className = "orb listening";

                    try {
                        const response = await fetch("/jarvis-texto", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ texto: textoEscuchado })
                        });
                        const data = await response.json();

                        document.getElementById('responseBox').innerText = data.respuesta_jarvis;
                        hablar(data.respuesta_jarvis);
                    } catch (e) {
                        document.getElementById('status').innerText = "Error de conexión.";
                    }
                };

                recognition.onend = () => {
                    if (isJarvisActive) {
                        recognition.start();
                    }
                };

                recognition.start();
            }
        </script>
    </body>
    </html>
    """

class PromptInput(BaseModel):
    texto: str

@app.post("/jarvis-texto")
async def procesar_texto(data: PromptInput):
    if not client_gemini:
        return {"respuesta_jarvis": "Falta la clave API de Gemini."}

    try:
        prompt = (
            "Eres JARVIS, la Inteligencia Artificial sofisticada de Tony Stark. "
            "Responde de forma muy concisa (máximo 2 oraciones), extremadamente elegante, educada, sobria y profesional, en español. "
            f"El usuario dice: {data.texto}"
        )
        respuesta_gemini = client_gemini.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return {"respuesta_jarvis": respuesta_gemini.text}
    except Exception as e:
        return {"respuesta_jarvis": f"Ocurrió un error en mis sistemas: {str(e)}"}
