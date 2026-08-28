from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from google import genai
from groq import Groq
import os

app = FastAPI()

GEMINI_KEY = os.getenv("GEMINI_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")

client_gemini = genai.Client(api_key=GEMINI_KEY)
client_groq = Groq(api_key=GROQ_KEY)

@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JARVIS Voice Control</title>
        <style>
            body { font-family: Arial, sans-serif; background: #0f172a; color: white; text-align: center; padding-top: 50px; }
            button { background: #0284c7; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; }
            button:hover { background: #0369a1; }
            #status { margin-top: 20px; font-size: 16px; color: #38bdf8; }
            #res { margin-top: 20px; font-size: 20px; font-weight: bold; color: #4ade80; }
        </style>
    </head>
    <body>
        <h1>JARVIS AI</h1>
        <button onclick="startRecording()">🎤 Presiona para Hablar</button>
        <div id="status"></div>
        <div id="res"></div>

        <script>
            async function startRecording() {
                const status = document.getElementById('status');
                const resDiv = document.getElementById('res');
                status.innerText = "Escuchando (4 segundos)...";
                resDiv.innerText = "";

                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mediaRecorder = new MediaRecorder(stream);
                const audioChunks = [];

                mediaRecorder.ondataavailable = event => audioChunks.push(event.data);
                mediaRecorder.onstop = async () => {
                    status.innerText = "Procesando en la nube...";
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append("file", audioBlob, "voice.wav");

                    const response = await fetch("/jarvis", { method: "POST", body: formData });
                    const data = await response.json();
                    
                    status.innerText = "Tú dijiste: " + data.escuchado;
                    resDiv.innerText = "JARVIS: " + data.respuesta_jarvis;
                };

                mediaRecorder.start();
                setTimeout(() => mediaRecorder.stop(), 4000);
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

    with open(audio_path, "rb") as audio_file:
        transcripcion = client_groq.audio.transcriptions.create(
            file=(audio_path, audio_file.read()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )

    os.remove(audio_path)

    prompt = f"Eres JARVIS, un asistente inteligente y respetuoso pero conciso. Responde en español a esto: {transcripcion}"
    
    respuesta_gemini = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "escuchado": transcripcion,
        "respuesta_jarvis": respuesta_gemini.text
    }
