from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

# -------- MODELOS --------
class Canal(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str

class CanalUpdate(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str | None = None

# -------- ROTAS --------

@app.get("/")
def read_root():
    return {"status": "API no ar"}

@app.get("/canais")
def listar_canais():
    res = supabase.table("canais").select("*").order("id", desc=True).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data

@app.post("/canais")
def adicionar_canal(canal: Canal):
    res = supabase.table("canais").insert(canal.dict()).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data

@app.put("/canais/{id}")
def atualizar_canal(id: int, canal: CanalUpdate):
    body = {k: v for k, v in canal.dict().items() if v is not None}
    res = supabase.table("canais").update(body).eq("id", id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return res.data

@app.delete("/canais/{id}")
def deletar_canal(id: int):
    res = supabase.table("canais").delete().eq("id", id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return {"status": "Canal removido com sucesso"}

@app.get("/admins/{id}")
def verificar_admin(id: int):
    res = supabase.table("admins").select("*").eq("id", id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=res.error.message)
    return {"admin": len(res.data) > 0}

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(status_code=400, detail="Formato de imagem não suportado.")

        file_id = f"{uuid.uuid4()}.{ext}"
        content_type = file.content_type or "image/jpeg"
        conteudo = file.file.read()

        response = supabase.storage.from_(BUCKET).upload(
            file_id,
            conteudo,
            {"content-type": content_type},
            upsert=True
        )

        if hasattr(response, "error") and response.error:
            raise HTTPException(status_code=500, detail=f"Erro no upload: {response.error}")

        url = supabase.storage.from_(BUCKET).get_public_url(file_id)
        return {"url": url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")
