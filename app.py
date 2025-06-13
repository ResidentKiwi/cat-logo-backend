from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import io
from supabase import create_client
from postgrest.exceptions import APIError

# Carregar variáveis de ambiente (sem fallback, obrigatório no Render)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_KEY devem estar definidas.")

# Inicializar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# CORS (ajustar domínio do frontend em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/admins")
async def get_admins():
    try:
        res = supabase.table("admins").select("id").execute()
        return [row.get("id") for row in res]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter admins: {e}")

class Channel(BaseModel):
    name: str
    description: str
    link: str
    image: str
    user_id: int

class ChannelUpdate(BaseModel):
    name: str
    description: str
    link: str
    image: str
    user_id: int

@app.get("/channels")
async def get_channels():
    try:
        res = supabase.table("channels").select("*").execute()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter canais: {e}")

@app.get("/channels/{channel_id}")
async def get_channel(channel_id: int):
    try:
        res = supabase.table("channels").select("*").eq("id", channel_id).execute()
        if not res:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        return res[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter canal: {e}")

@app.post("/channels")
async def add_channel(channel: Channel):
    try:
        admins = supabase.table("admins").select("id").eq("id", channel.user_id).execute()
        if not admins:
            raise HTTPException(status_code=403, detail="Usuário não autorizado")

        res = supabase.table("channels").insert({
            "name": channel.name,
            "description": channel.description,
            "link": channel.link,
            "image": channel.image
        }).execute()
        return res[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar canal: {e}")

@app.put("/channels/{channel_id}")
async def update_channel(channel_id: int, channel: ChannelUpdate):
    try:
        admins = supabase.table("admins").select("id").eq("id", channel.user_id).execute()
        if not admins:
            raise HTTPException(status_code=403, detail="Usuário não autorizado")

        res = supabase.table("channels").update({
            "name": channel.name,
            "description": channel.description,
            "link": channel.link,
            "image": channel.image
        }).eq("id", channel_id).execute()
        return res[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar canal: {e}")

@app.delete("/channels/{channel_id}")
async def delete_channel(channel_id: int, user_id: int = Query(...)):
    try:
        admins = supabase.table("admins").select("id").eq("id", user_id).execute()
        if not admins:
            raise HTTPException(status_code=403, detail="Usuário não autorizado")

        supabase.table("channels").delete().eq("id", channel_id).execute()
        return {"detail": "Canal excluído com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir canal: {e}")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_name = f"channels/{int(time.time())}_{file.filename}"
        supabase.storage.from_("canais").upload(
            file=io.BytesIO(content),
            path=file_name
        )
        public_res = supabase.storage.from_("canais").get_public_url(file_name)
        public_url = public_res.get("publicURL") or public_res.get("publicUrl")
        return {"url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload da imagem: {e}")
