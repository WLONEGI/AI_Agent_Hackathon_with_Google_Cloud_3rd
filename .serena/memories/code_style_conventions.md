# Code Style and Conventions

## Python (Backend)
### Naming Conventions
- **Functions/Variables**: snake_case (e.g., `generate_manga`, `user_input`)
- **Classes**: PascalCase (e.g., `MangaGenerator`, `UserModel`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_PAGES`, `API_VERSION`)
- **Private methods**: Leading underscore (e.g., `_process_internal`)

### Code Style
- **Indentation**: 4 spaces
- **Line length**: 88 characters (Black default)
- **Quotes**: Double quotes for strings
- **Type hints**: Used extensively with Pydantic models
- **Docstrings**: Present but minimal, focus on code clarity
- **Async**: Heavy use of async/await patterns

### Patterns
- Dependency injection via FastAPI
- Pydantic for data validation
- SQLAlchemy for ORM with async support
- Structured logging with structlog

## TypeScript/JavaScript (Frontend)
### Naming Conventions  
- **Components**: PascalCase (e.g., `MangaViewer.tsx`)
- **Functions/Variables**: camelCase (e.g., `handleSubmit`, `userData`)
- **Interfaces/Types**: PascalCase with 'I' or 'T' prefix avoided
- **Files**: camelCase for utilities, PascalCase for components

### Code Style
- **Indentation**: 2 spaces
- **Semicolons**: Avoided (Prettier config)
- **Quotes**: Single quotes for imports, double for JSX
- **Arrow functions**: Preferred over function declarations
- **Exports**: Named exports preferred, default for pages

### Patterns
- Functional components with hooks
- Custom hooks for reusable logic
- Zustand for state management
- Server-side rendering with Next.js
- Tailwind for styling with utility classes

## Git Conventions
- **Branch naming**: `feature/`, `bugfix/`, `hotfix/` prefixes
- **Commit messages**: Conventional Commits format
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation
  - `style:` Formatting
  - `refactor:` Code restructuring
  - `test:` Testing
  - `chore:` Maintenance

## File Organization
- One component per file
- Related files grouped in feature folders
- Shared utilities in lib/utils directories
- Tests adjacent to source in tests/ directories

## Error Handling
- Explicit error types in Python
- Try-catch with proper error boundaries in React
- Structured error responses in API
- Comprehensive logging for debugging

## Comments
- Minimal comments - code should be self-documenting
- Comments explain "why" not "what"
- TODO comments tracked and addressed
- No commented-out code in production