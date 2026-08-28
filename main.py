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
                font-family: Arial, sans-serif; 
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
                border-radius: 16px; 
                text-align: center; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.5); 
                max-width: 400px;
                width: 90%;
            }
            h1 { color: #38bdf8; margin-bottom: 25px; }
            button { 
                background: #0284c7; 
                color: white; 
                border: none; 
                padding: 15px 30px; 
                font-size: 18px; 
                font-weight: bold; 
                border-radius: 50px; 
                cursor: pointer; 
                transition: background 0.2s;
            }
            button:hover { background: #0369a1; }
            #status { margin-top: 20px; color: #94a3b8; }
            #res { margin-top: 20px; font-size: 18px; color: #4ade80; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>JARVIS SYSTEM</h1>
            <button id="micBtn" onclick="startRecording()">🎤 Presiona para Hablar</button>
            <div id="status">SISTEMA ONLINE</div>
            <div id="res"></div>
        </div>

        <script>
            function hablar(texto) {
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel(); // Detener cualquier audio previo
                    const utterance = new SpeechSynthesisUtterance(texto);
                    utterance.lang = 'es-ES'; // Idioma español
                    utterance.rate = 1.0;     // Velocidad normal
                    utterance.pitch = 0.9;    // Tono ligeramente más grave para JARVIS
                    window.speechSynthesis.speak(utterance);
                }
            }

            async function startRecording() {
                const status = document.getElementById('status');
                const resDiv = document.getElementById('res');
                const btn = document.getElementById('micBtn');

                btn.disabled = true;
                status.innerText = "Escuchando (4 segundos)...";
                resDiv.innerText = "";

                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const mediaRecorder = new MediaRecorder(stream);
                    const audioChunks = [];

                    mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
                    mediaRecorder.onstop = async () => {
                        status.innerText = "Procesando respuesta...";
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append("file", audioBlob, "voice.wav");

                        try {
                            const response = await fetch("/jarvis", { method: "POST", body: formData });
                            const data = await response.json();
                            
                            status.innerText = "Tú: " + data.escuchado;
                            resDiv.innerText = "JARVIS: " + data.respuesta_jarvis;
                            
                            // JARVIS responde con voz
                            hablar(data.respuesta_jarvis);
                        } catch (e) {
                            status.innerText = "Error procesando el audio";
                        } finally {
                            btn.disabled = false;
                        }
                    };

                    mediaRecorder.start();
                    setTimeout(() => mediaRecorder.stop(), 4000);
                } catch (e) {
                    status.innerText = "Error: Acceso al micrófono denegado";
                    btn.disabled = false;
                }
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

        # Transcripción con Groq Whisper
        transcripcion = client_groq.audio.transcriptions.create(
            file=audio_file_tuple,
            model="whisper-large-v3-turbo",
            response_format="text"
        )

        # Generación de respuesta con Gemini
        prompt = (
            "Eres JARVIS, un asistente inteligente, directo y conciso. "
            f"Responde de forma breve y clara en español a lo siguiente: {transcripcion}"
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
