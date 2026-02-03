

lệnh rebuild embedding:

```bash
python3 -m backend.build_embeddings
```

lệnh chạy chatbot:

lệnh khai báo thư viện:
```bash
source elevator_env38/bin/activate
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
lệnh chạy API chatbot:
```bash
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```
test ollama terminal:
```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"deepseek-r1:1.5b","prompt":"Do you think Loc is pretty?","stream":false}' | head
```
chạy clouldfale:
```bash
cloudflared tunnel --url http://localhost:8000
```
