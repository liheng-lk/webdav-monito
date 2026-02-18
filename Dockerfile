FROM docker.m.daocloud.io/library/node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM docker.m.daocloud.io/library/python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /frontend/dist ./frontend/dist

RUN mkdir -p data
EXPOSE 8000
ENV PYTHONPATH=/app

CMD ["python", "-u", "backend/main.py"]
