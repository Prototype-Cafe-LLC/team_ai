# Docker コンテナ実装構成

## 1. プロジェクト構造（Docker対応版）

```
multi-agent-dev-system/
├── docker/
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   └── Dockerfile
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── core/
│   │   ├── api/
│   │   └── __init__.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .dockerignore
├── .env.example
└── Makefile
```

## 2. Docker Compose 設定

### メイン docker-compose.yml

```yaml
version: '3.9'

x-backend-common: &backend-common
  build:
    context: ./backend
    dockerfile: ../docker/backend/Dockerfile
  environment:
    - PYTHONUNBUFFERED=1
    - REDIS_URL=redis://redis:6379
    - POSTGRES_URL=postgresql://postgres:postgres@postgres:5432/multiagent
  volumes:
    - ./backend:/app
  depends_on:
    - postgres
    - redis

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: multiagent
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching and state management
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    <<: *backend-common
    container_name: multiagent-backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file:
      - .env

  # Frontend React App
  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/frontend/Dockerfile
      target: development
    container_name: multiagent-frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_WS_URL=ws://localhost:8000
    depends_on:
      - backend

  # Nginx Reverse Proxy (for production)