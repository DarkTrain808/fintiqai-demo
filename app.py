from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import uuid
import json
import os
from fastapi.responses import HTMLResponse


DATA_FILE = "data.json"

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"issuers": [], "programmes": []}

def save_db(db):
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2, default=str)  # default=str handles dates


app = FastAPI(title="FintiqAI – Demo API", version="0.1.0")

# Store data in memory (will reset when server restarts)
DB = load_db()


# Data models
class Issuer(BaseModel):
    name: str
    ticker: Optional[str] = None
    market: Optional[str] = None

class Programme(BaseModel):
    issuer_id: str
    programme_name: str
    issue_date: date
    expiry_date: date
    strike_price: float
    total_warrants: int

# Routes
@app.post("/issuers")
def create_issuer(issuer: Issuer):
    new_issuer = issuer.dict()
    new_issuer["id"] = str(uuid.uuid4())
    DB["issuers"].append(new_issuer)
    save_db(DB)  # save to data.json
    return new_issuer


@app.get("/issuers")
def list_issuers():
    return DB["issuers"]

@app.post("/programmes")
def create_programme(prog: Programme):
    if not any(i["id"] == prog.issuer_id for i in DB["issuers"]):
        raise HTTPException(status_code=400, detail="Issuer not found")
    new_prog = prog.dict()
    new_prog["id"] = str(uuid.uuid4())
    DB["programmes"].append(new_prog)
    save_db(DB)  # save to data.json
    return new_prog


@app.get("/programmes")
def list_programmes():
    return DB["programmes"]@app.get("/everything")
def get_everything():
    return {
        "issuers": DB["issuers"],
        "programmes": DB["programmes"]
    }
@app.get("/everything")
def get_everything():
    return {
        "issuers": DB["issuers"],
        "programmes": DB["programmes"]
    }

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>FintiqAI – Demo</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; line-height: 1.4; }
    h1 { margin-bottom: 8px; }
    h2 { margin-top: 24px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    label { display:block; font-size: 12px; color:#444; margin-top: 8px; }
    input, select { width: 100%; padding: 8px; font-size: 14px; }
    button { margin-top: 12px; padding: 8px 12px; font-size: 14px; cursor: pointer; }
    pre { background:#f6f6f6; padding:12px; overflow:auto; }
    .card { border:1px solid #e5e5e5; border-radius: 10px; padding:16px; }
    .muted { color:#666; font-size:12px; }
  </style>
</head>
<body>
  <h1>FintiqAI – Demo</h1>
  <div class="muted">A tiny end-product: add issuers & programmes and view data.</div>

  <div class="grid" style="margin-top:16px;">
    <div class="card">
      <h2>Add Issuer</h2>
      <form id="issuerForm">
        <label>Name</label>
        <input id="issuer_name" required placeholder="SmarterWe Ltd">
        <label>Ticker</label>
        <input id="issuer_ticker" placeholder="SWC">
        <label>Market</label>
        <input id="issuer_market" placeholder="AQSE">
        <button type="submit">Create issuer</button>
      </form>
      <div id="issuerMsg" class="muted"></div>
    </div>

    <div class="card">
      <h2>Add Programme</h2>
      <form id="programmeForm">
        <label>Issuer</label>
        <select id="programme_issuer" required></select>
        <label>Programme name</label>
        <input id="programme_name" required placeholder="2025 Warrant Programme">
        <label>Issue date (YYYY-MM-DD)</label>
        <input id="issue_date" required placeholder="2025-08-11">
        <label>Expiry date (YYYY-MM-DD)</label>
        <input id="expiry_date" required placeholder="2028-08-11">
        <label>Strike price</label>
        <input id="strike_price" type="number" step="0.0001" required placeholder="0.15">
        <label>Total warrants</label>
        <input id="total_warrants" type="number" required placeholder="2000000">
        <button type="submit">Create programme</button>
      </form>
      <div id="programmeMsg" class="muted"></div>
    </div>
  </div>

  <h2 style="margin-top:28px;">Data</h2>
  <div class="grid">
    <div class="card">
      <h3>Issuers</h3>
      <pre id="issuersPre">Loading…</pre>
    </div>
    <div class="card">
      <h3>Programmes</h3>
      <pre id="programmesPre">Loading…</pre>
    </div>
  </div>

<script>
async function loadAll() {
  const r = await fetch('/everything');
  const data = await r.json();
  document.getElementById('issuersPre').textContent = JSON.stringify(data.issuers, null, 2);
  document.getElementById('programmesPre').textContent = JSON.stringify(data.programmes, null, 2);

  // populate issuer select
  const sel = document.getElementById('programme_issuer');
  sel.innerHTML = '';
  for (const issuer of data.issuers) {
    const opt = document.createElement('option');
    opt.value = issuer.id;
    opt.textContent = issuer.name + ' (' + (issuer.ticker || '—') + ')';
    sel.appendChild(opt);
  }
}

document.getElementById('issuerForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const body = {
    name: document.getElementById('issuer_name').value,
    ticker: document.getElementById('issuer_ticker').value || null,
    market: document.getElementById('issuer_market').value || null
  };
  const res = await fetch('/issuers', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
  const text = await res.text();
  document.getElementById('issuerMsg').textContent = res.ok ? 'Issuer created.' : 'Error: ' + text;
  await loadAll();
  e.target.reset();
});

document.getElementById('programmeForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const body = {
    issuer_id: document.getElementById('programme_issuer').value,
    programme_name: document.getElementById('programme_name').value,
    issue_date: document.getElementById('issue_date').value,
    expiry_date: document.getElementById('expiry_date').value,
    strike_price: Number(document.getElementById('strike_price').value),
    total_warrants: Number(document.getElementById('total_warrants').value)
  };
  const res = await fetch('/programmes', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
  const text = await res.text();
  document.getElementById('programmeMsg').textContent = res.ok ? 'Programme created.' : 'Error: ' + text;
  await loadAll();
  e.target.reset();
});

loadAll();
</script>
</body>
</html>
    """
