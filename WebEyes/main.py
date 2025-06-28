from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
import cv2

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Permitir conexiones externas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mapea cam_id con la URL de la cámara IP
camera_sources = {
    "cam1": "http://10.10.33.125:8080/video",  # Cambia IP según cada celular
    "cam2": "http://10.10.33.126:8080/video",
    "cam3": "http://192.168.51.58:8080/video",
    "cam4": "http://10.55.131.39:8080/video",
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def generate_frames(camera_url):
    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"No se pudo conectar a {camera_url}")
        return

    while True:
        success, frame = cap.read()
        if not success:
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
