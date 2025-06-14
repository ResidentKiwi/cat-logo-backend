from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, time
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

class Canal(BaseModel):
    nome: str
    url: str
    descricao: str | None = None
    imagem: str
    user_id: int

@app.get("/admins")
async def get_admins():
    res = supabase.table("admins").select("id").execute()
    return [r["id"] for r in res.data]

@app.get("/devs")
async def get_devs():
    res = supabase.table("devs").select("id").execute()
    return [r["id"] for r in res.data]

@app.post("/admins")
async def add_admin(payload: dict = Body(...)):
    admin_id = payload.get("user_id")
    novo = payload.get("novo_admin")
    devs = supabase.table("devs").select("id").eq("id", admin_id).execute()
    if not devs.data:
        raise HTTPException(403, "Somente dev pode adicionar admin")
    supabase.table("admins").insert({"id": novo}).execute()
    return {"status": "ok"}

@app.delete("/admins")
async def remove_admin(user_id: int = Query(...), remove_admin: int = Query(...)):
    devs = supabase.table("devs").select("id").eq("id", user_id).execute()
    if not devs.data:
        raise HTTPException(403, "Somente dev pode remover")
    supabase.table("admins").delete().eq("id", remove_admin).execute()
    return {"status": "ok"}

@app.get("/canais")
async def get_canais():
    res = supabase.table("canais").select("*").execute()
    return res.data

@app.post("/canais")
async def add_canal(c: Canal):
    admins = supabase.table("admins").select("id").eq("id", c.user_id).execute()
    if not admins.data:
        raise HTTPException(403, "Forbidden")
    r = supabase.table("canais").insert(c.dict(exclude={"user_id"})).execute()
    cid = r.data[0]["id"]
    supabase.table("admin_logs").insert({
        "admin_id": c.user_id,
        "action": "created_channel",
        "target_id": cid
    }).execute()
    return r.data[0]

@app.put("/canais/{cid}")
async def update_canal(cid: int, c: Canal):
    admins = supabase.table("admins").select("id").eq("id", c.user_id).execute()
    if not admins.data:
        raise HTTPException(403, "Forbidden")
    supabase.table("canais").update(c.dict(exclude={"user_id"})).eq("id", cid).execute()
    supabase.table("admin_logs").insert({
        "admin_id": c.user_id,
        "action": "updated_channel",
        "target_id": cid
    }).execute()
    return {"status": "ok"}

@app.delete("/canais/{cid}")
async def delete_canal(cid: int, user_id: int = Query(...)):
    admins = supabase.table("admins").select("id").eq("id", user_id).execute()
    if not admins.data:
        raise HTTPException(403, "Forbidden")
    supabase.table("canais").delete().eq("id", cid).execute()
    supabase.table("admin_logs").insert({
        "admin_id": user_id,
        "action": "deleted_channel",
        "target_id": cid
    }).execute()
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    path = f"canais/{int(time.time())}_{file.filename}"
    supabase.storage.from_("canais") \
      .upload(path=path, file=content, file_options={"content-type": file.content_type})
    url = supabase.storage.from_("canais").get_public_url(path)
    return {"url": url.get("publicURL") or url.get("publicUrl")}

@app.get("/admin_logs")
async def get_logs(user_id: int = Query(...)):
    res = supabase.table("admin_logs").select("*") \
      .eq("admin_id", user_id).order("timestamp", desc=True).execute()
    return res.data
