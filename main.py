import os
import json
import time
import asyncio
import logging
import csv
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin, ModelView
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import paho.mqtt.client as mqtt

# --- 1. CONFIGURAÇÃO DE CAMINHOS ---
BASE_APP_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_APP_DIR, "templates")

# Configuração de Logs e Banco
DB_URL = "sqlite:///logger.db"
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
LOG_DIR_NAME = "testes"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Logger")

# --- 2. BANCO DE DADOS ---
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Embarcado(Base):
    __tablename__ = "embarcados"
    id = Column(Integer, primary_key=True)
    id_esp = Column(String, unique=True, nullable=False)
    descricao = Column(String, nullable=True)
    def __str__(self): return self.id_esp

class Ativo(Base):
    __tablename__ = "ativos"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    mac_beacon = Column(String, unique=True, nullable=False)
    def __str__(self): return f"{self.nome} ({self.mac_beacon})"

Base.metadata.create_all(engine)

# --- 3. ESTADO GLOBAL DO GRAVADOR ---
RECORDER_STATE = {
    "is_recording": False,
    "test_name": "",
    "description": "",
    "selected_esps": [],
    "selected_assets": [],
    "start_time_str": None,
    "start_dt_obj": None
}

# --- 4. LÓGICA DE GRAVAÇÃO CSV ---
def save_to_file(esp_id, beacon_mac, rssi, wifi_signal):
    if not RECORDER_STATE["is_recording"]:
        return

    if esp_id not in RECORDER_STATE["selected_esps"]:
        return
    
    beacon_mac_norm = beacon_mac.lower()
    selected_assets_norm = [m.lower() for m in RECORDER_STATE["selected_assets"]]
    
    if beacon_mac_norm not in selected_assets_norm:
        return

    safe_test_name = "".join([c if c.isalnum() else "_" for c in RECORDER_STATE["test_name"]])
    safe_mac_filename = beacon_mac_norm.replace(":", "-") + ".csv"
    
    # Caminho: ./testes/NomeDoTeste/ID_ESP/
    dir_path = os.path.join(".", LOG_DIR_NAME, safe_test_name, esp_id)
    # A pasta já foi criada no start, mas garantimos aqui caso apaguem durante o teste
    os.makedirs(dir_path, exist_ok=True)
    
    file_path = os.path.join(dir_path, safe_mac_filename)
    file_exists = os.path.isfile(file_path)
    
    try:
        with open(file_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "datetime", "rssi", "wifi"])
            
            now = datetime.now()
            writer.writerow([
                time.time(), 
                now.strftime("%Y-%m-%d %H:%M:%S.%f"), 
                rssi, 
                wifi_signal
            ])
            
    except Exception as e:
        logger.error(f"Erro ao gravar arquivo: {e}")

# --- 5. MQTT ---
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    logger.info(f"Conectado ao MQTT (RC: {rc}).")
    client.subscribe("wyrd/rtls/esp/+/scan_data")

def on_message(client, userdata, msg):
    try:
        parts = msg.topic.split('/')
        if len(parts) < 4: return
        
        esp_id = parts[3]
        payload = json.loads(msg.payload)
        wifi_signal = payload.get("w", "")
        beacons = payload.get("b", {})
        
        for mac, rssi in beacons.items():
            save_to_file(esp_id, mac, rssi, wifi_signal)

    except Exception as e:
        pass

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    import time
    time.sleep(1) # Espera 1 segundinho para garantir a conexão
    # Manda o comando para o tópico geral que todas as ESPs escutam
    client.publish("wyrd/rtls/esp/all/command", json.dumps({"command": "fetch_config"}))
    logger.info("📢 Comando de atualização de Whitelist enviado para todas as ESPs!")
except Exception as e:
    logger.error(f"ERRO MQTT: {e}")

# --- 6. APP FASTAPI ---
app = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)
admin = Admin(app, engine)

# --- 7. ADMIN ---
class EmbarcadoAdmin(ModelView, model=Embarcado):
    column_list = [Embarcado.id_esp, Embarcado.descricao]
    icon = "fa-solid fa-microchip"

class AtivoAdmin(ModelView, model=Ativo):
    column_list = [Ativo.nome, Ativo.mac_beacon]
    icon = "fa-solid fa-tag"

admin.add_view(EmbarcadoAdmin)
admin.add_view(AtivoAdmin)

# --- 8. ROTAS ---

@app.get("/")
def index(request: Request, error: Optional[str] = None):
    db = SessionLocal()
    esps = db.query(Embarcado).all()
    ativos = db.query(Ativo).all()
    db.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "esps": esps,
        "ativos": ativos,
        "state": RECORDER_STATE,
        "error": error  # Passa o erro para o template exibir
    })

@app.post("/start")
async def start_recording(
    request: Request,
    test_name: str = Form(...),
    description: str = Form(""),
    esps: List[str] = Form([]),
    ativos: List[str] = Form([])
):
    if not test_name:
        return RedirectResponse("/", status_code=303)
        
    # --- TRAVA DE NOME DUPLICADO ---
    safe_test_name = "".join([c if c.isalnum() else "_" for c in test_name])
    path = os.path.join(".", LOG_DIR_NAME, safe_test_name)
    
    if os.path.exists(path):
        logger.warning(f"Tentativa de criar teste duplicado: {test_name}")
        # Redireciona de volta com aviso de erro
        return RedirectResponse("/?error=duplicate", status_code=303)
    # -------------------------------

    now = datetime.now()
    
    RECORDER_STATE["is_recording"] = True
    RECORDER_STATE["test_name"] = test_name
    RECORDER_STATE["description"] = description
    RECORDER_STATE["selected_esps"] = esps
    RECORDER_STATE["selected_assets"] = ativos
    RECORDER_STATE["start_time_str"] = now.strftime("%H:%M:%S")
    RECORDER_STATE["start_dt_obj"] = now
    
    # Cria a pasta e o arquivo inicial
    os.makedirs(path, exist_ok=True)
    
    with open(os.path.join(path, "info.txt"), "w") as f:
        f.write("=== DADOS DO TESTE ===\n")
        f.write(f"Teste: {test_name}\n")
        f.write(f"Descricao: {description}\n")
        f.write(f"Data: {now.strftime('%d/%m/%Y')}\n")
        f.write(f"Inicio: {RECORDER_STATE['start_time_str']}\n")
        f.write("-" * 20 + "\n")
        f.write(f"ESPs Monitoradas ({len(esps)}): {', '.join(esps)}\n")
        f.write(f"Ativos Monitorados ({len(ativos)}): {', '.join(ativos)}\n")
        f.write("-" * 20 + "\n")
        f.write("Aguardando finalizacao...\n")
    
    logger.info(f"GRAVAÇÃO INICIADA: {test_name}")
    return RedirectResponse("/", status_code=303)

@app.post("/stop")
def stop_recording():
    if not RECORDER_STATE["is_recording"]:
        return RedirectResponse("/", status_code=303)

    end_time = datetime.now()
    start_time = RECORDER_STATE["start_dt_obj"]
    duration = end_time - start_time
    duration_str = str(duration).split('.')[0]

    safe_test_name = "".join([c if c.isalnum() else "_" for c in RECORDER_STATE["test_name"]])
    path = os.path.join(".", LOG_DIR_NAME, safe_test_name, "info.txt")

    if os.path.exists(path):
        with open(path, "a") as f:
            f.write(f"Fim: {end_time.strftime('%H:%M:%S')}\n")
            f.write(f"Duracao Total: {duration_str}\n")
            f.write("=== FIM ===\n")

    RECORDER_STATE["is_recording"] = False
    logger.info(f"GRAVAÇÃO PARADA. Duração: {duration_str}")
    
    return RedirectResponse("/", status_code=303)

@app.get("/api/esp/handshake")
def handshake(id_esp: str):
    db = SessionLocal()
    esp_existe = db.query(Embarcado).filter(Embarcado.id_esp == id_esp).first()
    if not esp_existe:
        db.add(Embarcado(id_esp=id_esp, descricao="Auto-detectada"))
        db.commit()

    ativos = db.query(Ativo).all()
    whitelist = [a.mac_beacon for a in ativos]
    db.close()
    return {"whitelist": whitelist}

@app.get("/api/time")
def server_time():
    return {"unix_time": int(time.time())}