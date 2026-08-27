from fastapi import FastAPI, UploadFile, File
from google import genai
from groq import Groq
import os

app = FastAPI()

# --- REEMPLAZA AQUÍ CON TUS CLAVES REALES DENTRO DE LAS COMILLAS ---
GEMINI_KEY = "AQ.Ab8RN6ITAg5KbyR8C_hPa2XIQ106q_qqe72ro43GADTXm0MQng"
GROQ_KEY = "Tgsk_jVz51YcC9inR39i1GL8UWGdyb3FYeG6ciV94B7xTpR7v6hJXwhmF"

client_gemini = genai.Client(api_key=GEMINI_KEY)
client_groq = Groq(api_key=GROQ_KEY)

@app.get("/")
def inicio():
    return {"estado": "JARVIS online y escuchando"}

@app.post("/jarvis")
async def procesar_audio(file: UploadFile = File(...)):
    # 1. Guardar el archivo temporalmente
    audio_path = f"temp_{file.filename}"
    with open(audio_path, "wb") as f:
        f.write(await file.read())

    # 2. Transcribir voz a texto usando Groq (Whisper)
    with open(audio_path, "rb") as audio_file:
        transcripcion = client_groq.audio.transcriptions.create(
            file=(audio_path, audio_file.read()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )

    # Borrar archivo temporal
    os.remove(audio_path)

    # 3. Enviar texto a Gemini para responder
    prompt = f"Eres JARVIS, un asistente inteligente y respetuoso pero conciso. Responde en español a esto: {transcripcion}"
    
    respuesta_gemini = client_gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return {
        "escuchado": transcripcion,
        "respuesta_jarvis": respuesta_gemini.text
    }
