import json
import os
import queue
import threading

from flask import Flask, Response, jsonify, render_template, request
from flask_cors import CORS

from Analytic_For_WebUI import analyze_with_progress
from Extract import get_comments_from_csv
from Fetch import Fetch
from model_list import model_list

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
DEFAULT_API_KEY_FILE = "API_Key.txt"   # ไฟล์ fallback ถ้ายังไม่ได้เลือก
ACTIVE_KEY_FILE      = ".active_key"   # เก็บ path ของไฟล์ที่ user เลือกไว้ล่าสุด

app = Flask(__name__)
CORS(app)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def get_active_key_path() -> str:
    """
    อ่าน path ของไฟล์ API Key ที่ user เลือกไว้ล่าสุด
    ถ้ายังไม่เคยเลือก ให้ใช้ DEFAULT_API_KEY_FILE เป็นค่าเริ่มต้น
    """
    if os.path.exists(ACTIVE_KEY_FILE):
        with open(ACTIVE_KEY_FILE, "r") as f:
            path = f.read().strip()
        if path:
            return path
    return DEFAULT_API_KEY_FILE


def load_api_key() -> str | None:
    """อ่าน API Key จากไฟล์ที่ active อยู่"""
    path = get_active_key_path()
    try:
        with open(path, "r") as f:
            return f.readline().strip() or None
    except FileNotFoundError:
        return None


def save_active_key_path(path: str):
    """บันทึก path ที่ user เลือกลง .active_key"""
    with open(ACTIVE_KEY_FILE, "w") as f:
        f.write(path)


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """เสิร์ฟหน้า HTML หลัก"""
    return render_template("index.html")


@app.route("/api/key-status")
def key_status():
    """
    เช็คสถานะ API Key ตอนเปิดหน้าเว็บ
    Response: { has_key, active_file }
    """
    key  = load_api_key()
    path = get_active_key_path()
    return jsonify({
        "has_key":     bool(key),
        "active_file": os.path.basename(path),
    })


@app.route("/api/models")
def get_models():
    """ดึงรายชื่อโมเดลที่ติดตั้งใน Ollama บนเครื่อง"""
    try:
        models = model_list()
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e), "models": []}), 500


@app.route("/api/select-key", methods=["POST"])
def select_key():
    """
    รับ path ของไฟล์ API Key ที่ user เลือกจาก UI
    Body: { "path": "/absolute/path/to/key.txt" }
    """
    data = request.json or {}
    path = data.get("path", "").strip()

    if not path:
        return jsonify({"error": "ไม่ได้ระบุ path"}), 400

    if not os.path.isfile(path):
        return jsonify({"error": f"ไม่พบไฟล์: {path}"}), 404

    try:
        with open(path, "r") as f:
            key = f.readline().strip()
        if not key:
            return jsonify({"error": "ไฟล์ว่างเปล่า ไม่มี API Key"}), 400
    except Exception as e:
        return jsonify({"error": f"อ่านไฟล์ไม่ได้: {str(e)}"}), 400

    save_active_key_path(path)
    return jsonify({
        "success":     True,
        "active_file": os.path.basename(path),
    })


@app.route("/api/reset-key", methods=["POST"])
def reset_key():
    """กลับไปใช้ DEFAULT_API_KEY_FILE"""
    save_active_key_path(DEFAULT_API_KEY_FILE)
    key = load_api_key()
    return jsonify({
        "success":     True,
        "has_key":     bool(key),
        "active_file": os.path.basename(DEFAULT_API_KEY_FILE),
    })


@app.route("/api/analyze")
def analyze_stream():
    """
    SSE endpoint — รับ YouTube URL + model แล้วส่ง progress กลับ real-time
    เรียกด้วย EventSource('/api/analyze?url=...&model=...')
    """
    youtube_url = request.args.get("url", "").strip()
    model       = request.args.get("model", "qwen2.5:latest").strip()
    batch_size  = max(5, min(100, int(request.args.get("batch", 25))))

    if not youtube_url:
        return jsonify({"error": "ไม่มี URL"}), 400

    api_key = load_api_key()
    if not api_key:
        return jsonify({"error": "ยังไม่ได้ตั้งค่า API Key"}), 400

    progress_queue = queue.Queue()

    def run_pipeline():
        try:
            # 1. Fetch comments จาก YouTube
            progress_queue.put({
                "type": "status",
                "message": "กำลังดึงคอมเมนต์จาก YouTube...",
                "percent": 5,
            })
            result = Fetch(api_key, youtube_url)

            if result is None:
                progress_queue.put({
                    "type": "error",
                    "message": "ดึงคอมเมนต์ไม่สำเร็จ ตรวจสอบ URL หรือ API Key",
                })
                return

            file_name, total_expected = result
            progress_queue.put({
                "type":           "status",
                "message":        f"ดึงคอมเมนต์ได้แล้ว ({total_expected} รายการ) กำลังวิเคราะห์...",
                "percent":        20,
                "total_comments": total_expected,
            })

            # 2. Extract comment list จาก CSV
            comments = get_comments_from_csv(file_name)

            # 3. Analyze (progress ส่งผ่าน queue ใน Analytic.py)
            analyze_with_progress(comments, progress_queue, model=model, batch_size=batch_size)

        except Exception as e:
            progress_queue.put({"type": "error", "message": f"เกิดข้อผิดพลาด: {str(e)}"})

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    def event_stream():
        while True:
            try:
                event = progress_queue.get(timeout=120)
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") in ("done", "error"):
                    break
            except queue.Empty:
                yield 'data: {"type":"ping"}\n\n'

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ──────────────────────────────────────────────
# START
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 45)
    print("  Comment Analysis Server")
    print("  เปิด browser แล้วไปที่: http://localhost:5000")
    print("=" * 45)
    app.run(debug=False, host="0.0.0.0", port=5000)
