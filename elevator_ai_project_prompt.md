# Prompt hồ sơ dự án: Elevator AI / Sunybot Smart Elevator

Tài liệu này là **bản mô tả chuẩn, đầy đủ và thực dụng nhất** về project để có thể đưa cho bất kỳ chat nào. Mục tiêu là để chat mới **hiểu nhanh hệ thống đang làm gì, từng file có vai trò gì, file nào đang chạy thật, file nào là legacy/build/cache, và khi cần chỉnh sửa thì nên sửa đúng file nào**.

---

## 1) Cách dùng tài liệu này với chat mới

Khi gửi tài liệu này cho một chat khác, hãy xem đây như **ngữ cảnh nền tảng của project**. Chat đó nên:

1. Đọc toàn bộ tài liệu trước khi đề xuất sửa code.
2. Ưu tiên hiểu **runtime thật đang chạy** thay vì chỉ nhìn tên file.
3. Không sửa các file build/cache nếu còn source gốc.
4. Khi đề xuất thay đổi, luôn chỉ ra:
   - file bắt buộc sửa
   - file có thể bị ảnh hưởng
   - file không nên sửa
5. Nếu có mâu thuẫn giữa code và schema/UI, phải nêu rõ thay vì giả định.

---

## 2) Tóm tắt rất nhanh về đề tài

Đây là project **thang máy thông minh có tích hợp chatbot/voice assistant** tên là **Sunybot**.

Hệ thống gồm các phần chính:

- **Frontend GUI**: giao diện web chính cho trạng thái thang máy, gọi tầng, trợ lý ảo, SOS, bảo trì; ngoài ra còn có GUI desktop phụ.
- **Backend API (FastAPI)**: serve giao diện web, cung cấp endpoint chatbot và trạng thái thang máy.
- **Chatbot Engine**: quyết định cách trả lời câu hỏi bằng nhiều tầng ưu tiên.
- **Database MySQL**: lưu tri thức hỏi đáp, dữ liệu nhân viên, log chat.
- **Embedding + Semantic Matching**: so khớp câu hỏi với tri thức trong DB.
- **LLM/Ollama**: sinh câu trả lời fallback khi không match được DB.
- **Voice**: hỗ trợ wake word kiểu “hey sunybot” và speech-to-text / text-to-speech ở frontend.

### Sơ đồ tổng quan ngắn

```text
[Frontend GUI (Web/Desktop)]
        ↓ HTTP / JSON / Static Files
[Backend API (FastAPI)]
        ↓
[Chatbot Engine]
        ↓
[Knowledge Services]
(Employee Service + Semantic Matcher + Embedding Service + Ollama Service)
        ↓
[Database MySQL]
(Employees + Intents + Prompts + Answers + Chat Logs)
        ↘
         [Ollama]
         (Embedding model + LLM generation)
```

---

## 3) Mục tiêu chức năng của hệ thống

Project hiện thể hiện ít nhất các nhóm chức năng sau:

1. **Chatbot trả lời câu hỏi về thang máy**
   - có thể trả lời từ knowledge base trong DB
   - có thể fallback sang LLM

2. **Tra cứu thông tin nhân viên**
   - tra bằng mã nhân viên (ví dụ NV020)
   - tra gần đúng theo tên

3. **Hiển thị trạng thái thang máy**
   - tầng hiện tại
   - hướng di chuyển
   - trạng thái cửa
   - số người
   - quá tải

4. **Gọi tầng từ giao diện**
   - gọi tầng thường
   - có khái niệm tầng khóa

5. **SOS / khẩn cấp**
   - gửi tín hiệu SOS từ giao diện

6. **Tương tác bằng giọng nói**
   - wake word
   - STT (speech-to-text)
   - TTS (speech synthesis)

7. **Màn bảo trì / demo vận hành**
   - dashboard bảo trì
   - login demo bằng localStorage
   - truy vấn LLM demo

8. **Công cụ quản trị DB**
   - GUI PyQt cho phép xem/sửa/xóa/thêm dữ liệu MySQL theo primary key

---

## 4) Runtime thật hiện tại: file nào chạy chính

### Entrypoint backend/runtime chính

Runtime web hiện tại nên được hiểu là:

```bash
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

Đây là lệnh được gợi ý trực tiếp trong `install_jetson.sh`, nên **`backend/api.py` là entrypoint runtime web quan trọng nhất**.

### Frontend được ưu tiên khi mở `/`

`backend/api.py` ưu tiên serve:

1. `gui/web/dist/index.html` nếu tồn tại
2. nếu không có dist thì fallback sang `gui/web/index.html`

Điều này cực kỳ quan trọng vì project đang có **2 lớp frontend song song**:

- **frontend build mới** trong `gui/web/dist/*`
- **frontend cũ / source web** trong `gui/web/index.html`, `pages/*`, `static/*`

### Kết luận runtime hiện tại

Khi chạy mặc định bằng FastAPI:

- backend chạy thật: `backend/api.py`
- chatbot pipeline chạy thật: `backend/chatbot_engine.py` + các service liên quan
- DB chạy thật nếu MySQL có dữ liệu phù hợp
- frontend đang được ưu tiên: `gui/web/dist/*`
- frontend cũ vẫn tồn tại để fallback/legacy hoặc để tham khảo source

---

## 5) Luồng xử lý chính của chatbot

### Luồng backend

```text
Người dùng nhập câu hỏi
    ↓
POST /chat
    ↓
backend/api.py
    ↓
ChatbotEngine.handle()
    ↓
1) Nếu là mã nhân viên -> employee_service.find_employee_by_code()
2) Nếu giống tên người -> employee_service.find_employee_by_name()
3) Nếu không -> embedding_service.embed()
                 -> semantic_matcher.match()
4) Nếu vẫn không match -> ollama_service.chat()
    ↓
Trả về answer + source + intent + confidence
    ↓
Ghi log vào chat_logs
```

### Ý nghĩa của pipeline

Pipeline trả lời hiện tại có 4 tầng ưu tiên:

1. **Employee lookup theo mã**
2. **Employee lookup theo tên**
3. **DB semantic match**
4. **LLM fallback**

Đây là logic cốt lõi nhất của project. Nếu cần thay đổi hành vi chatbot, hầu hết phải xem `backend/chatbot_engine.py` trước.

---

## 6) Luồng xử lý chính của frontend web cũ/source

```text
web/index.html
  ↓
static/js/app.js boot
  ├─ initNav()
  ├─ bindGlobalFunctions()
  ├─ initTopbarClock()
  ├─ initMaint()
  ├─ updateStatus() mỗi 1 giây
  ├─ updateWeather() mỗi 10 phút
  ├─ updateSOSTime() mỗi 1 giây
  └─ enableWake()

Các module gọi tiếp:
  app.js
   ├─ status.js  -> api.js -> /api/elevator/status
   ├─ weather.js -> api.js -> /api/weather
   ├─ chat.js    -> api.js -> /chat
   ├─ call.js    -> api.js -> /api/elevator/call
   ├─ sos.js     -> api.js -> /api/sos
   ├─ voice.js   -> api.js -> /chat
   ├─ maint.js   -> demo/localStorage
   ├─ botui.js   -> TTS + trạng thái bot
   └─ dom.js     -> gom tất cả DOM reference
```

---

## 7) Các điểm rất quan trọng cần chat mới hiểu ngay

### 7.1. Project có nhiều lớp UI song song

Có ít nhất 4 lớp giao diện khác nhau:

1. **Frontend build mới**: `gui/web/dist/*`
2. **Frontend source web cũ**: `gui/web/index.html` + `static/*`
3. **Trang HTML riêng lẻ/legacy**: `gui/web/pages/*`, `gui/web/templates/chat.html`
4. **GUI desktop PyQt**: `gui/main.py`, `gui/gui/mysql_admin_gui_pk.py`

=> Không được giả định chỉ có một frontend duy nhất.

### 7.2. Một số phần là mock/demo, chưa production hoàn chỉnh

- `/api/elevator/status` hiện là **mock data** chứ chưa nối PLC/CV thật.
- `maint.js` là **demo maintenance**, dùng localStorage và kết quả LLM mẫu.
- `call.html` cũ mới demo UI gọi tầng, chưa thật sự nối API production.

### 7.3. Có dấu hiệu mâu thuẫn giữa code và schema

Đây là điểm rất quan trọng cho mọi chat mới:

- `chatbot_engine.py` ghi log vào `chat_logs(question, intent_name, confidence, source, answer_preview)`.
- Nhưng `schema.sql` đang tạo `chat_logs` chỉ có: `log_id, question, intent_name, confidence, created_at`.

=> Nghĩa là **schema DB và code backend có thể đang lệch nhau**. Nếu chạy nguyên xi, phần log chat có thể lỗi nếu DB chưa được update.

### 7.4. Có dấu hiệu mâu thuẫn giữa code mới và code cũ

- `backend/api.py` tự định nghĩa `ChatRequest`/`ChatResponse`, trong khi `backend/schemas.py` lại định nghĩa schema khác (`employee_id`, `employee_name`, `question`).
- `gui/main.py` import `get_chatbot_response` và `find_employee`, nhưng các file backend hiện tại nghiêng về `ChatbotEngine.handle()` hơn là các hàm cũ.

=> Có khả năng `gui/main.py` và `schemas.py` là **legacy / chưa đồng bộ với bản backend hiện tại**.

### 7.5. Frontend source và backend API chưa khớp hoàn toàn

Frontend source gọi:

- `/api/weather`
- `/api/sos`
- `/api/elevator/call`

Nhưng trong `backend/api.py` đã kiểm tra, hiện chỉ thấy rõ:

- `/`
- `/pages/{page}`
- `/health`
- `/api/elevator/status`
- `/chat`
- fallback SPA

=> Có khả năng **một số API frontend đang gọi chưa được định nghĩa trong `backend/api.py` hiện tại** hoặc nằm ở file khác chưa được tích hợp.

---

## 8) Cây thư mục tổng hợp có chú thích vai trò từng file

Lưu ý:
- Những file đã có nội dung được đọc thì mô tả với độ tin cậy cao.
- File build/cache/nhị phân được đánh dấu rõ.
- Một số file `__init__.py` chỉ là package marker.

```text
.
├── backend (tầng backend chính)
│   ├── api.py (entrypoint FastAPI; serve UI, expose /chat, /health, /api/elevator/status, SPA fallback)
│   ├── build_embeddings.py (script build/cập nhật embedding cho bảng prompts trong DB)
│   ├── chatbot_engine.py (bộ điều phối trung tâm của chatbot)
│   ├── embedding_service.py (service tạo vector embedding qua Ollama)
│   ├── employee_service.py (service tra cứu nhân viên theo mã/tên và format câu trả lời)
│   ├── __init__.py (đánh dấu backend là package Python)
│   ├── logger.py (thiết lập logging file + console)
│   ├── ollama_service.py (service gọi LLM Ollama để sinh câu trả lời fallback)
│   ├── __pycache__ (cache Python; bỏ qua khi phân tích logic)
│   │   ├── api.cpython-38.pyc (cache; bỏ qua)
│   │   ├── build_embeddings.cpython-38.pyc (cache; bỏ qua)
│   │   ├── chatbot_engine.cpython-38.pyc (cache; bỏ qua)
│   │   ├── embedding_service.cpython-38.pyc (cache; bỏ qua)
│   │   ├── employee_service.cpython-38.pyc (cache; bỏ qua)
│   │   ├── __init__.cpython-38.pyc (cache; bỏ qua)
│   │   ├── ollama_service.cpython-38.pyc (cache; bỏ qua)
│   │   ├── semantic_matcher.cpython-38.pyc (cache; bỏ qua)
│   │   └── text_utils.cpython-38.pyc (cache; bỏ qua)
│   ├── schemas.py (schema Pydantic cũ/riêng cho chat; có dấu hiệu legacy hoặc chưa đồng bộ)
│   ├── semantic_matcher.py (service so khớp ngữ nghĩa dựa trên prompt/embedding/answer trong DB)
│   ├── test_chatbot.py (test backend cho greeting, employee code, faq tốc độ)
│   └── text_utils.py (utility chuẩn hóa tiếng Việt và làm sạch text)
├── cloudflared-linux-amd64.deb (gói cài cloudflared; không phải app logic chính)
├── config (thư mục cấu hình)
│   ├── db_config.py (cấu hình và tạo kết nối MySQL)
│   ├── db_config.py.save (bản sao lưu file cấu hình DB)
│   ├── __init__.py (đánh dấu config là package Python)
│   └── __pycache__ (cache; bỏ qua)
│       ├── db_config.cpython-38.pyc (cache; bỏ qua)
│       └── __init__.cpython-38.pyc (cache; bỏ qua)
├── database (thư mục dữ liệu và script DB)
│   ├── __pycache__ (cache; bỏ qua)
│   │   └── remove_vietnamese_accent.cpython-38.pyc (cache; bỏ qua)
│   ├── remove_vietnamese_accent.py (utility bỏ dấu và script convert dữ liệu DB sang không dấu)
│   ├── schema.sql (khai báo cấu trúc bảng dữ liệu)
│   └── seed.sql (nạp dữ liệu mẫu ban đầu cho intents/prompts/answers/employees)
├── gui (thư mục giao diện)
│   ├── gui (desktop tools phụ)
│   │   └── mysql_admin_gui_pk.py (GUI PyQt quản trị bảng MySQL an toàn theo PK)
│   ├── __init__.py (đánh dấu gui là package Python)
│   ├── main.py (GUI desktop chatbot PyQt; có dấu hiệu dùng API/hàm cũ)
│   └── web (giao diện web)
│       ├── assets (asset web chung; ít thông tin hơn source cụ thể)
│       ├── dist (frontend build output; ưu tiên serve khi chạy /)
│       │   ├── assets (bundle CSS/JS đã build)
│       │   │   ├── index-bn7l8BoE.css (CSS build output; không nên sửa trực tiếp)
│       │   │   └── index-C94rDJOP.js (JS build output; không nên sửa trực tiếp)
│       │   ├── favicon.ico (icon build)
│       │   └── index.html (entry HTML của frontend đã build)
│       ├── index.html (frontend source/legacy tổng hợp nhiều màn hình và logic inline)
│       ├── pages (các trang chức năng riêng theo kiểu cũ)
│       │   ├── assistant.html (trang trợ lý ảo/chat dạng HTML tách riêng)
│       │   └── call.html (trang gọi tầng riêng kiểu cũ/demo)
│       ├── static (source frontend thật cho web cũ)
│       │   ├── app.css (CSS chính của kiosk/web app hiện đại)
│       │   ├── app.js (bootstrap layer ngắn để render topbar/tabbar và gọi SunyApp)
│       │   ├── favicon.ico (icon website)
│       │   ├── js (thư mục module frontend theo tính năng)
│       │   │   ├── api.js (lớp gọi API backend chung)
│       │   │   ├── app.js (orchestrator/boot của frontend web)
│       │   │   ├── botui.js (điều khiển trạng thái bot + TTS)
│       │   │   ├── call.js (logic gọi tầng)
│       │   │   ├── chat.js (logic chat frontend)
│       │   │   ├── dom.js (gom DOM reference dùng chung)
│       │   │   ├── maint.js (logic maintenance demo)
│       │   │   ├── sos.js (logic SOS)
│       │   │   ├── status.js (logic cập nhật trạng thái thang máy)
│       │   │   ├── voice.js (logic voice, STT, wake word)
│       │   │   └── weather.js (logic thời tiết)
│       │   ├── style.css (CSS cho chat UI cũ/đơn giản)
│       │   └── ui.js (UI helper chung: topbar, tabbar, toast, escapeHtml)
│       └── templates
│           └── chat.html (template chat HTML cũ đơn giản)
├── __init__.py (đánh dấu thư mục gốc là package Python)
├── install_jetson.sh (script cài môi trường cho Jetson và hướng dẫn chạy uvicorn)
├── package.json (metadata Node tối giản; chưa phản ánh toolchain frontend đầy đủ)
├── packages.microsoft.gpg (key hệ thống; không phải app logic)
├── pyproject.toml (file cấu hình Python project; chưa được đọc nội dung trong phiên làm việc này)
└── setup.py (build native extension sunycore_native bằng pybind11/C++)
```

---

## 9) Bảng vai trò từng file: file → gọi khi nào → liên quan file nào → sửa khi nào

## 9.1 Backend

### `backend/api.py`
- **Vai trò**: entrypoint FastAPI; mount static; serve dist/old UI; expose `/chat`; expose `/health`; expose `/api/elevator/status`; SPA fallback.
- **Được gọi khi nào**: khi chạy `uvicorn backend.api:app`.
- **Liên quan**:
  - gọi `backend.chatbot_engine.ChatbotEngine`
  - serve file trong `gui/web/dist`, `gui/web/index.html`, `gui/web/pages`, `gui/web/static`
- **Sửa khi**:
  - thêm/sửa endpoint backend
  - đổi route frontend
  - đổi cách serve UI
  - nối API weather/SOS/call thật
- **Ghi chú**:
  - hiện `/api/elevator/status` vẫn là mock
  - có vẻ chưa có route `/api/weather`, `/api/sos`, `/api/elevator/call` trong file này

### `backend/chatbot_engine.py`
- **Vai trò**: orchestrator trung tâm của chatbot.
- **Được gọi khi nào**: khi `/chat` nhận request.
- **Liên quan**:
  - `employee_service.py`
  - `embedding_service.py`
  - `semantic_matcher.py`
  - `ollama_service.py`
  - `config/db_config.py`
- **Sửa khi**:
  - đổi thứ tự xử lý chatbot
  - đổi threshold semantic search
  - thêm luật routing mới
  - đổi logic fallback
- **Ghi chú**:
  - là file quan trọng nhất cho hành vi chatbot
  - có khả năng lệch schema với `chat_logs`

### `backend/employee_service.py`
- **Vai trò**: nhận diện mã nhân viên, tìm nhân viên theo mã/tên, format câu trả lời.
- **Được gọi khi nào**: trong `ChatbotEngine.handle()` ở bước employee lookup.
- **Liên quan**:
  - `config/db_config.py`
  - `backend/text_utils.py`
  - bảng `employees`
- **Sửa khi**:
  - muốn tra cứu nhân viên tốt hơn
  - thêm tìm theo normalized name
  - đổi format trả lời nhân viên

### `backend/embedding_service.py`
- **Vai trò**: tạo embedding từ text qua Ollama embeddings API.
- **Được gọi khi nào**:
  - trong `chatbot_engine.py` trước semantic matching
  - trong `build_embeddings.py` khi build vector cho prompt
- **Liên quan**:
  - `backend/text_utils.py`
  - Ollama host/model embedding
- **Sửa khi**:
  - đổi model embedding
  - đổi timeout/retry
  - cải thiện độ chính xác semantic search

### `backend/semantic_matcher.py`
- **Vai trò**: load knowledge từ DB; exact match theo normalized text; cosine similarity theo embedding.
- **Được gọi khi nào**: từ `chatbot_engine.py` sau khi có embedding.
- **Liên quan**:
  - `config/db_config.py`
  - `backend/text_utils.py`
  - bảng `intents`, `prompts`, `answers`
- **Sửa khi**:
  - đổi threshold
  - thay chiến lược matching
  - thêm hybrid search
  - tối ưu semantic retrieval

### `backend/ollama_service.py`
- **Vai trò**: gọi LLM qua Ollama để fallback khi DB không trả lời được.
- **Được gọi khi nào**: bước cuối của `ChatbotEngine.handle()`.
- **Liên quan**:
  - Ollama host/model generation
- **Sửa khi**:
  - đổi prompt system
  - đổi model LLM
  - muốn câu trả lời dài hơn/ngắn hơn/tự nhiên hơn

### `backend/text_utils.py`
- **Vai trò**: chuẩn hóa tiếng Việt, bỏ dấu, gọn khoảng trắng, bỏ ký tự lạ.
- **Được gọi khi nào**:
  - trước embed
  - trước semantic matching
  - trong tìm kiếm nhân viên gần đúng
- **Liên quan**:
  - `database/remove_vietnamese_accent.py`
- **Sửa khi**:
  - muốn đổi quy tắc normalize
  - muốn giữ ký tự đặc biệt
  - muốn cải thiện matching tiếng Việt

### `backend/build_embeddings.py`
- **Vai trò**: script build/cập nhật embedding cho bảng `prompts`.
- **Được gọi khi nào**: chạy thủ công hoặc sau khi seed/cập nhật knowledge base.
- **Liên quan**:
  - `config/db_config.py`
  - `backend/embedding_service.py`
  - `backend/text_utils.py`
  - bảng `prompts`
- **Sửa khi**:
  - đổi model embedding
  - đổi format lưu embedding
  - rebuild knowledge base

### `backend/schemas.py`
- **Vai trò**: schema Pydantic cũ/riêng cho chat.
- **Được gọi khi nào**: hiện chưa thấy `backend/api.py` dùng.
- **Liên quan**: có thể là code cũ hoặc định hướng cũ.
- **Sửa khi**:
  - muốn thống nhất contract request/response toàn project
- **Ghi chú**:
  - hiện có dấu hiệu legacy vì khác với `backend/api.py`

### `backend/logger.py`
- **Vai trò**: setup logging file + console.
- **Được gọi khi nào**: nếu có file startup/import dùng `setup_logger()`.
- **Liên quan**: log runtime.
- **Sửa khi**:
  - đổi nơi ghi log
  - đổi format log
  - thêm rotation

### `backend/test_chatbot.py`
- **Vai trò**: test luồng chatbot backend.
- **Được gọi khi nào**: khi chạy test.
- **Liên quan**:
  - `backend/chatbot_engine.py`
  - DB seed dữ liệu
- **Sửa khi**:
  - thêm tính năng chatbot mới
  - đổi output mong đợi

## 9.2 Config / Database

### `config/db_config.py`
- **Vai trò**: cấu hình kết nối MySQL qua env vars.
- **Được gọi khi nào**: bất kỳ service nào cần DB.
- **Liên quan**:
  - backend services
  - database scripts
- **Sửa khi**:
  - đổi host/user/pass/db/port
  - thêm pool/config DB

### `database/schema.sql`
- **Vai trò**: tạo database và các bảng chính.
- **Được gọi khi nào**: lúc khởi tạo DB.
- **Liên quan**:
  - `seed.sql`
  - backend services
- **Sửa khi**:
  - đổi schema dữ liệu
  - thêm bảng/cột/index
- **Ghi chú**:
  - cần so khớp lại với code runtime, nhất là bảng `chat_logs` và `prompts`

### `database/seed.sql`
- **Vai trò**: nạp dữ liệu mẫu ban đầu.
- **Được gọi khi nào**: lúc seed DB.
- **Liên quan**:
  - `schema.sql`
  - `test_chatbot.py`
  - `semantic_matcher.py`
- **Sửa khi**:
  - đổi dữ liệu mẫu
  - thêm intents/prompts/answers/employees

### `database/remove_vietnamese_accent.py`
- **Vai trò**: utility bỏ dấu; đồng thời có thể convert dữ liệu hiện có trong DB sang không dấu.
- **Được gọi khi nào**:
  - gián tiếp qua `text_utils.py`
  - trực tiếp khi chạy script convert DB
- **Liên quan**:
  - `backend/text_utils.py`
  - các bảng text trong DB
- **Sửa khi**:
  - đổi cách remove accent
  - đổi script migrate dữ liệu

## 9.3 GUI desktop

### `gui/main.py`
- **Vai trò**: chatbot desktop PyQt đơn giản.
- **Được gọi khi nào**: khi chạy desktop app này trực tiếp.
- **Liên quan**:
  - backend chatbot
- **Sửa khi**:
  - muốn đổi UI chatbot desktop
  - test chatbot không qua web
- **Ghi chú**:
  - có dấu hiệu dùng API/hàm cũ (`get_chatbot_response`, `find_employee`)

### `gui/gui/mysql_admin_gui_pk.py`
- **Vai trò**: GUI quản trị MySQL bằng PyQt + pandas + SQLAlchemy.
- **Được gọi khi nào**: khi chạy tool admin DB.
- **Liên quan**:
  - MySQL
  - PK constraints
- **Sửa khi**:
  - muốn chỉnh tool admin
  - thêm search/filter/export
  - đổi cách save/update/delete
- **Ghi chú**:
  - có cơ chế chặn update/delete nếu table không có primary key

## 9.4 Web frontend – source/legacy

### `gui/web/index.html`
- **Vai trò**: frontend source/legacy lớn với nhiều logic inline, nhiều màn hình trong một app shell.
- **Được gọi khi nào**:
  - khi `dist` không có và backend fallback về old index
  - hoặc khi cố ý dùng bản source cũ
- **Liên quan**:
  - `/chat`, `/api/elevator/status`, `/api/weather`, `/api/sos`, `/api/elevator/call`
- **Sửa khi**:
  - muốn sửa frontend source cũ trực tiếp
- **Ghi chú**:
  - chứa nhiều logic trùng với `static/js/*`, cho thấy quá trình chuyển đổi chưa hoàn tất

### `gui/web/pages/assistant.html`
- **Vai trò**: trang chat/trợ lý ảo tách riêng theo kiểu cũ.
- **Được gọi khi nào**: qua `/pages/assistant.html`.
- **Liên quan**:
  - `/chat`
  - `static/ui.js`
  - `static/app.css`
- **Sửa khi**:
  - muốn sửa UX chat riêng của page cũ

### `gui/web/pages/call.html`
- **Vai trò**: trang gọi tầng demo kiểu cũ.
- **Được gọi khi nào**: qua `/pages/call.html`.
- **Liên quan**:
  - toast/UI helper
  - logic gọi tầng demo
- **Sửa khi**:
  - muốn sửa keypad/page gọi tầng cũ
- **Ghi chú**:
  - hiện là demo UI, chưa là flow production hoàn chỉnh

### `gui/web/templates/chat.html`
- **Vai trò**: template chat HTML rất cũ, đơn giản.
- **Được gọi khi nào**: nếu backend/template route cũ còn dùng.
- **Liên quan**:
  - `/static/style.css`
  - `/static/chat.js`
- **Sửa khi**:
  - muốn giữ hoặc sửa flow template cũ

## 9.5 Web frontend – static source

### `gui/web/static/app.css`
- **Vai trò**: CSS chính cho kiosk/web app hiện đại.
- **Được gọi khi nào**: khi frontend source web hiện đại chạy.
- **Liên quan**:
  - `gui/web/index.html`
  - `pages/assistant.html`
- **Sửa khi**:
  - đổi theme/layout/tổng thể UI

### `gui/web/static/style.css`
- **Vai trò**: CSS cho chat UI cũ/đơn giản.
- **Được gọi khi nào**: với `templates/chat.html` hoặc UI cũ.
- **Sửa khi**:
  - đổi giao diện chat legacy

### `gui/web/static/ui.js`
- **Vai trò**: UI helper chung; render topbar, tabbar, toast, escapeHtml.
- **Được gọi khi nào**: ở source web cũ/legacy.
- **Liên quan**:
  - `gui/web/index.html`
  - `pages/assistant.html`
- **Sửa khi**:
  - đổi topbar/toast/helper chung

### `gui/web/static/app.js`
- **Vai trò**: bootstrap layer ngắn để gọi `SunyUI.renderTopbar()`, `SunyUI.renderTabbar()`, `SunyApp.init()`.
- **Được gọi khi nào**: nếu HTML dùng file bootstrap này.
- **Liên quan**:
  - `ui.js`
  - `static/js/app.js`
- **Ghi chú**:
  - dễ nhầm với `gui/web/static/js/app.js`

## 9.6 Web frontend – module JS theo tính năng

### `gui/web/static/js/api.js`
- **Vai trò**: lớp fetch chung cho frontend.
- **Được gọi khi nào**: mọi module cần gọi backend.
- **Liên quan**:
  - `/chat`
  - `/api/elevator/status`
  - `/api/weather`
  - `/api/sos`
  - `/api/elevator/call`
- **Sửa khi**:
  - đổi endpoint/payload/error handling chung

### `gui/web/static/js/app.js`
- **Vai trò**: orchestrator/boot của frontend source.
- **Được gọi khi nào**: khi frontend source JS module được chạy.
- **Liên quan**:
  - `status.js`
  - `weather.js`
  - `voice.js`
  - `chat.js`
  - `call.js`
  - `sos.js`
  - `maint.js`
  - `dom.js`
- **Sửa khi**:
  - đổi boot app
  - đổi polling
  - thêm/bớt global actions
  - đổi nav giữa screen

### `gui/web/static/js/dom.js`
- **Vai trò**: gom các DOM element dùng chung.
- **Được gọi khi nào**: bởi hầu hết module JS khác.
- **Sửa khi**:
  - HTML đổi id
  - thêm/xóa phần tử giao diện

### `gui/web/static/js/chat.js`
- **Vai trò**: xử lý chat text ở frontend.
- **Được gọi khi nào**: khi người dùng gửi chat.
- **Liên quan**:
  - `api.js`
  - `botui.js`
  - `dom.js`
- **Sửa khi**:
  - đổi UX chat
  - thêm metadata/source/confidence
  - thêm lịch sử chat

### `gui/web/static/js/botui.js`
- **Vai trò**: đặt mode visual cho bot và phát TTS.
- **Được gọi khi nào**:
  - từ `chat.js`
  - từ `voice.js`
- **Sửa khi**:
  - đổi animation/trạng thái bot
  - đổi giọng nói/text-to-speech

### `gui/web/static/js/voice.js`
- **Vai trò**: wake word, STT, voice chat một lần.
- **Được gọi khi nào**: boot app hoặc bấm mic.
- **Liên quan**:
  - `api.js`
  - `botui.js`
  - `dom.js`
- **Sửa khi**:
  - đổi wake word
  - đổi hành vi voice
  - chống lặp/mic error tốt hơn

### `gui/web/static/js/status.js`
- **Vai trò**: cập nhật trạng thái thang máy ra UI.
- **Được gọi khi nào**: polling mỗi 1 giây.
- **Liên quan**:
  - `api.js`
  - `dom.js`
- **Sửa khi**:
  - đổi mapping UI status
  - thêm field backend mới
  - sửa trạng thái quá tải/cửa/hướng

### `gui/web/static/js/weather.js`
- **Vai trò**: lấy thời tiết và hiển thị lên UI.
- **Được gọi khi nào**: polling mỗi 10 phút.
- **Liên quan**:
  - `api.js`
  - `dom.js`
- **Sửa khi**:
  - đổi API thời tiết
  - đổi format hiển thị

### `gui/web/static/js/call.js`
- **Vai trò**: logic gọi tầng.
- **Được gọi khi nào**: khi user bấm gọi tầng.
- **Liên quan**:
  - `api.js`
- **Sửa khi**:
  - thêm xác thực tầng khóa
  - đổi flow gọi tầng

### `gui/web/static/js/sos.js`
- **Vai trò**: gửi tín hiệu SOS và cập nhật đồng hồ SOS.
- **Được gọi khi nào**: khi user bấm SOS, hoặc timer cập nhật thời gian.
- **Liên quan**:
  - `api.js`
  - `dom.js`
- **Sửa khi**:
  - đổi payload SOS
  - thêm retry/acknowledgement

### `gui/web/static/js/maint.js`
- **Vai trò**: maintenance demo.
- **Được gọi khi nào**: khi vào màn maintenance.
- **Liên quan**:
  - `dom.js`
  - localStorage
- **Sửa khi**:
  - biến thành chức năng thật
  - thêm auth thật
  - nối backend thật

## 9.7 Frontend build output

### `gui/web/dist/index.html`
- **Vai trò**: entry HTML của frontend đã build.
- **Được gọi khi nào**: khi mở `/` và dist tồn tại.
- **Sửa khi**:
  - hầu như không nên sửa trực tiếp
  - chỉ dùng để deploy/chạy

### `gui/web/dist/assets/index-C94rDJOP.js`
- **Vai trò**: JS bundle đã build (nhiều khả năng React/Vite).
- **Được gọi khi nào**: khi frontend build chạy.
- **Sửa khi**:
  - không nên sửa trực tiếp
  - chỉ debug hoặc tra cứu nhanh tính năng build
- **Ghi chú**:
  - bundle gợi ý build mới có màn chat, SOS, maintenance, khóa tầng, v.v.

### `gui/web/dist/assets/index-bn7l8BoE.css`
- **Vai trò**: CSS bundle đã build.
- **Được gọi khi nào**: cùng frontend build.
- **Sửa khi**:
  - không nên sửa trực tiếp

## 9.8 Root / packaging / deployment

### `install_jetson.sh`
- **Vai trò**: script cài môi trường Jetson Nano và hướng dẫn chạy.
- **Được gọi khi nào**: lúc setup deployment.
- **Liên quan**:
  - `setup.py`
  - `requirements.txt`
  - `backend/api.py`
- **Sửa khi**:
  - đổi môi trường target
  - thêm bước cài hệ thống

### `setup.py`
- **Vai trò**: build native extension `sunycore_native` bằng `pybind11`/C++.
- **Được gọi khi nào**: khi chạy `python3 setup.py build_ext --inplace`.
- **Liên quan**:
  - `suny_core/native/sunycore.cpp` (nguồn native không nằm trong các file đã xem)
- **Sửa khi**:
  - đổi module native
  - tối ưu native/C++
- **Ghi chú**:
  - hiện chưa thấy flow runtime web import module native này

### `package.json`
- **Vai trò**: metadata Node tối giản.
- **Được gọi khi nào**: gần như chưa đóng vai trò vận hành rõ ràng trong trạng thái hiện tại.
- **Sửa khi**:
  - nếu muốn chuẩn hóa frontend build tooling
- **Ghi chú**:
  - không có script `build/dev/start`, nên rất có thể chưa phải file điều phối frontend thật

### `pyproject.toml`
- **Vai trò**: cấu hình Python project hiện đại.
- **Trạng thái**: có trong cây thư mục nhưng **chưa được đọc nội dung trong phiên này**.
- **Ghi chú**:
  - chat mới nên kiểm tra file này nếu cần biết dependency/build config Python chính xác.

---

## 10) Danh sách file entrypoint

### Entrypoint runtime chính
- `backend/api.py`

### Entrypoint setup/deploy
- `install_jetson.sh`
- `setup.py`

### Entrypoint script dữ liệu
- `backend/build_embeddings.py`
- `database/remove_vietnamese_accent.py`

### Entrypoint GUI desktop
- `gui/main.py`
- `gui/gui/mysql_admin_gui_pk.py`

### Entrypoint frontend
- Runtime ưu tiên: `gui/web/dist/index.html`
- Fallback/legacy: `gui/web/index.html`
- Page riêng: `gui/web/pages/assistant.html`, `gui/web/pages/call.html`

---

## 11) Sơ đồ phụ thuộc giữa các file quan trọng

### 11.1. Sơ đồ phụ thuộc backend

```text
backend/api.py
  └─> backend/chatbot_engine.py
        ├─> backend/employee_service.py
        │     ├─> config/db_config.py
        │     └─> backend/text_utils.py
        │            └─> database/remove_vietnamese_accent.py
        │
        ├─> backend/embedding_service.py
        │     └─> backend/text_utils.py
        │
        ├─> backend/semantic_matcher.py
        │     ├─> config/db_config.py
        │     └─> backend/text_utils.py
        │
        ├─> backend/ollama_service.py
        │
        └─> config/db_config.py
```

### 11.2. Sơ đồ phụ thuộc frontend source

```text
gui/web/static/js/app.js
  ├─> status.js  -> api.js -> /api/elevator/status
  ├─> weather.js -> api.js -> /api/weather
  ├─> chat.js    -> api.js -> /chat
  ├─> call.js    -> api.js -> /api/elevator/call
  ├─> sos.js     -> api.js -> /api/sos
  ├─> voice.js   -> api.js -> /chat
  ├─> maint.js   -> dom.js + localStorage
  ├─> botui.js   -> speechSynthesis
  └─> dom.js
```

### 11.3. Sơ đồ phụ thuộc dữ liệu

```text
schema.sql
  ├─> intents
  ├─> prompts
  ├─> answers
  ├─> chat_logs
  └─> employees

seed.sql
  └─> nạp dữ liệu mẫu cho các bảng trên

build_embeddings.py
  └─> đọc prompts -> tạo embedding -> update prompts
```

---

## 12) File build/cache/artifact có thể bỏ qua khi đọc logic

Những thứ sau **không nên dùng để hiểu logic gốc**:

- `__pycache__/`
- `*.pyc`
- `gui/web/dist/assets/*` (nếu đã có source tương ứng)
- `cloudflared-linux-amd64.deb`
- `packages.microsoft.gpg`
- `db_config.py.save`

### Quy tắc sửa code an toàn

- Nếu có source + dist build, **sửa source**, không sửa build.
- Nếu có code cũ + code mới, phải xác định **runtime thực tế đang dùng cái nào** trước khi sửa.
- Với project này, backend runtime web rõ nhất là `backend/api.py`.

---

## 13) File nào có thể là legacy, chưa dùng, hoặc không hoạt động mặc định

### Rất có thể không phải runtime chính hiện tại
- `gui/main.py` (desktop chatbot)
- `gui/gui/mysql_admin_gui_pk.py` (tool admin)
- `gui/web/pages/*` (nếu đang ưu tiên dist)
- `gui/web/templates/chat.html`
- `gui/web/static/*` (nếu đang ưu tiên dist)
- `package.json` (quá tối giản)
- `setup.py` native module (chưa thấy được import trong flow runtime web hiện tại)

### Có khả năng legacy / chưa đồng bộ
- `backend/schemas.py`
- `gui/main.py`
- một phần logic inline trong `gui/web/index.html`

### Có khả năng mock/demo
- `/api/elevator/status` trong `backend/api.py`
- `maint.js`
- `pages/call.html`

---

## 14) Danh sách file nên sửa theo từng loại thay đổi

## 14.1. Muốn đổi hành vi chatbot
- **bắt buộc xem trước**: `backend/chatbot_engine.py`
- có thể sửa thêm:
  - `backend/semantic_matcher.py`
  - `backend/embedding_service.py`
  - `backend/ollama_service.py`
  - `backend/employee_service.py`

## 14.2. Muốn cải thiện semantic search / knowledge base
- `backend/semantic_matcher.py`
- `backend/embedding_service.py`
- `backend/build_embeddings.py`
- `database/seed.sql`
- có thể cần `database/schema.sql`

## 14.3. Muốn bot trả lời hay hơn bằng LLM
- `backend/ollama_service.py`
- có thể sửa threshold ở `backend/chatbot_engine.py`

## 14.4. Muốn tra cứu nhân viên tốt hơn
- `backend/employee_service.py`
- `database/schema.sql` nếu cần thêm cột normalized/search index
- `database/seed.sql` nếu thay dữ liệu mẫu

## 14.5. Muốn đổi API backend
- `backend/api.py`
- nếu đổi request/response contract thì xem thêm `backend/schemas.py` và frontend `api.js`

## 14.6. Muốn nối trạng thái thang máy thật
- `backend/api.py` (thay mock `/api/elevator/status` bằng dữ liệu thật)
- có thể thêm module service mới cho PLC/CV
- frontend liên quan:
  - `gui/web/static/js/status.js`
  - hoặc frontend build mới nếu dùng dist làm chính

## 14.7. Muốn thêm API còn thiếu cho frontend
- `backend/api.py`
- liên quan frontend source:
  - `gui/web/static/js/api.js`
  - `gui/web/static/js/weather.js`
  - `gui/web/static/js/sos.js`
  - `gui/web/static/js/call.js`

## 14.8. Muốn sửa giao diện web source/legacy
- bố cục/tổng thể: `gui/web/index.html`, `gui/web/static/app.css`
- topbar/toast/helper: `gui/web/static/ui.js`
- chat: `gui/web/static/js/chat.js`
- voice: `gui/web/static/js/voice.js`
- status: `gui/web/static/js/status.js`
- call: `gui/web/static/js/call.js`
- SOS: `gui/web/static/js/sos.js`
- maintenance: `gui/web/static/js/maint.js`

## 14.9. Muốn sửa frontend build mới
- nên tìm **source trước khi build** nếu có repo/source tương ứng
- **không nên sửa trực tiếp** `gui/web/dist/assets/index-*.js/css`
- nếu không còn source, dist chỉ nên dùng để tham khảo/debug khẩn cấp

## 14.10. Muốn sửa GUI desktop
- chatbot desktop: `gui/main.py`
- admin DB desktop: `gui/gui/mysql_admin_gui_pk.py`

## 14.11. Muốn sửa DB schema/dữ liệu
- schema: `database/schema.sql`
- seed: `database/seed.sql`
- normalize/bỏ dấu: `database/remove_vietnamese_accent.py`
- config kết nối: `config/db_config.py`

## 14.12. Muốn sửa setup/deploy
- Jetson setup: `install_jetson.sh`
- native build: `setup.py`
- Python build config: `pyproject.toml` (cần đọc nội dung thêm)

---

## 15) Những mâu thuẫn / rủi ro kỹ thuật mà chat mới phải biết

1. **Schema DB có thể lệch với code runtime**
   - cần đối chiếu lại `chat_logs`, `prompts` (các cột `embedding`, `normalized_text`, `embedding_model`, `source`, `answer_preview`)

2. **Backend API và frontend source chưa khớp hoàn toàn**
   - frontend gọi weather/SOS/call nhưng backend file hiện thấy chưa expose đủ

3. **Có nhiều lớp frontend song song**
   - dist mới
   - source cũ
   - pages riêng lẻ
   - template cũ

4. **GUI desktop có dấu hiệu dùng API cũ**
   - có thể sửa cần refactor nếu muốn dùng lại

5. **Có native extension nhưng chưa rõ đang dùng ở đâu trong runtime hiện tại**
   - `setup.py` build `sunycore_native`
   - cần kiểm tra lại nếu muốn dùng phần native

6. **Một số chức năng hiện còn là demo/mock**
   - maintenance
   - status realtime
   - call page cũ

---

## 16) Bộ tối thiểu để hệ thống web chính chạy

Nếu chỉ muốn chạy bản web chatbot/thang máy cơ bản, bộ tối thiểu nên hiểu là:

### Backend tối thiểu
- `backend/api.py`
- `backend/chatbot_engine.py`
- `backend/employee_service.py`
- `backend/embedding_service.py`
- `backend/semantic_matcher.py`
- `backend/ollama_service.py`
- `backend/text_utils.py`
- `config/db_config.py`

### Database tối thiểu
- `database/schema.sql`
- dữ liệu tương thích với code (hoặc `seed.sql` đã điều chỉnh)

### Frontend tối thiểu
- `gui/web/dist/*` nếu dùng bản build mới
- hoặc `gui/web/index.html` + `gui/web/static/*` nếu dùng source web cũ

### Phụ thuộc môi trường
- MySQL
- Ollama
- Python packages từ `requirements.txt`
- có thể cả native module nếu runtime thật sau này dùng đến

---

## 17) Gợi ý hành vi cho chat mới khi hỗ trợ sửa project này

Khi chat mới nhận tài liệu này, nên làm theo trình tự sau:

1. Xác định **đang sửa backend hay frontend hay DB**.
2. Xác định **runtime thật đang dùng dist hay source web cũ**.
3. Nếu sửa chatbot, đọc trước:
   - `backend/api.py`
   - `backend/chatbot_engine.py`
   - `backend/employee_service.py`
   - `backend/semantic_matcher.py`
   - `backend/embedding_service.py`
   - `backend/ollama_service.py`
4. Nếu sửa web source, đọc trước:
   - `gui/web/index.html`
   - `gui/web/static/js/app.js`
   - `gui/web/static/js/api.js`
   - module JS liên quan tính năng
5. Nếu sửa DB, luôn kiểm tra:
   - `schema.sql`
   - code SQL trong backend
6. Không đề xuất sửa `dist` hay `__pycache__` nếu source gốc còn tồn tại.
7. Nếu thấy mâu thuẫn giữa file này với file khác, phải nêu rõ và đề xuất cách thống nhất.

---

## 18) Prompt ngắn để dán kèm khi gửi cho chat khác

Bạn có thể gửi thêm đoạn này cùng tài liệu:

```text
Hãy dùng tài liệu Markdown này làm ngữ cảnh chuẩn của project Elevator AI / Sunybot.
Tôi muốn bạn hiểu đúng runtime, kiến trúc, vai trò từng file, và chỉ sửa đúng file cần thiết.
Khi trả lời, luôn chỉ ra:
1) file bắt buộc sửa
2) file có thể bị ảnh hưởng
3) file không nên sửa
4) nếu có điểm mâu thuẫn trong code/schema/frontend thì nêu rõ trước khi đề xuất sửa
Không sửa file build/cache nếu source gốc còn tồn tại.
```

---

## 19) Kết luận ngắn gọn

Project này là một hệ thống **thang máy thông minh tích hợp chatbot Sunybot**, gồm:

- backend FastAPI
- knowledge base MySQL
- semantic matching + embedding
- fallback LLM qua Ollama
- frontend web nhiều màn hình
- voice interaction
- tool desktop phụ

Điểm khó của project không nằm ở số lượng file, mà nằm ở việc nó có:

- nhiều lớp UI song song
- code mới và code cũ cùng tồn tại
- schema/code có dấu hiệu lệch nhau
- một số phần vẫn mock/demo

Vì vậy, mọi chỉnh sửa nên bắt đầu từ việc xác định **runtime thật đang dùng file nào**, rồi mới sửa đúng tầng.

---

## 20) Những file/chỗ chưa được xác minh 100% trong phiên làm việc này

Các phần sau có trong cây thư mục nhưng chưa được đọc sâu hoặc chưa có source gốc đầy đủ trong phiên này:

- `pyproject.toml`
- source thật của frontend build mới tương ứng với `gui/web/dist/assets/index-C94rDJOP.js`
- file native source `suny_core/native/sunycore.cpp`
- `requirements.txt`
- bất kỳ service ngoài `api.py` nào có thể đang được dùng nhưng chưa gửi

Nếu một chat mới cần chốt chính xác dependency/build/runtime nâng cao, nên kiểm tra thêm các file đó.

