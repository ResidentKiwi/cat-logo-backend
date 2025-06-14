from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, time
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

class Canal(BaseModel):
    nome: str
    url: str
    descricao: str | None = None
    imagem: str
    user_id: int

class CanalUpdate(BaseModel):
    nome: str
    url: str
    descricao: str | None = None
    imagem: str
    user_id: int

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

@app.post("/canais")
async def adicionar_canal(canal: Canal):
    try:
        print("📥 POST /canais recebido:", canal.dict())
        admin_check = supabase.table("admins").select("id").eq("id", canal.user_id).execute()
        if not admin_check.data:
            raise HTTPException(403, "Usuário não autorizado")
        data = {
            "nome": canal.nome,
            "url": canal.url,
            "descricao": canal.descricao or "",
            "imagem": canal.imagem
        }
        res = supabase.table("canais").insert(data).execute()
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erro ao criar canal: {e}")

@app.put("/canais/{canal_id}")
async def atualizar_canal(canal_id: int, canal: CanalUpdate):
    try:
        admin_check = supabase.table("admins").select("id").eq("id", canal.user_id).execute()
        if not admin_check.data:
            raise HTTPException(403, "Usuário não autorizado")
        res = supabase.table("canais").update({
            "nome": canal.nome,
            "url": canal.url,
            "descricao": canal.descricao,
            "imagem": canal.imagem
        }).eq("id", canal_id).execute()
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erro ao atualizar canal: {e}")

@app.delete("/canais/{canal_id}")
async def excluir_canal(canal_id: int, user_id: int = Query(...)):
    try:
        admin_check = supabase.table("admins").select("id").eq("id", user_id).execute()
        if not admin_check.data:
            raise HTTPException(403, "Usuário não autorizado")
        supabase.table("canais").delete().eq("id", canal_id).execute()
        return {"detail": "Canal excluído com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erro ao excluir canal: {e}")

@app.post("/upload")
async def upload_imagem(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_name = f"canais/{int(time.time())}_{file.filename}"
        supabase.storage.from_("canais").upload(file_name, content)  # ✅ Correção aqui
        public_res = supabase.storage.from_("canais").get_public_url(file_name)
        url = public_res.get("publicURL") or public_res.get("publicUrl")
        return {"url": url}
    except Exception as e:
        raise HTTPException(500, f"Erro no upload da imagem: {e}")
