#!/bin/bash
"""
Quick Security Fix Script - Phase 1 Critical Issues Only
For immediate security vulnerability resolution (24-hour window)
"""

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️ $1${NC}"
}

log_info() {
    log "${BLUE}ℹ️ $1${NC}"
}

# Pre-flight checks
preflight_check() {
    log_info "Running pre-flight security checks..."
    
    # Check if we're in the right directory
    if [ ! -f "app/main.py" ]; then
        log_error "Not in backend directory or app/main.py not found"
        exit 1
    fi
    
    # Check git status
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "Uncommitted changes detected - consider committing first"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [ "$(echo "$PYTHON_VERSION >= 3.9" | bc -l)" -eq 1 ]; then
        log_success "Python version OK ($PYTHON_VERSION)"
    else
        log_error "Python 3.9+ required (found $PYTHON_VERSION)"
        exit 1
    fi
    
    log_success "Pre-flight checks passed"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    BACKUP_DIR="/tmp/backend_security_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup critical files
    cp .env "$BACKUP_DIR/.env.backup"
    cp app/services/cache_service.py "$BACKUP_DIR/cache_service.py.backup"
    
    # Create git backup branch
    git add -A
    git commit -m "Pre-security-fix backup - $(date)" || true
    git branch "security-fix-backup-$(date +%Y%m%d)" || true
    
    echo "$BACKUP_DIR" > .cleanup_backup_location
    log_success "Backup created at: $BACKUP_DIR"
}

# Fix SEC-001: Hardcoded Secret Key
fix_secret_key() {
    log_info "🔐 SEC-001: Fixing hardcoded secret key..."
    
    # Generate new secure key
    NEW_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    if [ ${#NEW_KEY} -lt 32 ]; then
        log_error "Generated key too short"
        return 1
    fi
    
    # Update .env file
    cp .env .env.backup
    sed -i.tmp "s/SECRET_KEY=dev-secret-key-change-in-production-minimum-32-chars-long/SECRET_KEY=$NEW_KEY/" .env
    
    # Verify change
    if grep -q "$NEW_KEY" .env; then
        log_success "Secret key updated successfully"
        rm .env.tmp
    else
        log_error "Secret key update failed"
        cp .env.backup .env
        return 1
    fi
    
    # Update any hardcoded references in code
    if grep -r "dev-secret-key" app/ >/dev/null 2>&1; then
        log_warning "Hardcoded secret references found in code - manual update needed"
        grep -r "dev-secret-key" app/ | head -3
    fi
}

# Fix SEC-002: Pickle Vulnerability  
fix_pickle_vulnerability() {
    log_info "🐍 SEC-002: Fixing pickle deserialization vulnerability..."
    
    # Create safe serialization module
    cat > app/core/safe_serialization.py << 'EOF'
"""Safe serialization module replacing pickle."""
import json
import structlog
from typing import Any, Optional

logger = structlog.get_logger(__name__)

def safe_serialize(data: Any) -> str:
    """Safe serialization without pickle vulnerabilities."""
    try:
        return json.dumps(data, default=str, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error("Serialization failed", error=str(e))
        raise ValueError(f"Cannot serialize data: {e}")

def safe_deserialize(data: str) -> Optional[Any]:
    """Safe deserialization with validation."""
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error("Deserialization failed", error=str(e))
        return None

def migrate_pickle_data(pickle_data: bytes) -> str:
    """Migrate existing pickle data to JSON format."""
    try:
        import pickle
        data = pickle.loads(pickle_data)
        return safe_serialize(data)
    except Exception as e:
        logger.error("Pickle migration failed", error=str(e))
        return "{}"
EOF
    
    # Backup cache service
    cp app/services/cache_service.py app/services/cache_service.py.backup
    
    # Replace pickle usage
    sed -i.tmp 's/import pickle//g' app/services/cache_service.py
    sed -i 's/pickle\.loads(redis_data\.encode.*)/safe_deserialize(redis_data)/g' app/services/cache_service.py
    sed -i 's/pickle\.dumps/safe_serialize/g' app/services/cache_service.py
    
    # Add import for safe serialization
    if ! grep -q "safe_serialization" app/services/cache_service.py; then
        sed -i '1i from app.core.safe_serialization import safe_serialize, safe_deserialize' app/services/cache_service.py
    fi
    
    # Verify no pickle usage remains
    if grep -q "pickle\." app/services/cache_service.py; then
        log_error "Pickle usage still found in cache service"
        cp app/services/cache_service.py.backup app/services/cache_service.py
        return 1
    else
        log_success "Pickle vulnerability fixed"
        rm app/services/cache_service.py.tmp
    fi
}

# Fix SEC-003: Input Sanitization
fix_input_sanitization() {
    log_info "🧼 SEC-003: Adding input sanitization..."
    
    # Add bleach dependency if not present
    if ! grep -q "bleach" requirements.txt; then
        echo "bleach==6.1.0" >> requirements.txt
        log_success "Added bleach dependency to requirements.txt"
    fi
    
    # Create input sanitization module
    cat > app/core/input_sanitization.py << 'EOF'
"""Input sanitization and validation."""
import html
import re
from typing import Any, Dict

def sanitize_text(content: str) -> str:
    """Sanitize plain text content."""
    if not content:
        return ""
    # Basic HTML escape
    content = html.escape(content.strip())
    # Remove potential script patterns
    content = re.sub(r'<script.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    return content

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    import os
    return os.path.basename(filename)

def validate_natural_language_input(content: str) -> str:
    """Validate and sanitize natural language input."""
    if not content or len(content.strip()) == 0:
        raise ValueError("Content cannot be empty")
    
    if len(content) > 10000:
        raise ValueError("Content too long (max 10000 characters)")
    
    return sanitize_text(content)
EOF
    
    log_success "Input sanitization module created"
}

# Verification and validation
run_security_validation() {
    log_info "🔍 Running security validation..."
    
    # Check secret key
    SECRET_LENGTH=$(grep SECRET_KEY .env | cut -d= -f2 | wc -c)
    if [ "$SECRET_LENGTH" -gt 40 ]; then
        log_success "Secret key length OK ($SECRET_LENGTH chars)"
    else
        log_error "Secret key too short ($SECRET_LENGTH chars)"
        return 1
    fi
    
    # Check pickle removal
    if grep -r "pickle\." app/ >/dev/null 2>&1; then
        log_error "Pickle usage still found:"
        grep -r "pickle\." app/ | head -3
        return 1
    else
        log_success "Pickle vulnerability eliminated"
    fi
    
    # Check app functionality
    if python3 -c "import sys; sys.path.append('.'); from app.main import app" 2>/dev/null; then
        log_success "Application loads successfully"
    else
        log_error "Application loading failed after fixes"
        return 1
    fi
    
    # Security scan if bandit available
    if command -v bandit >/dev/null 2>&1; then
        log_info "Running security scan..."
        bandit -r app/ -f json > security_scan_results.json 2>/dev/null || true
        ISSUES=$(cat security_scan_results.json | jq '.results | length' 2>/dev/null || echo "0")
        log_info "Security scan found $ISSUES potential issues (see security_scan_results.json)"
    fi
    
    log_success "Security validation completed"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "🛡️  Quick Security Fix Script"
    echo "================================"
    echo "Fixing critical security vulnerabilities in backend"
    echo -e "${NC}"
    
    # Confirmation
    log_warning "This script will modify your codebase to fix critical security issues"
    log_info "Backup will be created automatically"
    
    read -p "Proceed with security fixes? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Security fix cancelled by user"
        exit 0
    fi
    
    # Execute fixes
    preflight_check
    create_backup
    
    log_info "🚀 Starting security fixes..."
    
    if fix_secret_key && fix_pickle_vulnerability && fix_input_sanitization; then
        log_success "All security fixes applied"
        
        if run_security_validation; then
            log_success "🎉 Security fixes completed successfully!"
            log_info "Backup location: $(cat .cleanup_backup_location)"
            log_info "Git backup branch: security-fix-backup-$(date +%Y%m%d)"
            
            echo -e "\n${GREEN}Next Steps:${NC}"
            echo "1. Test your application thoroughly"
            echo "2. Run full test suite: pytest app/tests/"
            echo "3. Deploy to staging for validation"
            echo "4. Consider running full cleanup plan: python scripts/execute_cleanup_plan.py"
            
            return 0
        else
            log_error "Security validation failed"
            return 1
        fi
    else
        log_error "Security fixes failed"
        log_info "To rollback: cp \$(cat .cleanup_backup_location)/.env.backup .env"
        return 1
    fi
}

# Script execution
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi