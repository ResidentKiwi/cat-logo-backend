from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import io
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Variáveis SUPABASE_URL e SUPABASE_KEY devem estar definidas.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/admins")
async def get_admins():
    res = supabase.table("admins").select("id").execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao obter admins: {res.error}")
    return [row.get("id") for row in res.data]

class Channel(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str
    user_id: int

class ChannelUpdate(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str
    user_id: int

@app.get("/channels")
async def get_channels():
    res = supabase.table("channels").select("*").execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao obter canais: {res.error}")
    return res.data

@app.get("/channels/{channel_id}")
async def get_channel(channel_id: int):
    res = supabase.table("channels").select("*").eq("id", channel_id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao obter canal: {res.error}")
    if not res.data:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return res.data[0]

@app.post("/channels")
async def add_channel(channel: Channel):
    res_admin = supabase.table("admins").select("id").eq("id", channel.user_id).execute()
    if res_admin.error:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar admin: {res_admin.error}")
    if not res_admin.data:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    try:
        res = supabase.table("channels").insert({
            "nome": channel.nome,
            "descricao": channel.descricao,
            "url": channel.url,
            "imagem": channel.imagem
        }).execute()
        if res.error:
            raise Exception(res.error)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar canal: {e}")
    return res.data[0]

@app.put("/channels/{channel_id}")
async def update_channel(channel_id: int, channel: ChannelUpdate):
    res_admin = supabase.table("admins").select("id").eq("id", channel.user_id).execute()
    if res_admin.error:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar admin: {res_admin.error}")
    if not res_admin.data:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    try:
        res = supabase.table("channels").update({
            "nome": channel.nome,
            "descricao": channel.descricao,
            "url": channel.url,
            "imagem": channel.imagem
        }).eq("id", channel_id).execute()
        if res.error:
            raise Exception(res.error)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar canal: {e}")
    return res.data[0]

@app.delete("/channels/{channel_id}")
async def delete_channel(channel_id: int, user_id: int = Query(...)):
    res_admin = supabase.table("admins").select("id").eq("id", user_id).execute()
    if res_admin.error:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar admin: {res_admin.error}")
    if not res_admin.data:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    try:
        res = supabase.table("channels").delete().eq("id", channel_id).execute()
        if res.error:
            raise Exception(res.error)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir canal: {e}")
    return {"detail": "Canal excluído com sucesso"}

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_name = f"channels/{int(time.time())}_{file.filename}"
        res = supabase.storage.from_("canais").upload(
            file=io.BytesIO(content),
            path=file_name
        )
        if isinstance(res, dict) and res.get("error"):
            raise Exception(res["error"])
        public_res = supabase.storage.from_("canais").get_public_url(file_name)
        public_url = public_res.get("publicURL") or public_res.get("publicUrl")
        return {"url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload da imagem: {e}")
