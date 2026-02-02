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





