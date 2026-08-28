import os
import logging
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# Configurar logs para ver TODO en Vercel
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="J.A.R.V.I.S. HUD Interface")

# Permitir peticiones desde cualquier origen (vital para Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Groq
GROQ_KEY = os.getenv("GROQ_API_KEY")
logging.info(f"¿GROQ_API_KEY encontrada?: {'SÍ' if GROQ_KEY else 'NO'}")

client_groq = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

class EntradaTexto(BaseModel):
    texto: str

# Historial básico para que recuerde el contexto
historial = [
    {"role": "system", "content": "Eres J.A.R.V.I.S. Responde de forma concisa (máximo 2 oraciones), elegante, educada y profesional en español. Llama al usuario 'señor'."}
]

@app.get("/")
async def inicio():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error leyendo index.html: {e}")
        return {"error": "No se encontró static/index.html"}

@app.post("/procesar")
async def procesar(data: EntradaTexto):
    logging.info(f"Petición recibida: {data.texto}")
    
    if not client_groq:
        logging.error("ERROR CRÍTICO: GROQ_API_KEY no está en las variables de entorno de Vercel.")
        return {"respuesta": "Señor, la clave de acceso al núcleo no está configurada."}

    historial.append({"role": "user", "content": data.texto})

    try:
        logging.info("Llamando a la API de Groq...")
        completion = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=historial,
            temperature=0.6,
            max_tokens=150
        )
        
        respuesta = completion.choices[0].message.content
        historial.append({"role": "assistant", "content": respuesta})
        
        # Mantener el historial corto para no saturar
        if len(historial) > 15:
            historial = [historial[0]] + historial[-14:]
            
        return {"respuesta": respuesta}
        
    except Exception as e:
        # ESTO ES LO QUE NOS SALVARÁ: Imprime el error exacto en los logs de Vercel
        logging.error(f"ERROR EN GROQ: {str(e)}")
        logging.error(f"TRACEBACK: {traceback.format_exc()}")
        return {"respuesta": "Señor, he detectado una anomalía en el procesamiento central."}
