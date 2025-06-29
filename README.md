# Quick Reply Flask 應用程式

這是一個使用 Flask 和 PostgreSQL 的快速回覆應用程式，用於管理兒童體重和身高數據。

## 環境設置

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 環境變數設置

#### 本地開發環境

1. 在專案根目錄創建 `.env` 文件
2. 複製 `.env.example` 的內容到 `.env`
3. 修改 `.env` 文件中的環境變數值：

```env
DATABASE_URL=postgresql://username:password@host:port/database
```

#### 生產環境（Heroku）

在 Heroku 中設置環境變數：
```bash
heroku config:set DATABASE_URL=your_database_url
```

### 3. 運行應用程式

```bash
python app_core.py
```

## 文件說明

- `app_core.py` - 主要的 Flask 應用程式
- `.env` - 本地環境變數（不會提交到 Git）
- `.env.example` - 環境變數範例文件
- `requirements.txt` - Python 依賴套件
- `config.ini` - 應用程式配置
- `templates/` - HTML 模板文件

## 注意事項

- `.env` 文件包含敏感信息，已被 `.gitignore` 忽略
- 在部署到生產環境時，確保設置正確的環境變數
- 本地開發時確保 PostgreSQL 資料庫運行中
