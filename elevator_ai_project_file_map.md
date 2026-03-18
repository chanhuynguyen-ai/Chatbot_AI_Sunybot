# Bản đồ file project `elevator_ai_project`

## Cách để hiểu đúng vai trò từng file trong project nhiều file

Để hiểu **từng file có vai trò gì** một cách hiệu quả và đủ sâu để biết **nên sửa file nào khi thay đổi tính năng**, cách làm đúng là theo 4 lớp:

1. **Nhìn cây thư mục để phân tầng**
   - `backend/` là tầng xử lý nghiệp vụ và API.
   - `config/` là tầng cấu hình.
   - `database/` là tầng schema, seed và script dữ liệu.
   - `gui/` là tầng giao diện desktop/web.
   - `dist/`, `__pycache__/`, `*.pyc` là build/cache, chủ yếu để chạy, không phải nơi nên sửa logic.

2. **Đọc file entrypoint trước**
   - Backend: `backend/api.py`
   - Desktop GUI: `gui/main.py`
   - Web app: `gui/web/index.html`, `gui/web/static/js/app.js`
   Các file này cho biết toàn hệ thống được nối với nhau như thế nào.

3. **Map quan hệ gọi nhau**
   - Backend route gọi engine nào.
   - Engine gọi service nào.
   - Frontend gọi API nào.
   - HTML dùng JS/CSS nào.
   Khi đã có sơ đồ gọi nhau, việc sửa đúng file sẽ rõ ràng hơn nhiều.

4. **Gắn vai trò file với loại thay đổi**
   - Đổi API -> sửa route/API layer.
   - Đổi pipeline chatbot -> sửa orchestrator.
   - Đổi semantic search -> sửa matcher/embedding.
   - Đổi voice/chat/call/status -> sửa đúng module frontend tương ứng.
   - Đổi DB schema -> sửa SQL/schema/config liên quan.

---

## Cảnh báo các file có thể bỏ qua khi phân tích logic

Những file/thư mục sau **không phải nơi nên sửa logic chính**:

- `__pycache__/`
- `*.pyc`
- `gui/web/dist/*`
- `*.save`
- `cloudflared-linux-amd64.deb`
- `packages.microsoft.gpg`

Chúng chủ yếu là cache, output build hoặc artifact cài đặt.

---

## Cây thư mục và vai trò từng file

```text
.
├── backend (thư mục backend chính; chứa API, engine, service, utility, test)
│   ├── api.py (entrypoint FastAPI; khai báo route chat/health/static và gọi ChatbotEngine)
│   ├── build_embeddings.py (script build/cập nhật embedding cho dữ liệu prompt trong DB)
│   ├── chatbot_engine.py (orchestrator trung tâm; quyết định pipeline xử lý câu hỏi)
│   ├── embedding_service.py (service tạo vector embedding từ văn bản qua Ollama)
│   ├── employee_service.py (service tra cứu nhân viên theo mã/tên và format trả lời nhân viên)
│   ├── __init__.py (đánh dấu backend là package Python)
│   ├── logger.py (thiết lập logging ghi file và console)
│   ├── ollama_service.py (service gọi LLM Ollama để sinh câu trả lời fallback)
│   ├── __pycache__ (cache Python; bỏ qua khi phân tích logic)
│   ├── schemas.py (schema request/response cho backend chat)
│   ├── semantic_matcher.py (so khớp ngữ nghĩa và exact match với dữ liệu prompt-answer trong DB)
│   ├── test_chatbot.py (test kiểm tra luồng chatbot)
│   └── text_utils.py (utility chuẩn hóa tiếng Việt, bỏ dấu, làm sạch text)
├── cloudflared-linux-amd64.deb (gói cài cloudflared; artifact cài đặt/tunnel)
├── config (thư mục cấu hình hệ thống)
│   ├── db_config.py (cấu hình và tạo kết nối MySQL bằng biến môi trường)
│   ├── db_config.py.save (bản sao lưu file cấu hình DB)
│   ├── __init__.py (đánh dấu config là package Python)
│   └── __pycache__ (cache Python; bỏ qua)
├── database (thư mục schema, seed và script dữ liệu)
│   ├── __pycache__ (cache Python; bỏ qua)
│   ├── remove_vietnamese_accent.py (utility bỏ dấu tiếng Việt và script convert dữ liệu text trong DB)
│   ├── schema.sql (khai báo cấu trúc bảng dữ liệu của hệ thống)
│   └── seed.sql (nạp dữ liệu mẫu ban đầu cho intents/prompts/answers/employees)
├── gui (thư mục giao diện và ứng dụng người dùng)
│   ├── gui (GUI desktop/phụ trợ)
│   │   └── mysql_admin_gui_pk.py (GUI desktop PyQt để quản trị dữ liệu MySQL theo primary key)
│   ├── __init__.py (đánh dấu gui là package Python)
│   ├── main.py (GUI desktop chatbot PyQt để test/hỏi đáp trực tiếp)
│   └── web (thư mục giao diện web)
│       ├── assets (thư mục tài nguyên frontend)
│       ├── dist (frontend đã build; dùng chạy/deploy, không nên sửa trực tiếp)
│       │   ├── assets (CSS/JS bundle đã build)
│       │   │   ├── index-bn7l8BoE.css (CSS bundle build output; không nên sửa trực tiếp)
│       │   │   └── index-C94rDJOP.js (JS bundle build output; không nên sửa trực tiếp)
│       │   ├── favicon.ico (icon web app đã build)
│       │   └── index.html (HTML entry của app đã build)
│       ├── index.html (khung web app chính; gom nhiều màn hình như home/call/assistant/sos/guide/maint)
│       ├── pages (các trang web chức năng riêng)
│       │   ├── assistant.html (trang trợ lý ảo/chat)
│       │   └── call.html (trang gọi tầng)
│       ├── static (source frontend thật; nơi nên sửa giao diện và logic web)
│       │   ├── app.css (CSS chính của kiosk/web app hiện đại)
│       │   ├── app.js (bootstrap layer của static; nối UI tổng với module frontend)
│       │   ├── favicon.ico (icon website)
│       │   ├── js (thư mục module logic frontend theo tính năng)
│       │   │   ├── api.js (lớp gọi API backend chung)
│       │   │   ├── app.js (file khởi động/orchestrator của frontend web)
│       │   │   ├── botui.js (điều khiển trạng thái bot và phát TTS)
│       │   │   ├── call.js (logic gọi tầng)
│       │   │   ├── chat.js (logic chat frontend)
│       │   │   ├── dom.js (gom DOM reference dùng chung)
│       │   │   ├── maint.js (logic bảo trì/demo maintenance)
│       │   │   ├── sos.js (logic SOS)
│       │   │   ├── status.js (logic cập nhật trạng thái thang máy)
│       │   │   ├── voice.js (logic voice/STT/wake word)
│       │   │   └── weather.js (logic thời tiết)
│       │   ├── style.css (CSS cho chat UI đơn giản/legacy)
│       │   └── ui.js (UI helper dùng chung: topbar, toast, escapeHtml)
│       └── templates
│           └── chat.html (template chat web đơn giản kiểu cũ)
├── __init__.py (đánh dấu thư mục gốc là package Python)
├── install_jetson.sh (script cài đặt môi trường cho Jetson Nano, build native module và hướng dẫn chạy backend)
├── package.json (metadata Node/frontend rất tối giản; hiện hầu như chưa quản lý frontend thực tế) 
├── packages.microsoft.gpg (key hệ thống để cài package Microsoft; artifact cài đặt)
├── pyproject.toml (cấu hình build/dependency Python hiện đại)
└── setup.py (build native extension `sunycore_native` bằng pybind11/C++)
```

---

## Bảng vai trò từng file

| File | Vai trò chính | Được gọi khi nào | File liên quan | Nên sửa khi nào |
|---|---|---|---|---|
| `backend/api.py` | Entry API FastAPI | Khi backend chạy, khi frontend gọi `/chat`, `/health`, static routes | `chatbot_engine.py`, `schemas.py` hoặc model request/response nội bộ, frontend `api.js` | Thêm/sửa route, đổi response API, serve UI |
| `backend/build_embeddings.py` | Build/update embeddings cho DB | Khi cập nhật kho prompt/tri thức | `embedding_service.py`, `db_config.py`, bảng `prompts` | Đổi cách build embedding, đổi model/vector flow |
| `backend/chatbot_engine.py` | Orchestrator xử lý câu hỏi | Mỗi request chat | `employee_service.py`, `semantic_matcher.py`, `embedding_service.py`, `ollama_service.py`, `db_config.py` | Đổi pipeline chatbot, thứ tự ưu tiên, fallback |
| `backend/embedding_service.py` | Tạo embedding qua Ollama | Trước semantic match, khi build embeddings | `text_utils.py`, Ollama endpoint, `semantic_matcher.py` | Đổi model embedding, timeout, preprocessing |
| `backend/employee_service.py` | Tìm nhân viên theo mã/tên | Khi câu hỏi liên quan nhân viên | `db_config.py`, `chatbot_engine.py` | Đổi logic nhân viên, format thông tin |
| `backend/__init__.py` | Package marker | Khi import package backend | Các file trong backend | Hiếm khi cần sửa |
| `backend/logger.py` | Thiết lập logging | Khi app khởi động / runtime cần log | `api.py` hoặc startup script | Đổi format log, nơi lưu log |
| `backend/ollama_service.py` | Gọi LLM fallback | Khi DB/employee flow không trả được câu trả lời | `chatbot_engine.py`, Ollama API | Đổi prompt, model, độ dài/trạng thái trả lời |
| `backend/schemas.py` | Định nghĩa schema chat | Khi validate request/response | `api.py` | Đổi contract API |
| `backend/semantic_matcher.py` | Exact match + cosine similarity | Sau khi có embedding/query normalized | `db_config.py`, `text_utils.py`, `embedding_service.py` | Cải thiện semantic search, threshold, matching |
| `backend/test_chatbot.py` | Test integration chatbot | Khi chạy test | `chatbot_engine.py`, DB test data | Thêm/chỉnh test hồi quy |
| `backend/text_utils.py` | Chuẩn hóa tiếng Việt/text | Trước embed/match | `remove_vietnamese_accent.py`, `embedding_service.py`, `semantic_matcher.py` | Đổi normalize, xử lý dấu/ký tự |
| `config/db_config.py` | Kết nối MySQL | Mỗi khi backend/database service cần DB | `employee_service.py`, `semantic_matcher.py`, `chatbot_engine.py` | Đổi host/user/password/dbname, connection policy |
| `config/db_config.py.save` | Bản sao lưu config | Không nên dùng runtime chính | `db_config.py` | Thường bỏ qua |
| `database/remove_vietnamese_accent.py` | Utility bỏ dấu + script convert dữ liệu | Khi normalize dữ liệu hoặc chạy convert DB | `text_utils.py`, dữ liệu DB | Đổi quy tắc bỏ dấu/convert |
| `database/schema.sql` | Định nghĩa bảng dữ liệu | Khi khởi tạo DB | `seed.sql`, toàn bộ backend service | Đổi schema, thêm bảng/cột/index |
| `database/seed.sql` | Dữ liệu seed ban đầu | Khi nạp dữ liệu mới | `schema.sql`, `semantic_matcher.py`, `employee_service.py` | Đổi dữ liệu mẫu, intents, nhân viên |
| `gui/gui/mysql_admin_gui_pk.py` | GUI quản trị MySQL desktop | Khi quản trị dữ liệu thủ công | DB MySQL, các bảng backend dùng | Đổi tool admin, thêm filter/import/export |
| `gui/__init__.py` | Package marker | Khi import `gui` | `main.py`, module GUI khác | Hiếm khi cần sửa |
| `gui/main.py` | GUI chatbot desktop PyQt | Khi chạy app desktop test chatbot | `employee_service.py` hoặc backend logic gọi trực tiếp | Đổi UI desktop chatbot |
| `gui/web/dist/assets/index-bn7l8BoE.css` | CSS bundle đã build | Khi chạy frontend build | `dist/index.html` | Không nên sửa trực tiếp |
| `gui/web/dist/assets/index-C94rDJOP.js` | JS bundle đã build | Khi chạy frontend build | `dist/index.html` | Không nên sửa trực tiếp |
| `gui/web/dist/index.html` | Entry HTML cho bản build | Khi deploy frontend build | bundle CSS/JS build | Gần như không sửa trực tiếp |
| `gui/web/index.html` | App shell web chính | Khi mở web app chính | `static/ui.js`, `static/app.css`, `static/js/app.js` | Đổi bố cục tổng thể, thêm màn/tab |
| `gui/web/pages/assistant.html` | Trang trợ lý/chat riêng | Khi mở màn assistant | `static/js/chat.js`, `api.js`, `voice.js` | Đổi UX chat riêng |
| `gui/web/pages/call.html` | Trang gọi tầng riêng | Khi mở màn call | `static/js/call.js`, `api.js` | Đổi UI/flow gọi tầng |
| `gui/web/static/app.css` | CSS chính web app | Khi render kiosk/web app | `web/index.html`, UI elements | Đổi theme, layout, visual app |
| `gui/web/static/app.js` | Bootstrap layer cho static | Khi source web app khởi động | `ui.js`, `static/js/app.js` | Đổi entry/bootstrap frontend |
| `gui/web/static/style.css` | CSS chat legacy | Khi dùng template chat cũ | `templates/chat.html` | Đổi UI chat cũ |
| `gui/web/static/ui.js` | UI helper chung | Khi render topbar/toast/tabbar | `web/index.html`, `static/app.js` | Đổi topbar, toast, helper UI |
| `gui/web/static/js/api.js` | API client frontend | Mỗi khi frontend gọi backend | `chat.js`, `call.js`, `status.js`, `sos.js`, `weather.js` | Đổi endpoint/payload/error handling |
| `gui/web/static/js/app.js` | Orchestrator frontend web | Khi app web khởi động | `api.js`, `status.js`, `weather.js`, `voice.js`, `maint.js`, `dom.js` | Đổi boot flow, nav, polling, binding |
| `gui/web/static/js/botui.js` | Trạng thái bot + TTS | Khi bot nghe/nói/trả lời | `chat.js`, `voice.js` | Đổi visual bot, TTS state |
| `gui/web/static/js/call.js` | Logic gọi tầng | Khi user bấm gọi tầng | `api.js`, HTML call screen | Đổi rule tầng khóa, payload call |
| `gui/web/static/js/chat.js` | Logic chat frontend | Khi user gửi tin nhắn chat | `api.js`, `botui.js`, `voice.js`, DOM chat | Đổi UX chat, render answer, history |
| `gui/web/static/js/dom.js` | Gom DOM refs | Khi frontend cần truy cập phần tử HTML | Hầu hết các module JS | Đổi ID phần tử, thêm màn mới |
| `gui/web/static/js/maint.js` | Màn maintenance/demo | Khi vào màn bảo trì | localStorage, DOM, có thể gọi LLM demo | Đổi maintenance flow, auth thật |
| `gui/web/static/js/sos.js` | Logic gửi SOS | Khi user bấm SOS | `api.js`, `status.js`, DOM | Đổi payload SOS, retry, UX xác nhận |
| `gui/web/static/js/status.js` | Cập nhật trạng thái thang | Poll định kỳ mỗi giây | `api.js`, `dom.js`, UI home/topbar/maint/sos | Đổi mapping status, field hiển thị |
| `gui/web/static/js/voice.js` | Voice/STT/wake word | Khi bật voice hoặc wake word | `chat.js`, `botui.js`, Web Speech API | Đổi wake word, STT flow, restart logic |
| `gui/web/static/js/weather.js` | Logic thời tiết | Poll định kỳ, refresh topbar/home | `api.js`, DOM | Đổi format/source weather |
| `gui/web/templates/chat.html` | Template chat web cũ | Khi route template cũ được mở | `static/style.css`, `static/js/chat.js` | Đổi flow chat legacy |
| `__init__.py` | Package marker gốc | Khi import project root | Toàn project Python | Hiếm khi cần sửa |
| `install_jetson.sh` | Cài môi trường Jetson + build native | Khi setup trên Jetson Nano | `setup.py`, `requirements.txt`, `backend.api:app` | Đổi quy trình cài đặt/deploy |
| `package.json` | Metadata Node tối giản | Khi dùng npm, hiện chủ yếu để metadata | Frontend tooling (nếu mở rộng) | Bổ sung scripts/deps frontend thật |
| `pyproject.toml` | Cấu hình build/dependency Python | Khi build/cài package Python | `setup.py`, môi trường Python | Đổi metadata/build backend |
| `setup.py` | Build native extension `sunycore_native` | Khi chạy `build_ext --inplace` | `install_jetson.sh`, source C++ `suny_core/native/sunycore.cpp` | Đổi module native/build flags |
| `cloudflared-linux-amd64.deb` | Artifact cài cloudflared | Khi cài tunnel | Hạ tầng/deploy | Thường bỏ qua logic app |
| `packages.microsoft.gpg` | Artifact key cài package | Khi setup package system | Hạ tầng hệ điều hành | Thường bỏ qua logic app |

---

## Sơ đồ phụ thuộc giữa các file

### 1) Backend

```text
frontend / desktop GUI
   -> backend/api.py
      -> chatbot_engine.py
         -> employee_service.py
            -> config/db_config.py
         -> embedding_service.py
            -> text_utils.py
               -> database/remove_vietnamese_accent.py
         -> semantic_matcher.py
            -> config/db_config.py
            -> text_utils.py
         -> ollama_service.py
         -> log_chat() -> config/db_config.py

build_embeddings.py
   -> embedding_service.py
   -> config/db_config.py
   -> bảng prompts trong database
```

### 2) Database

```text
schema.sql
   -> tạo bảng intents / prompts / answers / employees / chat_logs
seed.sql
   -> nạp dữ liệu ban đầu vào các bảng trên

backend services
   -> dùng db_config.py để truy cập schema + seed data
```

### 3) Frontend web

```text
gui/web/index.html
   -> gui/web/static/app.css
   -> gui/web/static/ui.js
   -> gui/web/static/app.js
      -> gui/web/static/js/app.js
         -> api.js
         -> dom.js
         -> status.js
         -> weather.js
         -> voice.js
         -> maint.js
         -> chat.js
         -> call.js
         -> sos.js
         -> botui.js

api.js
   -> backend/api.py endpoints
```

### 4) Desktop GUI

```text
gui/main.py
   -> gọi chatbot/employee flow để test desktop

gui/gui/mysql_admin_gui_pk.py
   -> kết nối MySQL trực tiếp để quản trị dữ liệu
```

---

## Danh sách file entrypoint

### Entrypoint runtime chính
- `backend/api.py` -> entrypoint backend HTTP/FastAPI
- `gui/main.py` -> entrypoint GUI desktop chatbot
- `gui/web/index.html` -> entrypoint source web app chính
- `gui/web/dist/index.html` -> entrypoint bản build frontend

### Entrypoint script/tool
- `backend/build_embeddings.py` -> entrypoint build embeddings
- `backend/test_chatbot.py` -> entrypoint test chatbot
- `gui/gui/mysql_admin_gui_pk.py` -> entrypoint tool quản trị DB
- `install_jetson.sh` -> entrypoint setup môi trường Jetson
- `setup.py` -> entrypoint build native extension

---

## Danh sách file nên sửa cho từng loại thay đổi

### 1) Đổi API hoặc route backend
- `backend/api.py`
- nếu đổi contract dữ liệu: `backend/schemas.py`
- nếu frontend đang gọi endpoint đó: `gui/web/static/js/api.js`

### 2) Đổi pipeline chatbot
- `backend/chatbot_engine.py`
- có thể kèm `backend/employee_service.py`
- có thể kèm `backend/semantic_matcher.py`
- có thể kèm `backend/ollama_service.py`

### 3) Cải thiện hiểu câu hỏi/semantic search
- `backend/semantic_matcher.py`
- `backend/embedding_service.py`
- `backend/text_utils.py`
- `database/remove_vietnamese_accent.py`
- nếu dữ liệu prompt chưa tốt: `database/seed.sql` hoặc dữ liệu DB thật

### 4) Đổi logic tra cứu nhân viên
- `backend/employee_service.py`
- có thể kèm `database/schema.sql`, `database/seed.sql`

### 5) Đổi prompt/model AI fallback
- `backend/ollama_service.py`
- nếu cần đổi orchestration: `backend/chatbot_engine.py`

### 6) Đổi cấu trúc DB
- `database/schema.sql`
- `database/seed.sql`
- `config/db_config.py`
- các backend service đang dùng bảng/cột đó

### 7) Đổi dữ liệu seed/intents/FAQ/nhân viên
- `database/seed.sql`
- nếu cần build lại embeddings: `backend/build_embeddings.py`

### 8) Đổi giao diện web tổng thể
- `gui/web/index.html`
- `gui/web/static/app.css`
- `gui/web/static/ui.js`

### 9) Đổi logic chat web
- `gui/web/static/js/chat.js`
- `gui/web/static/js/api.js`
- nếu có voice/TTS: `gui/web/static/js/botui.js`, `gui/web/static/js/voice.js`
- nếu là trang riêng: `gui/web/pages/assistant.html`

### 10) Đổi voice assistant / wake word
- `gui/web/static/js/voice.js`
- `gui/web/static/js/botui.js`

### 11) Đổi gọi tầng
- `gui/web/static/js/call.js`
- `gui/web/static/js/api.js`
- `gui/web/pages/call.html`

### 12) Đổi màn hình trạng thái thang máy
- `gui/web/static/js/status.js`
- `gui/web/static/js/dom.js`
- `gui/web/static/app.css`

### 13) Đổi SOS
- `gui/web/static/js/sos.js`
- `gui/web/static/js/api.js`

### 14) Đổi weather
- `gui/web/static/js/weather.js`
- `gui/web/static/js/api.js`

### 15) Đổi maintenance dashboard
- `gui/web/static/js/maint.js`
- `gui/web/index.html`

### 16) Đổi chat/template cũ
- `gui/web/templates/chat.html`
- `gui/web/static/style.css`
- `gui/web/static/js/chat.js`

### 17) Đổi GUI desktop chatbot
- `gui/main.py`

### 18) Đổi công cụ quản trị DB
- `gui/gui/mysql_admin_gui_pk.py`

### 19) Đổi quy trình cài đặt/deploy Jetson
- `install_jetson.sh`
- `setup.py`
- `pyproject.toml`
- `package.json` (nếu sau này quản lý frontend nghiêm túc hơn)

---

## Tóm tắt kiến trúc tổng thể

### Backend
- `api.py` nhận request từ web/desktop.
- `chatbot_engine.py` là bộ não điều phối.
- `employee_service.py` xử lý nhân viên.
- `semantic_matcher.py` + `embedding_service.py` xử lý tìm kiếm ngữ nghĩa.
- `ollama_service.py` là fallback LLM.
- `text_utils.py` + `remove_vietnamese_accent.py` chuẩn hóa tiếng Việt.

### Database
- `schema.sql` định nghĩa cấu trúc.
- `seed.sql` cung cấp dữ liệu đầu vào cho matcher/nhân viên.
- `db_config.py` nối backend với MySQL.

### Frontend
- `web/index.html` là app shell.
- `static/js/app.js` là orchestrator frontend.
- `api.js` là cổng gọi backend.
- `chat.js`, `voice.js`, `call.js`, `status.js`, `sos.js`, `weather.js`, `maint.js` là các module tính năng.
- `dom.js` gom DOM.
- `ui.js` là helper UI dùng chung.

### Desktop/tooling
- `gui/main.py` là app desktop test chatbot.
- `mysql_admin_gui_pk.py` là tool admin MySQL.
- `install_jetson.sh` + `setup.py` là lớp setup/deploy/native build.

---

## Ghi chú cuối
