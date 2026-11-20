FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py provider.py renderer.py index.html catalog.json ./
RUN mkdir -p /app/output
ENV RENDER_ENGINE=demo SOCIAL_FACTORY_OUTPUT=/app/output HOST=0.0.0.0 PORT=8765
EXPOSE 8765
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8765"]
