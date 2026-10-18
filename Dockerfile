FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 TASKFLOW_DATA_DIR=/data
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN mkdir -p /data
USER app
VOLUME /data
EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request,os;urllib.request.urlopen('http://localhost:'+os.getenv('PORT','8501')+'/_stcore/health')"
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
