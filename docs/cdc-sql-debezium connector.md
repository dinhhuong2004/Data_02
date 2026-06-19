# SQL Server CDC + Debezium + Kafka Setup Guide

## 1. Mục tiêu

Luồng dữ liệu:

```text
SQL Server
    ↓ CDC
Debezium Connector
    ↓
Kafka Topic
    ↓
Consumer / Spark / Flink / Iceberg
```

---

# 2. Điều kiện tiên quyết

## SQL Server

Kiểm tra version:

```sql
SELECT @@VERSION;
```

CDC hỗ trợ:

* SQL Server 2016+
* SQL Server 2019
* SQL Server 2022

---

## SQL Server Agent

CDC yêu cầu SQL Server Agent chạy.

Kiểm tra:

```sql
SELECT servicename,status_desc
FROM sys.dm_server_services;
```

Kết quả:

```text
SQL Server Agent (MSSQLSERVER) | Running
```

---

## Kafka

Kiểm tra broker:

```bash
docker ps
```

---

## Debezium Connect

Kiểm tra:

```bash
curl http://localhost:8083/
```

---

# 3. Tạo Database Test

```sql
CREATE DATABASE CDC_Test;
GO
```

---

# 4. Enable CDC cho Database

```sql
USE CDC_Test;
GO

EXEC sys.sp_cdc_enable_db;
GO
```

Kiểm tra:

```sql
SELECT name,is_cdc_enabled
FROM sys.databases
WHERE name='CDC_Test';
```

Kết quả:

```text
CDC_Test | 1
```

---

# 5. Tạo bảng Test

```sql
USE CDC_Test;
GO

CREATE TABLE dbo.Users
(
    UserId INT IDENTITY(1,1) PRIMARY KEY,
    UserName NVARCHAR(100),
    Email NVARCHAR(255),
    CreatedDate DATETIME2 DEFAULT GETDATE()
);
GO
```

---

# 6. Enable CDC cho Table

```sql
EXEC sys.sp_cdc_enable_table
    @source_schema='dbo',
    @source_name='Users',
    @role_name=NULL;
GO
```

---

# 7. Kiểm tra CDC

## Kiểm tra table được track CDC

```sql
SELECT
    name,
    is_tracked_by_cdc
FROM sys.tables
WHERE name='Users';
```

Kết quả:

```text
Users | 1
```

---

## Kiểm tra Capture Instance

```sql
EXEC sys.sp_cdc_help_change_data_capture;
```

Kết quả:

```text
source_schema = dbo
source_table  = Users
capture_instance = dbo_Users
```

---

## Kiểm tra CDC Jobs

```sql
EXEC sys.sp_cdc_help_jobs;
```

Kết quả:

```text
capture
cleanup
```

---

# 8. Tạo dữ liệu test

```sql
INSERT INTO dbo.Users(UserName,Email)
VALUES
('User 1','user1@test.com'),
('User 2','user2@test.com');
```

---

# 9. Kiểm tra CDC Change Table

```sql
SELECT *
FROM cdc.dbo_Users_CT;
```

Nếu có dữ liệu:

```text
__$operation = 2
```

CDC hoạt động bình thường.

---

# 10. Cấu hình Debezium Connector

File:

sqlserver-cdc-test.json

```json
{
  "name": "sqlserver-cdc-test",
  "config": {
    "connector.class": "io.debezium.connector.sqlserver.SqlServerConnector",

    "database.hostname": "sqlserver",
    "database.port": "1433",

    "database.user": "sa",
    "database.password": "Wenami@12345",

    "database.names": "CDC_Test",

    "table.include.list": "dbo.Users",

    "topic.prefix": "cdc-test",

    "snapshot.mode": "initial",

    "database.encrypt": "false",
    "database.trustServerCertificate": "true",

    "include.schema.changes": "false",

    "schema.history.internal.kafka.bootstrap.servers": "kafka:29092",
    "schema.history.internal.kafka.topic": "schemahistory.cdc-test"
  }
}
```

---

# 11. Tạo Connector

```bash
curl -X POST \
http://localhost:8083/connectors \
-H "Content-Type: application/json" \
-d @sqlserver-cdc-test.json
```

---

# 12. Kiểm tra Connector

```bash
curl http://localhost:8083/connectors/sqlserver-cdc-test/status
```

Kết quả:

```json
{
  "connector": {
    "state": "RUNNING"
  },
  "tasks": [
    {
      "state": "RUNNING"
    }
  ]
}
```

---

# 13. Kiểm tra Topic

Liệt kê topic:

```bash
docker exec -it kafka kafka-topics \
--bootstrap-server kafka:29092 \
--list
```

Topic CDC:

```text
cdc-test.CDC_Test.dbo.Users
```

---

# 14. Đọc dữ liệu CDC

```bash
docker exec -it kafka kafka-console-consumer \
--bootstrap-server kafka:29092 \
--topic cdc-test.CDC_Test.dbo.Users \
--from-beginning
```

---

# 15. Test Realtime

Insert:

```sql
INSERT INTO dbo.Users(UserName,Email)
VALUES ('Realtime User','rt@test.com');
```

Update:

```sql
UPDATE dbo.Users
SET Email='updated@test.com'
WHERE UserId=1;
```

Delete:

```sql
DELETE dbo.Users
WHERE UserId=1;
```

---

# 16. Các lỗi thường gặp

## Lỗi

```text
The specified '@srv' is invalid
```

Nguyên nhân:

* SQL Agent metadata lỗi
* CDC Job không tạo được

Kiểm tra:

```sql
SELECT @@SERVERNAME;
EXEC sp_helpserver;
```

---

## Lỗi

```text
No table on connector's include list has enabled CDC
```

Nguyên nhân:

Sai:

```json
"table.include.list": "CDC_Test.dbo.Users"
```

Đúng:

```json
"table.include.list": "dbo.Users"
```

---

## Lỗi

```text
table is not on connector's table include list
```

Nguyên nhân:

Debezium không match được schema/table filter.

Sửa:

```json
"table.include.list": "dbo.Users"
```

---

## Lỗi

```text
LEADER_NOT_AVAILABLE
```

Nguyên nhân:

Kafka broker chưa sẵn sàng hoặc listener cấu hình sai.

Kiểm tra:

```bash
docker logs kafka
```

---

## Connector RUNNING nhưng không có message

Kiểm tra CDC table:

```sql
SELECT *
FROM cdc.dbo_Users_CT;
```

Nếu có dữ liệu:

```text
CDC OK
Debezium/Kafka lỗi
```

Nếu không có dữ liệu:

```text
CDC Capture Job lỗi
```

---

# 17. Checklist Debug

## SQL Server

```sql
SELECT @@SERVERNAME;

EXEC sys.sp_cdc_help_jobs;

EXEC sys.sp_cdc_help_change_data_capture;

SELECT *
FROM cdc.dbo_Users_CT;
```

---

## Debezium

```bash
curl http://localhost:8083/connectors/sqlserver-cdc-test/status

docker logs connect -f
```

---

## Kafka

```bash
docker exec -it kafka kafka-topics \
--bootstrap-server kafka:29092 \
--list
```

```bash
docker exec -it kafka kafka-console-consumer \
--bootstrap-server kafka:29092 \
--topic cdc-test.CDC_Test.dbo.Users \
--from-beginning
```

---

# 18. Luồng xác nhận thành công

```text
Users Table
    ↓
cdc.dbo_Users_CT
    ↓
Debezium Connector RUNNING
    ↓
Kafka Topic Created
    ↓
Message Count > 0
    ↓
Realtime CDC Working
```
# 19. SQL Test CDC Realtime

## 19.1 Insert dữ liệu mới

```sql
USE CDC_Test;
GO

INSERT INTO dbo.Users(UserName, Email)
VALUES
('User_A', 'usera@test.com'),
('User_B', 'userb@test.com');
GO
```

Kiểm tra dữ liệu:

```sql
SELECT *
FROM dbo.Users;
```

---

## 19.2 Update dữ liệu

```sql
UPDATE dbo.Users
SET Email = 'updated_usera@test.com'
WHERE UserName = 'User_A';
GO
```

---

## 19.3 Delete dữ liệu

```sql
DELETE
FROM dbo.Users
WHERE UserName = 'User_B';
GO
```

---

## 19.4 Kiểm tra CDC Change Table

```sql
SELECT
    __$start_lsn,
    __$operation,
    UserId,
    UserName,
    Email
FROM cdc.dbo_Users_CT
ORDER BY __$start_lsn DESC;
```

Ý nghĩa __$operation:

| Value | Action          |
| ----- | --------------- |
| 1     | DELETE          |
| 2     | INSERT          |
| 3     | UPDATE (Before) |
| 4     | UPDATE (After)  |

---

## 19.5 Test liên tục (Streaming Test)

Sinh dữ liệu mỗi giây:

```sql
DECLARE @i INT = 1;

WHILE @i <= 100
BEGIN

    INSERT INTO dbo.Users
    (
        UserName,
        Email
    )
    VALUES
    (
        CONCAT('User_', @i),
        CONCAT('user', @i, '@test.com')
    );

    WAITFOR DELAY '00:00:01';

    SET @i = @i + 1;
END
GO
```

---

## 19.6 Test Update liên tục

```sql
DECLARE @i INT = 1;

WHILE @i <= 50
BEGIN

    UPDATE dbo.Users
    SET Email = CONCAT('updated_', @i, '@test.com')
    WHERE UserId = @i;

    WAITFOR DELAY '00:00:01';

    SET @i = @i + 1;
END
GO
```

---

## 19.7 Test hỗn hợp Insert + Update + Delete

```sql
INSERT INTO dbo.Users(UserName, Email)
VALUES ('CDC_TEST', 'cdc@test.com');

DECLARE @id INT;

SET @id = SCOPE_IDENTITY();

UPDATE dbo.Users
SET Email = 'cdc_updated@test.com'
WHERE UserId = @id;

DELETE dbo.Users
WHERE UserId = @id;
```

---

## 19.8 Kiểm tra Debezium đã đọc tới LSN nào

```sql
SELECT TOP 20
    __$start_lsn,
    __$seqval,
    __$operation,
    UserId,
    UserName
FROM cdc.dbo_Users_CT
ORDER BY __$start_lsn DESC;
```

---

## 19.9 Test tải lớn (Performance Test)

```sql
SET NOCOUNT ON;

DECLARE @i INT = 1;

WHILE @i <= 10000
BEGIN

    INSERT INTO dbo.Users
    (
        UserName,
        Email
    )
    VALUES
    (
        CONCAT('LoadTest_', @i),
        CONCAT('load', @i, '@test.com')
    );

    SET @i = @i + 1;
END
GO
```

Mục đích:

* Kiểm tra CDC Capture Job.
* Kiểm tra Debezium throughput.
* Kiểm tra Kafka topic growth.
* Kiểm tra khả năng ingest của Spark/Flink downstream.

---

## 19.10 Theo dõi CDC Lag

Số bản ghi CDC đã capture:

```sql
SELECT COUNT(*)
FROM cdc.dbo_Users_CT;
```

Số bản ghi nguồn:

```sql
SELECT COUNT(*)
FROM dbo.Users;
```

Nếu CDC hoạt động bình thường:

```text
INSERT/UPDATE/DELETE
    ↓
cdc.dbo_Users_CT
    ↓ (1-5 giây)
Debezium
    ↓
Kafka Topic
```

