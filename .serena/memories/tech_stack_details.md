# Technology Stack

## Backend
- **Language**: Python 3.12.11+
- **Framework**: FastAPI 0.109.0
- **ASGI Server**: Uvicorn 0.27.0 with standard extras
- **Validation**: Pydantic 2.5.3
- **Database ORM**: SQLAlchemy 2.0.25
- **Migrations**: Alembic 1.13.1
- **Async DB**: asyncpg 0.29.0, psycopg[binary] 3.1.18

## Frontend
- **Framework**: Next.js 15.5.2 with React 18.3.1
- **Language**: TypeScript 5.x
- **Styling**: TailwindCSS 3.4.17
- **UI Components**: Radix UI, Lucide React icons
- **State Management**: Zustand 5.0.8
- **Build Tool**: Next.js with Turbopack support

## Google Cloud & AI
- **AI Platform**: Google Vertex AI 1.40.0+
  - Gemini Pro for text processing
  - Imagen 4 for image generation
- **Storage**: Google Cloud Storage 2.14.0+
- **Authentication**: Firebase Admin 6.4.0, Firebase Auth
- **Secrets**: Google Cloud Secret Manager 2.18.0+

## Infrastructure
- **Container**: Docker 28.1.1+
- **Orchestration**: Cloud Run (8 vCPU, 32GB RAM)
- **IaC**: Terraform
- **Database**: Cloud SQL (PostgreSQL)
- **Cache**: Redis 5.0.1 with aioredis
- **CI/CD**: GitHub Actions + Cloud Build

## Development Tools
- **Testing Backend**: pytest 7.4.4, pytest-asyncio, pytest-cov
- **Testing Frontend**: Jest 30.1.1, Playwright 1.55.0, Testing Library
- **Linting**: ESLint 9 (frontend)
- **Formatting**: Prettier 3.6.2 (frontend)
- **Type Checking**: TypeScript compiler

## Monitoring & Performance
- **Logging**: structlog 24.1.0
- **Metrics**: prometheus-fastapi-instrumentator 6.1.0
- **WebSocket**: python-socketio 5.11.0, websockets 12.0
- **Async Tools**: aiofiles, aiocache, httpx