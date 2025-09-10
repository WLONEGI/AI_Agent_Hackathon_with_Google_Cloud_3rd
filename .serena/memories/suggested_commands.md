# Development Commands

## Project Setup
```bash
# Initial setup (recommended)
chmod +x scripts/setup.sh
./scripts/setup.sh

# Google Cloud authentication
gcloud auth application-default login
gcloud config set project comic-ai-agent
```

## Backend Development
```bash
# Navigate to backend
cd backend

# Activate Python virtual environment
python3 -m venv comic-ai-env
source comic-ai-env/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run development server (port 8000)
uvicorn main:app --reload

# Run backend tests
pytest
pytest --cov  # with coverage

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Frontend Development
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Development server (port 3000)
npm run dev
npm run dev:turbo  # with Turbopack

# Build production
npm run build

# Type checking and linting
npm run type-check
npm run lint

# Testing
npm run test              # All tests
npm run test:unit        # Unit tests only
npm run test:integration # Integration tests
npm run test:e2e         # End-to-end tests with Playwright
npm run test:coverage    # With coverage report
```

## Docker Operations
```bash
# Navigate to infrastructure
cd infrastructure

# Start all services
docker-compose up

# Start specific service
docker-compose up redis

# Build and start
docker-compose up --build
```

## API Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Redis: localhost:6379

## Git Workflow
```bash
# Create feature branch
git checkout -b feature/feature-name
git checkout -b bugfix/bug-description

# Check status before committing
git status
git diff

# Commit with conventional commits
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update README"
```

## Utility Commands (macOS)
```bash
# File operations
ls -la           # List all files with details
find . -name "*.py"  # Find Python files
grep -r "pattern" .  # Search for pattern

# Process management
ps aux | grep python  # Find Python processes
kill -9 PID          # Force kill process
lsof -i :8000        # Check what's using port 8000
```