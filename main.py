import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import logging

# Configurar logs
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="J.A.R.V.I.S. HUD Interface")

# Añadir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Verificar la clave de Groq
GROQ_KEY = os.getenv("GROQ_API_KEY")
logging.info(f"GROQ_API_KEY encontrada: {'Sí' if GROQ_KEY else 'No'}")

if not GROQ_KEY:
    logging.error("ERROR: GROQ_API_KEY no está configurada en Vercel")

client_groq = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

# 🧠 MEMORIA: Historial de conversación para que JARVIS recuerde el contexto
historial_conversacion = [
    {
        "role": "system",
        "content": "Eres J.A.R.V.I.S., la inteligencia artificial avanzada de Tony Stark. Responde de forma concisa (máximo 2 oraciones), extremadamente elegante, educada y profesional en español. Siempre llamas al usuario 'señor'."
    }
]

class EntradaTexto(BaseModel):
    texto: str

@app.get("/", response_class=HTMLResponse)
async def inicio():
    # Leer el HTML desde la carpeta static
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logging.error("No se encontró static/index.html")
        return "<h1>Error: No se encontró el archivo de interfaz.</h1>"

@app.post("/procesar")
async def procesar(data: EntradaTexto):
    if not client_groq:
        return {"respuesta": "Clave GROQ_API_KEY no configurada en el servidor."}

    # Añadir el mensaje del usuario al historial
    historial_conversacion.append({"role": "user", "content": data.texto})

    try:
        # Nota: Si sientes que tarda mucho, cambia el modelo a "llama-3.1-8b-instant"
        completion = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=historial_conversacion,
            temperature=0.6,
            max_tokens=150
        )
        
        respuesta = completion.choices[0].message.content
        
        # Añadir la respuesta de JARVIS al historial
        historial_conversacion.append({"role": "assistant", "content": respuesta})
        
        # Limitar el historial a las últimas 10 conversaciones para no saturar la API
        if len(historial_conversacion) > 21: 
            historial_conversacion = [historial_conversacion[0]] + historial_conversacion[-20:]

        return {"respuesta": respuesta}
        
    except Exception as e:
        logging.error(f"Error en Groq: {str(e)}")
        return {"respuesta": "Señor, he detectado una anomalía en el procesamiento central."}

# Añadir esto al final:
app = app
