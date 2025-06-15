from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, time
from supabase import create_client

# Configuração Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DEV_ID = 5185766186  # Seu ID fixo como desenvolvedor

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

# Utilitário: Verifica se o user é admin ou dev
def is_manage(user_id: int) -> bool:
    if user_id == DEV_ID:
        return True
    admins = supabase.table("admins").select("id").execute().data or []
    return any(r["id"] == user_id for r in admins)

# Modelos
class Canal(BaseModel):
    nome: str
    url: str
    descricao: str | None = None
    imagem: str
    user_id: int

class CanalUpdate(Canal):
    pass

# Rotas básicas
@app.get("/admins")
async def get_admins():
    try:
        res = supabase.table("admins").select("id").execute()
        return [r["id"] for r in res.data]
    except Exception as e:
        raise HTTPException(500, f"Erro ao obter admins: {e}")

@app.get("/canais")
async def get_canais():
    try:
        res = supabase.table("canais").select("*").execute()
        return res.data
    except Exception as e:
        raise HTTPException(500, f"Erro ao obter canais: {e}")

# CRUD de canais com logs
@app.post("/canais")
async def adicionar_canal(canal: Canal):
    if not is_manage(canal.user_id):
        raise HTTPException(403, "Usuário não autorizado")
    try:
        res = supabase.table("canais").insert({
            "nome": canal.nome,
            "url": canal.url,
            "descricao": canal.descricao or "",
            "imagem": canal.imagem
        }).execute()
        canal_id = res.data[0]["id"]
        supabase.table("admin_logs").insert({
            "admin_id": canal.user_id,
            "action": "created_channel",
            "target_id": canal_id
        }).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(500, f"Erro ao criar canal: {e}")

@app.put("/canais/{canal_id}")
async def atualizar_canal(canal_id: int, canal: CanalUpdate):
    if not is_manage(canal.user_id):
        raise HTTPException(403, "Usuário não autorizado")
    try:
        res = supabase.table("canais").update({
            "nome": canal.nome,
            "url": canal.url,
            "descricao": canal.descricao,
            "imagem": canal.imagem
        }).eq("id", canal_id).execute()
        supabase.table("admin_logs").insert({
            "admin_id": canal.user_id,
            "action": "updated_channel",
            "target_id": canal_id
        }).execute()
        return res.data[0]
    except Exception as e:
        raise HTTPException(500, f"Erro ao atualizar canal: {e}")

@app.delete("/canais/{canal_id}")
async def excluir_canal(canal_id: int, user_id: int = Query(...)):
    if not is_manage(user_id):
        raise HTTPException(403, "Usuário não autorizado")
    try:
        supabase.table("canais").delete().eq("id", canal_id).execute()
        supabase.table("admin_logs").insert({
            "admin_id": user_id,
            "action": "deleted_channel",
            "target_id": canal_id
        }).execute()
        return {"detail": "Canal excluído com sucesso"}
    except Exception as e:
        raise HTTPException(500, f"Erro ao excluir canal: {e}")

# Upload de imagem
@app.post("/upload")
async def upload_imagem(file: UploadFile = File(...)):
    try:
        content = await file.read()
        if not content:
            raise Exception("Arquivo está vazio")
        path = f"canais/{int(time.time())}_{file.filename}"
        supabase.storage.from_("canais").upload(
            path=path,
            file=content,
            file_options={"content-type": file.content_type}
        )
        public_url = supabase.storage.from_("canais").get_public_url(path)
        return {"url": public_url.get("publicURL") or public_url.get("publicUrl")}
    except Exception as e:
        raise HTTPException(500, f"Erro no upload da imagem: {e}")

# Logs — somente você (dev) pode acessar
@app.get("/admin_logs")
async def get_logs(user_id: int = Query(...)):
    if user_id != DEV_ID:
        raise HTTPException(403, "Acesso restrito")
    try:
        res = supabase.table("admin_logs").select("*").order("timestamp", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(500, f"Erro ao obter logs: {e}")

# Painel dev: gerenciamento de admins
@app.get("/dev/admins")
async def list_admins_dev(user_id: int = Query(...)):
    if user_id != DEV_ID:
        raise HTTPException(403, "Somente o desenvolvedor pode acessar.")
    try:
        res = supabase.table("admins").select("id").execute()
        return [r["id"] for r in res.data]
    except Exception as e:
        raise HTTPException(500, f"Erro ao listar admins: {e}")

@app.post("/dev/admins")
async def add_admin(new_id: int = Query(...), user_id: int = Query(...)):
    if user_id != DEV_ID:
        raise HTTPException(403, "Somente o desenvolvedor pode adicionar admins.")
    try:
        supabase.table("admins").insert({"id": new_id}).execute()
        return {"added": new_id}
    except Exception as e:
        raise HTTPException(500, f"Erro ao adicionar admin: {e}")

@app.delete("/dev/admins")
async def remove_admin(del_id: int = Query(...), user_id: int = Query(...)):
    if user_id != DEV_ID:
        raise HTTPException(403, "Somente o desenvolvedor pode remover admins.")
    try:
        supabase.table("admins").delete().eq("id", del_id).execute()
        return {"deleted": del_id}
    except Exception as e:
        raise HTTPException(500, f"Erro ao remover admin: {e}")
