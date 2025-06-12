from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
import os
import uuid

app = FastAPI()

# Libera CORS para qualquer origem (útil para front-end externo como GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis de ambiente (devem estar configuradas no Render)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET = "imagens"

# Verifica se variáveis estão presentes
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL ou SUPABASE_KEY não configurados!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Modelo de canal
class Canal(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str = None

# Listar canais
@app.get("/canais")
def listar():
    try:
        result = supabase.table("canais").select("*").order("id", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Criar canal
@app.post("/canais")
def criar(canal: Canal):
    try:
        result = supabase.table("canais").insert(canal.dict()).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Atualizar canal
@app.put("/canais/{canal_id}")
def atualizar(canal_id: int, canal: Canal):
    try:
        result = supabase.table("canais").update(canal.dict(exclude_unset=True)).eq("id", canal_id).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Excluir canal
@app.delete("/canais/{canal_id}")
def deletar(canal_id: int):
    try:
        result = supabase.table("canais").delete().eq("id", canal_id).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verificar se é admin
@app.get("/admins/{user_id}")
def verificar_admin(user_id: int):
    try:
        data = supabase.table("admins").select("*").eq("id", user_id).execute().data
        return {"admin": len(data) > 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Upload de imagem para o Supabase Storage
@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        ext = file.filename.split(".")[-1]
        file_id = f"{uuid.uuid4()}.{ext}"
        content_type = file.content_type

        # Upload da imagem
        supabase.storage.from_(BUCKET).upload(file_id, file.file, {"content-type": content_type})

        # URL pública
        url = supabase.storage.from_(BUCKET).get_public_url(file_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
