from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
import cv2
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

camera_sources = {
    "cam1": "http://172.20.10.3:8080/video",
    "cam2": "http://172.20.10.4:8080/video",
    "cam3": "http://192.168.51.58:8080/video",
    "cam4": "http://172.20.10.2:8080/video",
}

# -----------------------------------------------------------------------------
### NUEVO: Almacén de estado para las alertas de cada cámara
# Creamos un diccionario para guardar si cada cámara tiene una amenaza activa.
# Se inicializa con todas las cámaras en False (sin amenaza).
alert_status = {cam_id: False for cam_id in camera_sources.keys()}


# -----------------------------------------------------------------------------


@app.post("/alert/{cam_id}")
async def receive_alert(cam_id: str, alert_data: dict):
    """
    Este endpoint es el "buzón" para el script detector.py.
    Cuando recibe una alerta, la imprime y ACTUALIZA el estado de la alarma.
    """
    threat = alert_data.get('threat', False)
    level = alert_data.get('level', 'NONE')
    message = alert_data.get('message', 'Sin información')
    timestamp = time.strftime('%H:%M:%S')

    # -----------------------------------------------------------------------------
    ### MODIFICADO: Actualizar el estado de la alarma global
    if cam_id in alert_status:
        alert_status[cam_id] = threat  # Actualizamos el estado para esta cámara específica
    # -----------------------------------------------------------------------------

    if threat:
        print("-----------------------------------------")
        print(f"🚨 ALERTA RECIBIDA [{timestamp}] 🚨")
        print(f"    Cámara: {cam_id}")
        print(f"    Nivel de Riesgo: {level}")
        print(f"    Mensaje: {message}")
        print("-----------------------------------------")
        return {"status": "alert_received", "cam_id": cam_id}
    else:
        print(f"✅ Amenaza despejada en {cam_id} a las {timestamp}")
        return {"status": "threat_cleared", "cam_id": cam_id}


# -----------------------------------------------------------------------------
### NUEVO: Ruta para consultar el estado general de la alarma
@app.get("/alarma/deactivate")
async def get_alarm_status():
    """
    Devuelve un booleano que representa el estado general de la alarma.
    Será True si CUALQUIER cámara tiene una amenaza activa.
    Será False solo si TODAS las cámaras están sin amenazas.
    """
    # La función any() devuelve True si al menos un elemento de la lista es True.
    for cam_id in alert_status:
        alert_status[cam_id] = False
    print("🔕 Todas las alarmas han sido desactivadas manualmente.")
    return {"alarma_activa": False, "estado_camaras": alert_status}
@app.get("/alarma")
async def get_alarm_status():
    """
    Devuelve un booleano que representa el estado general de la alarma.
    Será True si CUALQUIER cámara tiene una amenaza activa.
    Será False solo si TODAS las cámaras están sin amenazas.
    """
    # La función any() devuelve True si al menos un elemento de la lista es True.
    is_alarm_active = any(alert_status.values())

    # Devolvemos el resultado en un JSON para que sea fácil de consumir por otras apps.
    return {"alarma_activa": is_alarm_active}


# -----------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "cam_ids": camera_sources.keys()})


def generate_frames(camera_url):
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"No se pudo conectar a {camera_url}")
        return
    while True:
        success, frame = cap.read()
        if not success:
            cap.release()
            cap = cv2.VideoCapture(camera_url)
            continue
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")


@app.get("/video_feed/{cam_id}")
async def video_feed(cam_id: str):
    if cam_id not in camera_sources:
        return HTMLResponse(f"ID de cámara inválido: {cam_id}", status_code=404)
    return StreamingResponse(
        generate_frames(camera_sources[cam_id]),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )