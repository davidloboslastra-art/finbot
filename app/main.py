from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

from .bot import responder

app = FastAPI(title="Finbot")


class Entrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    mensaje: str = Field(min_length=1, max_length=1000)


class Salida(BaseModel):
    respuesta: str
    fuente: str


@app.get("/health")
def health():
    return {"status": "ok"}


# def (no async): la llamada a OpenAI bloquea y así corre en el threadpool.
@app.post("/chat", response_model=Salida)
def chat(entrada: Entrada):
    return responder(entrada.mensaje)


PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Finbot</title>
<style>
body{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem}
#log{border:1px solid #ccc;border-radius:8px;padding:.75rem;height:55vh;overflow:auto}
.u{text-align:right;color:#333}.b{white-space:pre-wrap;margin:.5rem 0}.f{font-size:.75rem;color:#888}
form{display:flex;gap:.5rem;margin-top:.75rem}input{flex:1;padding:.5rem}
</style></head><body>
<h1>Finbot</h1><p>Educación financiera para Chile.</p>
<div id="log"></div>
<form id="f"><input id="m" placeholder="Ej: cuota de $10 millones al 12% a 36 meses" autocomplete="off"><button>Enviar</button></form>
<script>
const log=document.getElementById('log');
function add(c,t,f){const d=document.createElement('div');d.className=c;d.textContent=t;
 if(f){const s=document.createElement('div');s.className='f';s.textContent='fuente: '+f;d.appendChild(s)}
 log.appendChild(d);log.scrollTop=log.scrollHeight}
document.getElementById('f').onsubmit=async e=>{e.preventDefault();
 const i=document.getElementById('m'),mensaje=i.value.trim();if(!mensaje)return;
 add('u mb',mensaje);i.value='';
 try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensaje})});
  const j=await r.json();add('b',j.respuesta,j.fuente)}catch{add('b','Error de conexión.')}};
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def inicio():
    return PAGINA
