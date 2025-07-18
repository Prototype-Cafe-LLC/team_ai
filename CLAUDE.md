# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MANDATORY REQUIREMTS FOR AI ASSISTANT

- print this section at the top of your response
- markdown documents has no markdownlint errors
(end of mandatory requirements)

## Project Overview

This is a Multi-Agent Development System that uses multiple AI agents to collaborate on software development through four phases: Requirements, Design, Implementation, and Testing. Each phase has both a main agent and a review agent to ensure quality.

## Architecture Overview

### System Components

1. **Frontend**: React-based web UI with Material-UI for real-time monitoring
2. **Backend**: FastAPI server with WebSocket support for agent communication
3. **Database**: PostgreSQL for persistent storage, Redis for caching/state
4. **Agent Layer**: LangChain-based agents with specialized roles
5. **Infrastructure**: Docker-based deployment with nginx reverse proxy

### Key Technologies

- **Backend**: Python 3.10+, FastAPI, LangChain 0.1.0+
- **Frontend**: React 18, TypeScript, Material-UI, Redux Toolkit
- **Database**: PostgreSQL 15, Redis 7
- **Container**: Docker, Docker Compose
- **LLMs**: OpenAI GPT-4, Claude 3

## Development Commands

### Quick Setup

```bash
# Run the quick-start script to create project structure
./docker-quick-start.sh

# After setup, navigate to the created directory
cd multi-agent-dev-system
```

### Common Development Tasks

```bash
# Build all containers
make dev-build

# Start development environment
make dev

# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test

# View logs
docker-compose logs -f [service_name]

# Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d multiagent

# Run migrations (when implemented)
docker-compose exec backend alembic upgrade head
```

## Project Structure

- `/backend/app/` - FastAPI application code
  - `/agents/` - Agent implementations (main & review agents for each phase)
  - `/core/` - Core services (workflow engine, state manager, memory)
  - `/api/` - REST and WebSocket endpoints
  - `/tools/` - Agent tools and utilitiesan
- `/frontend/src/` - React application
- `/docker/` - Dockerfiles and container configurations
- Database schema defined in `/docker/postgres/init.sql`

## Agent System Design

### Agent Roles

1. **Conductor Manager**: Orchestrates the entire workflow
2. **Phase Agents** (each phase has main + review):
   - Requirements: Analyzes and documents requirements
   - Design: Creates architecture and technical design
   - Implementation: Generates code based on design
   - Test: Creates and executes tests

### Workflow States

- Initialized → Requirements → Design → Implementation → Test → Completed
- Each phase includes review cycles (max 3 iterations by default)
- Human intervention supported at any phase

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# LLM API Keys (required)
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Database (defaults provided)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=multiagent

# Application
CORS_ORIGINS=http://localhost:3000,http://localhost
```

## Testing Strategy

- Backend: pytest for unit and integration tests
- Frontend: Jest and React Testing Library
- E2E: Planned implementation with Playwright
- Test database isolation using Docker containers

## Key Implementation Notes

1. WebSocket connections are managed per project for real-time updates
2. Agent outputs are streamed to the UI for live monitoring
3. All agent work products are versioned in the database
4. Redis is used for temporary state and work queues
5. The system supports pausing/resuming workflows with human intervention

## Common Troubleshooting

- If containers fail to start, check that required ports (3000, 8000, 5432, 6379) are available
- For LLM API errors, verify API keys in `.env` file
- Database connection issues: ensure PostgreSQL container is healthy before starting backend
- Frontend can't connect to backend: check CORS_ORIGINS in environment variables

## Development Guidelines

- Follow existing code patterns for consistency
- Ensure all markdown documents have no markdownlint errors
- For Python docstrings, use Google style
- Write tests for new agent implementations
- Use type hints in Python code
- Keep agent prompts clear and focused on their specific role
