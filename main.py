from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from google import genai
from groq import Groq
import os

app = FastAPI()

GEMINI_KEY = os.getenv("GEMINI_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")

client_gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
client_groq = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

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
            body { 
                background-color: #0b0f19; 
                color: white; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                justify-content: center; 
                height: 100vh; 
                margin: 0; 
            }
            .card { 
                background: #1e293b; 
                padding: 40px; 
                border-radius: 20px; 
                text-align: center; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.6); 
                max-width: 420px;
                width: 90%;
                border: 1px solid #334155;
            }
            h1 { color: #38bdf8; margin-bottom: 10px; letter-spacing: 2px; }
            .subtitle { color: #64748b; font-size: 14px; margin-bottom: 25px; }
            
            .indicator {
                width: 100px;
                height: 100px;
                border-radius: 50%;
                background: radial-gradient(circle, #38bdf8 0%, #0284c7 70%);
                margin: 0 auto 25px auto;
                box-shadow: 0 0 20px #0284c7;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                transition: all 0.3s ease;
            }
            .indicator.listening {
                background: radial-gradient(circle, #ef4444 0%, #dc2626 70%);
                box-shadow: 0 0 30px #ef4444;
                animation: pulse 1s infinite alternate;
            }
            .indicator.processing {
                background: radial-gradient(circle, #f59e0b 0%, #d97706 70%);
                box-shadow: 0 0 25px #f59e0b;
            }

            @keyframes pulse {
                0% { transform: scale(1); }
                100% { transform: scale(1.08); }
            }

            button { 
                background: #0284c7; 
                color: white; 
                border: none; 
                padding: 14px 28px; 
                font-size: 16px; 
                font-weight: bold; 
                border-radius: 50px; 
                cursor: pointer; 
                transition: all 0.2s;
                width: 100%;
                margin-top: 10px;
            }
            button:hover { background: #0369a1; }
            
            #status { margin-top: 20px; color: #94a3b8; font-weight: 500; }
            #res { margin-top: 15px; font-size: 17px; color: #38bdf8; font-weight: bold; min-height: 50px; }
            .voice-select-box { margin-top: 15px; text-align: left; }
            .voice-select-box label { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 5px; }
            select { width: 100%; padding: 8px; border-radius: 8px; background: #0f172a; color: #e2e8f0; border: 1px solid #334155; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>JARVIS</h1>
            <div class="subtitle">Activación por Aplauso</div>

            <div id="orb" class="indicator">🎙️</div>

            <button id="startSysBtn" onclick="iniciarSistema()">⚡ Activar Detección de Aplausos</button>

            <div id="status">Presiona el botón para activar los sensores.</div>
            <div id="res"></div>

            <div class="voice-select-box">
                <label for="voiceSelect">Voz del sistema:</label>
                <select id="voiceSelect"></select>
            </div>
        </div>

        <script>
            let audioContext;
            let analyser;
            let microphone;
            let isSystemActive = false;
            let isRecording = false;
            let mediaRecorder;
            let audioChunks = [];
            let voices = [];

            function cargarVoces() {
                voices = window.speechSynthesis.getVoices();
                const select = document.getElementById('voiceSelect');
                select.innerHTML = '';

                voices.forEach((voice, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = `${voice.name} (${voice.lang})`;
                    
                    if (voice.lang.includes('es') && (voice.name.toLowerCase().includes('male') || voice.name.toLowerCase().includes('pablo') || voice.name.toLowerCase().includes('jorge') || voice.name.toLowerCase().includes('raul') || voice.name.toLowerCase().includes('hombre'))) {
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
                    utterance.pitch = 0.75;  // Voz grave de hombre

                    window.speechSynthesis.speak(utterance);
                }
            }

            async function iniciarSistema() {
                if (isSystemActive) return;

                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    analyser = audioContext.createAnalyser();
                    microphone = audioContext.createMediaStreamSource(stream);

                    analyser.fftSize = 512;
                    microphone.connect(analyser);

                    isSystemActive = true;
                    document.getElementById('startSysBtn').style.display = 'none';
                    document.getElementById('status').innerText = "🔊 Escuchando aplausos... (Da dos aplausos fuertes)";

                    escucharAplausos(stream);
                } catch (e) {
                    document.getElementById('status').innerText = "Error: Acceso al micrófono denegado.";
                }
            }

            let ultimoAplauso = 0;

            function escucharAplausos(stream) {
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                
                function detectar() {
                    if (!isSystemActive || isRecording) {
                        requestAnimationFrame(detectar);
                        return;
                    }

                    analyser.getByteFrequencyData(dataArray);
                    
                    let suma = 0;
                    for (let i = 0; i < dataArray.length; i++) {
                        suma += dataArray[i];
                    }
                    let promedio = suma / dataArray.length;

                    if (promedio > 65) {
                        const ahora = Date.now();
                        if (ahora - ultimoAplauso > 120 && ahora - ultimoAplauso < 800) {
                            activarJarvis(stream);
                            ultimoAplauso = 0;
                        } else {
                            ultimoAplauso = ahora;
                        }
                    }
                    requestAnimationFrame(detectar);
                }
                detectar();
            }

            async function activarJarvis(stream) {
                isRecording = true;
                const orb = document.getElementById('orb');
                const status = document.getElementById('status');
                const resDiv = document.getElementById('res');

                orb.className = "indicator listening";
                orb.innerText = "🎙️";
                status.innerText = "¡Aplauso detectado! Escuchando orden...";
                resDiv.innerText = "";

                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
                
                mediaRecorder.onstop = async () => {
                    orb.className = "indicator processing";
                    orb.innerText = "⚙️";
                    status.innerText = "Procesando respuesta...";

                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append("file", audioBlob, "voice.wav");

                    try {
                        const response = await fetch("/jarvis", { method: "POST", body: formData });
                        const data = await response.json();

                        status.innerText = "Tú: " + data.escuchado;
                        resDiv.innerText = "JARVIS: " + data.respuesta_jarvis;

                        hablar(data.respuesta_jarvis);
                    } catch (e) {
                        status.innerText = "Error procesando el audio.";
                    } finally {
                        setTimeout(() => {
                            isRecording = false;
                            orb.className = "indicator";
                            orb.innerText = "🎙️";
                            status.innerText = "🔊 Escuchando aplausos nuevamente...";
                        }, 2000);
                    }
                };

                mediaRecorder.start();
                
                setTimeout(() => {
                    if (mediaRecorder.state === "recording") {
                        mediaRecorder.stop();
                    }
                }, 4000);
            }
        </script>
    </body>
    </html>
    """

@app.post("/jarvis")
async def procesar_audio(file: UploadFile = File(...)):
    if not client_gemini or not client_groq:
        return {"escuchado": "Error", "respuesta_jarvis": "Faltan las claves API en Vercel."}

    try:
        audio_bytes = await file.read()
        audio_file_tuple = ("voice.wav", audio_bytes)

        transcripcion = client_groq.audio.transcriptions.create(
            file=audio_file_tuple,
            model="whisper-large-v3-turbo",
            response_format="text"
        )

        prompt = (
            "Eres JARVIS, la Inteligencia Artificial de Tony Stark. Responde de forma muy concisa, respetuosa, "
            "elegante y profesional, en español. Hablas como un asistente masculino sobrio. "
            f"El usuario dice: {transcripcion}"
        )
        respuesta_gemini = client_gemini.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return {
            "escuchado": transcripcion,
            "respuesta_jarvis": respuesta_gemini.text
        }
    except Exception as e:
        return {
            "escuchado": "Error en el servidor",
            "respuesta_jarvis": f"Detalle del error: {str(e)}"
        }
