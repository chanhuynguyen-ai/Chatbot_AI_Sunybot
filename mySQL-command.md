"host": "localhost",
"user": "elevator_ai",
"password": "elevator123",
"database": "elevator_ai",
"charset": "utf8mb4"

#Lệnh code database trong mysql:

Vào MySQL
```bash
sudo mysql
```
hoặc
```bash
mysql -u elevator_bot -p
```

Xem tất cả DATABASE
```bash
SHOW DATABASES;
```

Chọn database của bạn

```bash
USE elevator_ai;
```

Xem tất cả TABLE trong database

```bash
SHOW TABLES;
```

Xem cấu trúc 1 table (các cột)

```bash
DESCRIBE intents;
DESCRIBE prompts;
DESCRIBE answers;
DESCRIBE chat_logs;
DESCRIBE employees;
```

Xem toàn bộ dữ liệu trong table

```bash
SELECT * FROM intents;
SELECT * FROM prompts;
SELECT * FROM answers;
SELECT * FROM chat_logs;
SELECT * FROM employees;
```

 Xem dữ liệu có chọn lọc (khuyến nghị)

```bash

SELECT intent_id, intent_name FROM intents;
SELECT prompt_text FROM prompts;

SELECT full_name, position, department FROM employees;

```

 Xem liên kết Prompt – Answer (debug chatbot)

```bash
SELECT 
    i.intent_name,
    p.prompt_text,
    a.answer_text
FROM intents i
JOIN prompts p ON i.intent_id = p.intent_id
JOIN answers a ON i.intent_id = a.intent_id;

```
check local host:
```bash

SELECT user, host FROM mysql.user;

```

Lệnh kiểm tra TẤT CẢ prompt thuộc intent greeting

```bash

SELECT 
    p.prompt_id,
    p.prompt_text,
    i.intent_name,
    p.intent_id
FROM prompts p
JOIN intents i ON p.intent_id = i.intent_id
WHERE i.intent_name = 'greeting'
ORDER BY p.prompt_id;

```

Thoát MySQL


```bash
EXIT;
```

#TỔNG HỢP CÁC LỆNH BỔ SUNG THƯ VIỆN TRONG MYSQL:

1️⃣ INSERT DỮ LIỆU VÀO BẢNG employees

👉 Dùng khi thêm nhân viên để chatbot tra cứu theo mã NV / họ tên
```bash
INSERT INTO employees
(
    employee_code,
    full_name,
    birth_year,
    position,
    department,
    hometown,
    phone,
    email,
    photo_path
)
VALUES
(
    'NV181',
    'Lê Thị Nghi Lộc',
    2004,
    'Kỹ sư vận hành',
    'Kỹ thuật',
    'TP. Hồ Chí Minh',
    '0909123456',
    'nghiloc@company.com',
    NULL
```

2️⃣ INSERT DỮ LIỆU VÀO BẢNG intents

👉 Mỗi intent đại diện cho 1 nhóm câu hỏi
```bash
INSERT INTO intents
(intent_name, domain, description)
VALUES
('elevator_load', 'elevator', 'Tải trọng tối đa của thang máy
```

3️⃣ INSERT DỮ LIỆU VÀO BẢNG prompts

👉 Các câu hỏi mẫu để match semantic
```bash
INSERT INTO prompts
(intent_id, prompt_text)
VALUES
(1, 'Tốc độ thang máy là bao nhiêu');

INSERT INTO prompts
(intent_id, prompt_text)
VALUES
(1, 'Thang máy chạy nhanh hay chậm');
```

📌 Sau khi insert prompt, bạn cần build embedding lại:
```
python3 -m backend.build_embeddings
```

4️⃣ INSERT DỮ LIỆU VÀO BẢNG answers

👉 Câu trả lời chuẩn cho intent
```bash
INSERT INTO answers
(intent_id, answer_text)
VALUES
(1, 'Tốc độ thang máy hiện tại là 1.2 m/s, đảm bảo an toàn khi vận hành.');
```

📌 1 intent → có thể có nhiều prompt, nhưng thường 1 answer chính

5️⃣ INSERT TRỌN BỘ 1 INTENT (THỰC TẾ NHẤT)

👉 Ví dụ: Tải trọng thang máy
```bash
-- 1. Intent
INSERT INTO intents (intent_name, domain, description)
VALUES ('elevator_capacity', 'elevator', 'Tải trọng thang máy');

SET @intent_id = LAST_INSERT_ID();

-- 2. Prompts
INSERT INTO prompts (intent_id, prompt_text)
VALUES
(@intent_id, 'Thang máy chở được bao nhiêu kg'),
(@intent_id, 'Tải trọng tối đa của thang máy là bao nhiêu'),
(@intent_id, 'Thang máy chịu được bao nhiêu người');

-- 3. Answer
INSERT INTO answers (intent_id, answer_text)
VALUES
(@intent_id, 'Thang máy có tải trọng tối đa 1000 kg, tương đương khoảng 13 người.');
```

📌 Đây là cách làm chuẩn sản phẩm, rất nên ghi vào báo cáo.

6️⃣ INSERT DỮ LIỆU VÀO chat_logs (CHỈ ĐỂ TEST)

👉 Bình thường bảng này backend tự ghi, nhưng bạn có thể test:
```bash
INSERT INTO chat_logs
(question, intent_name, confidence)
VALUES
('Tốc độ thang máy là bao nhiêu', 'elevator_speed', 0.82);
```
7️⃣ MẪU SEED DỮ LIỆU (DÙNG CHO seed.sql)

Bạn có thể viết 1 file seed:
```bash
-- Intent
INSERT INTO intents (intent_name, domain, description)
VALUES ('greeting', 'general', 'Câu chào hỏi');

SET @greeting_id = LAST_INSERT_ID();

-- Prompts
INSERT INTO prompts (intent_id, prompt_text)
VALUES
(@greeting_id, 'xin chào'),
(@greeting_id, 'hello'),
(@greeting_id, 'chào bạn');

-- Answers
INSERT INTO answers (intent_id, answer_text)
VALUES
(@greeting_id, 'Xin chào, tôi là Sunybot, tôi có thể hỗ trợ gì cho bạn?');
```
8️⃣ KIỂM TRA SAU KHI INSERT
```bash
SELECT i.intent_name, p.prompt_text, a.answer_text
FROM intents i
JOIN prompts p ON i.intent_id = p.intent_id
JOIN answers a ON i.intent_id = a.intent_id;
```


