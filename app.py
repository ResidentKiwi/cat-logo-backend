from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import io
from supabase import create_client, SupabaseClient

# ⛓️ Verifica variáveis de ambiente obrigatórias
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("As variáveis SUPABASE_URL e SUPABASE_KEY devem estar definidas.")

# 🔗 Conecta ao Supabase
supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# 🔓 CORS liberado para facilitar testes e integração com GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, idealmente especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📋 Modelo de canal
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

# 🔐 Verifica se o usuário é admin
@app.get("/admins")
async def get_admins():
    res = supabase.table("admins").select("id").execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao obter admins: {res.error}")
    return [row.get("id") for row in res.data]

# 📚 Lista todos os canais
@app.get("/channels")
async def get_channels():
    res = supabase.table("channels").select("*").execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao obter canais: {res.error}")
    return res.data

# 🔎 Pega um canal pelo ID
@app.get("/channels/{channel_id}")
async def get_channel(channel_id: int):
    res = supabase.table("channels").select("*").eq("id", channel_id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao obter canal: {res.error}")
    if not res.data:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return res.data[0]

# ➕ Cria novo canal
@app.post("/channels")
async def add_channel(channel: Channel):
    # Verifica se é admin
    res_admin = supabase.table("admins").select("id").eq("id", channel.user_id).execute()
    if not res_admin.data:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    # Insere canal
    res = supabase.table("channels").insert({
        "name": channel.name,
        "description": channel.description,
        "link": channel.link,
        "image": channel.image
    }).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao criar canal: {res.error}")
    return res.data[0]

# ✏️ Atualiza canal
@app.put("/channels/{channel_id}")
async def update_channel(channel_id: int, channel: ChannelUpdate):
    res_admin = supabase.table("admins").select("id").eq("id", channel.user_id).execute()
    if not res_admin.data:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    res = supabase.table("channels").update({
        "name": channel.name,
        "description": channel.description,
        "link": channel.link,
        "image": channel.image
    }).eq("id", channel_id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar canal: {res.error}")
    return res.data[0]

# ❌ Exclui canal
@app.delete("/channels/{channel_id}")
async def delete_channel(channel_id: int, user_id: int = Query(...)):
    res_admin = supabase.table("admins").select("id").eq("id", user_id).execute()
    if not res_admin.data:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    res = supabase.table("channels").delete().eq("id", channel_id).execute()
    if res.error:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir canal: {res.error}")
    return {"detail": "Canal excluído com sucesso"}

# 📤 Upload de imagem para Supabase Storage
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_name = f"channels/{int(time.time())}_{file.filename}"
        upload_res = supabase.storage.from_("canais").upload(
            file=io.BytesIO(content),
            path=file_name
        )
        if isinstance(upload_res, dict) and upload_res.get("error"):
            raise Exception(upload_res["error"])
        public_url = supabase.storage.from_("canais").get_public_url(file_name).get("publicURL")
        return {"url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload da imagem: {str(e)}")
