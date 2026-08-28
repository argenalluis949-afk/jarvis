from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from google import genai
from groq import Groq
import os

app = FastAPI()

# Claves obtenidas de las variables de entorno en Render
GEMINI_KEY = os.getenv("GEMINI_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")

client_gemini = genai.Client(api_key=GEMINI_KEY)
client_groq = Groq(api_key=GROQ_KEY)

@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JARVIS AI</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #0b0f19;
                color: #e2e8f0;
                font-family: Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
            }

            .container {
                text-align: center;
                background: #1e293b;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
                max-width: 450px;
                width: 90%;
            }

            h1 {
                margin-bottom: 30px;
                color: #38bdf8;
                letter-spacing: 2px;
            }

            button {
                background-color: #0284c7;
                color: white;
                border: none;
                padding: 16px 32px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 50px;
                cursor: pointer;
                transition: background 0.3s ease, transform 0.2s ease;
                box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
            }

            button:hover {
                background-color: #0369a1;
                transform: scale(1.03);
            }

            #status {
                margin-top: 25px;
                font-size: 15px;
                color: #94a3b8;
            }

            #res {
                margin-top: 20px;
                font-size: 18px;
                font-weight: bold;
                color: #4ade80;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>JARVIS SYSTEM</h1>
            <button onclick="startRecording()">🎤 Presiona para Hablar</button>
            <div id="status">SISTEMA ONLINE</div>
            <div id="res"></div>
        </div>

        <script>
            async function startRecording() {
                const status = document.getElementById('status');
                const resDiv = document.getElementById('res');
                status.innerText = "Escuchando (4 segundos)...";
                resDiv.innerText = "";

                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const mediaRecorder = new MediaRecorder(stream);
                    const audioChunks = [];

                    mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
                    mediaRecorder.onstop = async () => {
                        status.innerText = "Procesando en la nube...";
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append("file", audioBlob, "voice.wav");

                        try {
                            const response = await fetch("/jarvis", { method: "POST", body: formData });
                            const data = await response.json();
                            
                            status.innerText = "Tú: " + data.escuchado;
                            resDiv.innerText = "JARVIS: " + data.respuesta_jarvis;
                        } catch (err) {
                            status.innerText = "Error de comunicación con el servidor.";
                        }
                    };

                    mediaRecorder.start();
                    setTimeout(() => mediaRecorder.stop(), 4000);
                } catch (err) {
                    status.innerText = "Error: Permiso de micrófono denegado.";
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/jarvis")
async def procesar_audio(file: UploadFile = File(...)):
    audio_path = f"temp_{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())

    # Transcripción con Groq
    with open(audio_path, "rb") as audio_file:
        transcripcion = client_groq.audio.transcriptions.create(
            file=(audio_path, audio_file.read()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )

    if os.path.exists(audio_path):
        os.remove(audio_path)

    # Respuesta con Gemini (usando el modelo activo)
    prompt = f"Eres JARVIS, un asistente inteligente, conciso y servicial. Responde en español a esto: {transcripcion}"
    
    respuesta_gemini = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "escuchado": transcripcion,
        "respuesta_jarvis": respuesta_gemini.text
    }
