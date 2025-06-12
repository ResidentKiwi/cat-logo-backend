from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
import os
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET = "imagens"

class Canal(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str = None

@app.get("/canais")
def listar():
    return supabase.table("canais").select("*").order("id", desc=True).execute().data

@app.post("/canais")
def criar(canal: Canal):
    return supabase.table("canais").insert(canal.dict()).execute().data

@app.put("/canais/{canal_id}")
def atualizar(canal_id: int, canal: dict):
    return supabase.table("canais").update(canal).eq("id", canal_id).execute().data

@app.delete("/canais/{canal_id}")
def deletar(canal_id: int):
    return supabase.table("canais").delete().eq("id", canal_id).execute().data

@app.get("/admins/{user_id}")
def verificar_admin(user_id: int):
    data = supabase.table("admins").select("*").eq("id", user_id).execute().data
    return {"admin": len(data) > 0}

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    file_id = f"{uuid.uuid4()}.{ext}"
    supabase.storage.from_(BUCKET).upload(file_id, file.file, {"content-type": file.content_type})
    url = supabase.storage.from_(BUCKET).get_public_url(file_id)
    return {"url": url}
