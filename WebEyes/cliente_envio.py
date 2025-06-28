import cv2
import requests
import time
import gc

# Dirección del video IP Webcam
ip_webcam_url = "http://10.55.131.39:8080/video"

# Dirección de tu servidor FastAPI
fastapi_url = "http://192.168.51.166:8000/upload/cam1"  # Ajusta esta IP

def main():
    cap = cv2.VideoCapture(ip_webcam_url)

    if not cap.isOpened():
        print("❌ No se pudo conectar a IP Webcam")
        return
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ No se pudo leer el frame")
                time.sleep(0.2)
                continue
            # Codificar la imagen como JPEG
            ret2, img_encoded = cv2.imencode('.jpg', frame)
            if not ret2:
                print("⚠️ Error al codificar imagen")
                continue

            # Enviar frame como archivo JPEG
            files = {
                "file": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
            }

            try:
                r = requests.post(fastapi_url, files=files, timeout=1.0)
                print("✅ Enviado:", r.status_code)
            except Exception as e:
                print("❌ Error al enviar:", e)

            # Libera la imagen codificada y fuerza limpieza de memoria
            del img_encoded
            del frame
            gc.collect()

            time.sleep(0.3)  # Intervalo de envío (3 FPS aprox)

    except KeyboardInterrupt:
        print("🛑 Interrumpido por el usuario")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("🎥 Recurso de cámara liberado correctamente")

if __name__ == "__main__":
    main()
