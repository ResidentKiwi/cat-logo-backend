from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import uuid
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://residentkiwi.github.io"], # ou especifique seu domínio exato
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "canais"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
class Canal(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str = None

@app.get("/canais")
async def listar_canais():
    try:
        data = supabase.table("canais").select("*").execute()
        return data.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/canais")
async def adicionar_canal(canal: Canal):
    try:
        res = supabase.table("canais").insert(canal.dict()).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/canais/{id}")
async def editar_canal(id: int, canal: Canal):
    try:
        res = supabase.table("canais").update(canal.dict()).eq("id", id).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/canais/{id}")
async def excluir_canal(id: int):
    try:
        supabase.table("canais").delete().eq("id", id).execute()
        return {"message": "Canal excluído com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admins/{user_id}")
def verificar_admin(user_id: int):
    response = supabase.table("admins").select("id").eq("id", user_id).execute()
    return {"admin": len(response.data) > 0}
    
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{file_ext}"
        file_content = await file.read()
        res = supabase.storage.from_(BUCKET).upload(filename, file_content)
        if hasattr(res, "status_code") and res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {res}")
        public_url = supabase.storage.from_(BUCKET).get_public_url(filename)
        return {"url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")
