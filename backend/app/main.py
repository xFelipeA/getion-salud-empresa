# main.py
import os
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
import httpx
from supabase_client import supabase

app = FastAPI()

SUPABASE_URL = os.environ.get("SUPABASE_URL")  # ex: https://abc.supabase.co
SUPABASE_AUTH_REST = f"{SUPABASE_URL}/auth/v1/user"

# ---------- Helpers ----------
async def get_user_from_token(token: str):
    """
    Verifica token no Supabase Auth REST.
    Retorna objeto user (json) ou levanta HTTPException(401).
    """
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(SUPABASE_AUTH_REST, headers=headers)
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")
    return r.json()

# ---------- Models ----------
class NotificacaoCreate(BaseModel):
    usuario_destino: str  # uuid
    mensagem: str

class AtividadeCreate(BaseModel):
    acao: str
    detalhes: str | None = None

# ---------- Endpoints ----------
@app.post("/notificacoes")
async def criar_notificacao(payload: NotificacaoCreate, authorization: str | None = Header(None)):
    # header Authorization: Bearer <token>
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split("Bearer ")[-1]
    user = await get_user_from_token(token)
    usuario_origem = user.get("id")
    # Insert into table 'notificacoes'
    data = {
        "usuario_destino": payload.usuario_destino,
        "usuario_origem": usuario_origem,
        "mensagem": payload.mensagem,
        "lida": False
    }
    resp = supabase.table("notificacoes").insert(data).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=str(resp.error))
    # Log activity
    supabase.table("atividades").insert({
        "usuario_id": usuario_origem,
        "acao": "criou_notificacao",
        "detalhes": payload.mensagem
    }).execute()
    return {"ok": True, "data": resp.data}

@app.get("/notificacoes")
async def listar_notificacoes(authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split("Bearer ")[-1]
    user = await get_user_from_token(token)
    uid = user.get("id")
    resp = supabase.table("notificacoes").select("*").eq("usuario_destino", uid).order("criada_em", desc=True).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=str(resp.error))
    return {"notificacoes": resp.data}

@app.post("/atividades")
async def criar_atividade(payload: AtividadeCreate, authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split("Bearer ")[-1]
    user = await get_user_from_token(token)
    uid = user.get("id")
    resp = supabase.table("atividades").insert({
        "usuario_id": uid,
        "acao": payload.acao,
        "detalhes": payload.detalhes
    }).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=str(resp.error))
    return {"ok": True, "data": resp.data}

@app.get("/perfis/me")
async def meu_perfil(authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.split("Bearer ")[-1]
    user = await get_user_from_token(token)
    uid = user.get("id")
    # buscar na tabela perfis o role
    resp = supabase.table("perfis").select("*").eq("user_id", uid).limit(1).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=str(resp.error))
    if not resp.data:
        return {"role": None}
    return {"role": resp.data[0].get("role")}
