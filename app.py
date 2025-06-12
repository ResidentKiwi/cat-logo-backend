from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import supabase

app = FastAPI()

# CORS para permitir acesso do GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Idealmente, especifique seu domínio exato
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa cliente Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

class Canal(BaseModel):
    nome: str
    descricao: str
    url: str
    imagem: str

@app.get("/canais")
def listar_canais():
    res = supabase_client.table("canais").select("*").order("id", desc=True).execute()
    return res.data

@app.post("/canais")
def adicionar_canal(canal: Canal):
    res = supabase_client.table("canais").insert([canal.dict()]).execute()
    return res.data

@app.get("/admins/{user_id}")
def verificar_admin(user_id: int):
    res = supabase_client.table("admins").select("*").eq("id", user_id).execute()
    return {"admin": len(res.data) > 0}
