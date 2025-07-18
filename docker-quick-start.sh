#!/bin/bash
# quick-start.sh - マルチエージェント開発システムのDockerセットアップスクリプト

set -e

echo "🚀 Multi-Agent Development System - Docker Setup"
echo "=============================================="

# プロジェクトディレクトリの作成
echo "📁 Creating project structure..."
mkdir -p multi-agent-dev-system/{backend,frontend,docker/{backend,frontend,nginx,postgres}}
cd multi-agent-dev-system

# .gitignore の作成
cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.env
.venv

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Docker
*.log
docker-compose.override.yml

# Testing
.coverage
htmlcov/
.pytest_cache/
coverage.xml
*.cover

# Production
build/
dist/
*.egg-info/
EOL

# .dockerignore の作成
cat > .dockerignore << 'EOL'
**/__pycache__
**/*.pyc
**/*.pyo
**/*.pyd
.Python
env/
venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
coverage.xml
*.cover
*.log
.git
.gitignore
.mypy_cache
.pytest_cache
.hypothesis
.env
.venv

# Frontend
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*

# IDEs
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOL

# Backend初期構造の作成
echo "🐍 Setting up backend structure..."
mkdir -p backend/app/{agents,core,api,tools,utils}

# backend/app/__init__.py
touch backend/app/__init__.py

# backend/app/main.py
cat > backend/app/main.py << 'EOL'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
import os

app = FastAPI(title="Multi-Agent Development System")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Multi-Agent Development System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()
    await websocket.send_json({"type": "connection", "message": "Connected to project " + project_id})
    # TODO: Implement WebSocket handling
EOL

# Frontend初期構造の作成
echo "⚛️  Setting up frontend structure..."
mkdir -p frontend/{src,public}

# frontend/package.json
cat > frontend/package.json << 'EOL'
{
  "name": "multi-agent-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0",
    "@mui/material": "^5.14.20",
    "@reduxjs/toolkit": "^2.0.1",
    "axios": "^1.6.2",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-redux": "^9.0.4",
    "react-router-dom": "^6.20.1",
    "socket.io-client": "^4.7.2",
    "typescript": "^5.3.3"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "devDependencies": {
    "@types/node": "^20.10.5",
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "react-scripts": "5.0.1"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
  }
}
EOL

# frontend/src/App.tsx
cat > frontend/src/App.tsx << 'EOL'
import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, Typography, Box } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'dark',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            Multi-Agent Development System
          </Typography>
          <Typography variant="h6" component="h2" gutterBottom>
            AI-Powered Software Development Pipeline
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
EOL

# frontend/src/index.tsx
cat > frontend/src/index.tsx << 'EOL'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOL

# frontend/public/index.html
cat > frontend/public/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Multi-Agent Development System" />
    <title>Multi-Agent Dev System</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOL

# Nginx設定
echo "🔧 Setting up Nginx configuration..."
cat > docker/nginx/nginx.conf << 'EOL'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOL

# PostgreSQL初期化スクリプト
cat > docker/postgres/init.sql << 'EOL'
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    requirements TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_works (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phase_id UUID NOT NULL REFERENCES phases(id) ON DELETE CASCADE,
    agent_id VARCHAR(100) NOT NULL,
    agent_role VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work_id UUID NOT NULL REFERENCES agent_works(id) ON DELETE CASCADE,
    reviewer_id VARCHAR(100) NOT NULL,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    feedback TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_phases_project_id ON phases(project_id);
CREATE INDEX idx_phases_type ON phases(phase_type);
CREATE INDEX idx_agent_works_phase_id ON agent_works(phase_id);
CREATE INDEX idx_reviews_work_id ON reviews(work_id);
EOL

# 環境変数ファイルのサンプル
echo "🔐 Creating environment configuration..."
cat > .env.example << 'EOL'
# Application
APP_NAME=MultiAgentDevSystem
APP_ENV=development
DEBUG=True

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=multiagent
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# LLM APIs
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost

# WebSocket
WS_MESSAGE_QUEUE_SIZE=1000
WS_HEARTBEAT_INTERVAL=30

# Monitoring
LOG_LEVEL=INFO
EOL

# 実際の.envファイルをコピー
cp .env.example .env

# Docker Compose ファイルは既に作成済みなので、ここでは作成しない
# （前のアーティファクトから手動でコピーする必要があります）

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy the docker-compose.yml from the previous artifact"
echo "2. Copy the Dockerfiles from the previous artifact"
echo "3. Copy the Makefile from the previous artifact"
echo "4. Edit .env file with your API keys"
echo "5. Run: make dev-build"
echo "6. Run: make dev"
echo ""
echo "Your application will be available at:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"