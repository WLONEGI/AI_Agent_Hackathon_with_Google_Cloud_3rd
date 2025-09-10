# Task Completion Checklist

## When Completing Any Task

### 1. Code Quality Checks
**Backend (Python)**
```bash
# Run tests
pytest
pytest --cov  # Check coverage

# Type checking (if mypy configured)
# mypy app/

# Check for import errors
python -c "import app.main"
```

**Frontend (TypeScript)**
```bash
# Type checking - MUST PASS
npm run type-check

# Linting - MUST PASS  
npm run lint

# Run tests
npm run test

# Build check
npm run build
```

### 2. Before Marking Task Complete
- ✅ All tests passing
- ✅ No TypeScript errors (`npm run type-check`)
- ✅ No linting errors (`npm run lint`)
- ✅ Code follows existing patterns
- ✅ No console.log or print debug statements
- ✅ No TODO comments for implemented features
- ✅ API endpoints tested if modified
- ✅ UI components render correctly if changed

### 3. Git Hygiene
```bash
# Always check before committing
git status
git diff

# Stage intentionally
git add -p  # Review each change

# Never commit to main
git branch  # Verify on feature branch
```

### 4. Documentation Updates
- Update README if adding new features
- Update API documentation if endpoints changed
- Add JSDoc/docstrings for public functions
- Update environment variables if added

### 5. Security Checks
- No hardcoded credentials
- No exposed API keys
- Environment variables used for secrets
- Sensitive data not logged

### 6. Performance Considerations
- No N+1 queries in database operations
- Appropriate indexes on database queries
- React components memoized where needed
- Large lists virtualized
- Images optimized and lazy loaded

## Red Flags - Never Ignore
- ❌ Failing tests
- ❌ TypeScript errors
- ❌ Commented out tests
- ❌ Skipped validation
- ❌ Hardcoded secrets
- ❌ Unhandled promise rejections
- ❌ Memory leaks in subscriptions

## Quick Validation Commands
```bash
# Backend validation
cd backend && pytest && echo "✅ Backend OK"

# Frontend validation  
cd frontend && npm run type-check && npm run lint && npm run test && echo "✅ Frontend OK"

# Full check
npm run test:ci  # If configured
```

## Important Notes
- If you cannot find the lint/type-check command, ASK the user
- Never skip validation to "make things work"
- Always fix root causes, not symptoms
- Clean up temporary files and debug code