

lệnh rebuild embedding:

```bash
python3 -m backend.build_embeddings
```

lệnh chạy chatbot:

lệnh khai báo thư viện:

Ubuntu:
```bash
source elevator_env38/bin/activate
```

Jetson:
```bash
source ~/venvs/sunybot_jetson/bin/activate
```
```bash
cd ~/elevator_ai_project
```
lệnh test chatbot:
```bash
python3 -m backend.test_chatbot
```
lệnh chạy GUI chatbot:
```bash
python3 -m gui.main
```
lệnh chạy GUI quản lý database:
```bash
python mysql_admin_gui_pk.py
```
lệnh chạy API chatbot:
```bash
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```
test ollama terminal:
```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"deepseek-r1:1.5b","prompt":"Do you think Loc is pretty?","stream":false}' | head
```
chạy cloudflare:
```bash
cloudflared tunnel --url http://localhost:8000
```
lệnh test camera(IMX219):

kiểm tra jetson có nhận camera chưa:

```bash
gst-inspect-1.0 nvarguscamerasrc
```

lệnh chạy test camera:

```bash
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! nvvidconv ! xvimagesink
```
lệnh chạy test camera bằng tool invdia:

```bash
nvgstcapture-1.0
```

