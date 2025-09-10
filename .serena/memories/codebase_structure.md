# Codebase Structure

## Root Directory
```
AI_Agent_Hackathon_with_Google_Cloud_3rd/
├── backend/              # Python FastAPI backend
├── frontend/             # React Next.js frontend  
├── infrastructure/       # Terraform and Docker configs
├── docs/                 # Documentation
├── .github/              # GitHub Actions workflows
├── .serena/              # Serena MCP cache and memories
├── .claude/              # Claude configuration
└── README.md            # Main project documentation
```

## Backend Structure
```
backend/
├── app/                  # Main application code
│   ├── agents/          # 8-stage AI processing modules
│   ├── api/             # API endpoints
│   ├── core/            # Core utilities and config
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── websocket/       # WebSocket handlers
│   ├── domain/          # Domain logic
│   ├── infrastructure/ # Infrastructure layer
│   ├── application/     # Application layer
│   └── main.py          # FastAPI app entry point
├── alembic/             # Database migrations
├── scripts/             # Python utility scripts
├── tests/               # Test files
├── deployment/          # Deployment configs
├── Dockerfile           # Container definition
└── requirements.txt     # Python dependencies
```

## Frontend Structure  
```
frontend/
├── src/                 # Source code
│   ├── app/            # Next.js app directory
│   ├── components/     # React components
│   ├── lib/            # Utilities and helpers
│   ├── types/          # TypeScript type definitions
│   └── styles/         # CSS/styling files
├── public/             # Static assets
├── tests/              # Test files
├── mock/               # Mock data for testing
├── claudedocs/         # Claude-specific documentation
├── package.json        # Node dependencies
├── tsconfig.json       # TypeScript config
├── next.config.ts      # Next.js configuration
└── tailwind.config.ts  # TailwindCSS config
```

## Key Directories
- **agents/**: Contains the 8-stage AI pipeline modules for manga generation
- **api/**: RESTful API endpoints and route handlers
- **websocket/**: Real-time communication for progress updates
- **infrastructure/**: Terraform IaC and Docker configurations
- **tests/**: Comprehensive test suites (unit, integration, E2E)

## File Naming Conventions
- Python: snake_case (e.g., `manga_generator.py`)
- TypeScript/JavaScript: camelCase for files, PascalCase for components
- Tests: `test_*.py` for Python, `*.test.ts` for TypeScript
- Config files: lowercase with extensions (e.g., `jest.config.js`)

## Import Patterns
- Python: Absolute imports from app root
- TypeScript: Alias imports using `@/` for src directory
- External libraries imported before internal modules