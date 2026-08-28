import os
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

# Configurar logs para ver errores en la consola de Render
logging.basicConfig(level=logging.INFO)

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="J.A.R.V.I.S. HUD Interface")

# Inicialización del cliente Groq
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    logging.warning("¡ADVERTENCIA! GROQ_API_KEY no encontrada en las variables de entorno.")

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
        # Al final de main.py
from fastapi import FastAPI
# ... todo tu código ...

# Añadir esto al final:
app = app
