from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "canais"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Rota de upload de imagem
@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        # Verifica extensão permitida
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(status_code=400, detail="Formato de imagem não suportado.")

        file_id = f"{uuid.uuid4()}.{ext}"
        content_type = file.content_type or "image/jpeg"

        # Lê o conteúdo do arquivo em bytes
        conteudo = file.file.read()

        # Faz upload no Supabase Storage
        response = supabase.storage.from_(BUCKET).upload(
            file_id,
            conteudo,
            {"content-type": content_type},
            upsert=True  # Permite sobrescrever se necessário
        )

        if hasattr(response, "error") and response.error:
            raise HTTPException(status_code=500, detail=f"Erro no upload: {response.error}")

        # Gera URL pública
        url = supabase.storage.from_(BUCKET).get_public_url(file_id)
        return {"url": url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

# Exemplo de rota básica para testes
@app.get("/")
def read_root():
    return {"status": "API no ar"}
