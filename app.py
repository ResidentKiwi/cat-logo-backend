from fastapi import FastAPI, UploadFile, File, HTTPException
from supabase import create_client, Client
import uuid
import os

app = FastAPI()

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "canais"  # Substitua pelo nome do seu bucket

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Gera nome único
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"

        # Lê o conteúdo do arquivo
        file_content = await file.read()

        # Realiza o upload
        res = supabase.storage.from_(BUCKET).upload(filename, file_content)

        # Verifica sucesso baseado no status_code
        if hasattr(res, "status_code") and res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {res}")

        # Retorna a URL pública do arquivo
        public_url = supabase.storage.from_(BUCKET).get_public_url(filename)
        return {"url": public_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")
