FROM python:3.10-slim

WORKDIR /app

# 安裝基本的 curl 供健康檢查使用
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 相依套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製其餘程式碼
COPY . .

# Hugging Face Spaces 使用 7860
EXPOSE 7860

# 啟動 Streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]