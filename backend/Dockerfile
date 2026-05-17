# 這份 Dockerfile 用來把後端 Python API 打包成可部署的容器。
# 設計重點：
# - 先安裝相依套件，再複製程式碼，讓 Docker layer cache 更有效率
# - 只保留後端執行所需的最小環境
# - 容器啟動後直接執行 FastAPI 應用
FROM python:3.10-slim

WORKDIR /app

# 先複製 requirements，讓依賴安裝能被快取
COPY requirements_backend.txt .

# 安裝後端依賴，避免把 pip cache 留在映像中
RUN pip install --no-cache-dir -r requirements_backend.txt

# 複製後端原始碼與模板檔
COPY backend ./backend
COPY template ./template

# 設定 Python 模組搜尋路徑與服務埠號
ENV PYTHONPATH=/app
ENV PORT=8000

# 對外開放 API port
EXPOSE 8000

# 容器啟動時直接執行後端 API
CMD ["python", "-m", "backend.api"]
