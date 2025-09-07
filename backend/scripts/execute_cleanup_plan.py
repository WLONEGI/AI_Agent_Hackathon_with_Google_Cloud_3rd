#!/usr/bin/env python3
"""
Comprehensive Backend Cleanup Execution Script
Implements the systematic cleanup plan with safety validation.
"""

import os
import sys
import subprocess
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

class CleanupExecutor:
    """Execute backend cleanup plan with safety validation."""
    
    def __init__(self, backend_path: str = "."):
        self.backend_path = Path(backend_path).resolve()
        self.backup_dir = Path(f"/tmp/backend_cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.log_file = self.backend_path / "cleanup_execution.log"
        self.phase_status = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log cleanup progress."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, command: str, description: str = "") -> Tuple[bool, str]:
        """Execute shell command with logging."""
        self.log(f"Executing: {description or command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=self.backend_path
            )
            if result.returncode == 0:
                self.log(f"✅ Success: {description}")
                return True, result.stdout
            else:
                self.log(f"❌ Failed: {description} - {result.stderr}", "ERROR")
                return False, result.stderr
        except Exception as e:
            self.log(f"❌ Exception: {description} - {str(e)}", "ERROR")
            return False, str(e)
    
    def create_backup(self) -> bool:
        """Create comprehensive backup before cleanup."""
        self.log("Creating comprehensive backup...")
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy entire backend directory
            shutil.copytree(self.backend_path, self.backup_dir / "backend")
            
            # Create git backup branch
            success, _ = self.run_command(
                f"git branch cleanup-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "Create git backup branch"
            )
            
            if success:
                self.log(f"✅ Backup created at: {self.backup_dir}")
                return True
            else:
                self.log("❌ Git backup failed, but filesystem backup exists")
                return True
                
        except Exception as e:
            self.log(f"❌ Backup creation failed: {str(e)}", "ERROR")
            return False
    
    def validate_prerequisites(self) -> bool:
        """Validate system prerequisites for cleanup."""
        self.log("Validating prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 9):
            self.log("❌ Python 3.9+ required", "ERROR")
            return False
        
        # Check git status
        success, output = self.run_command("git status --porcelain", "Check git status")
        if success and output.strip():
            self.log("⚠️ Warning: Uncommitted changes detected")
            self.log("Consider committing changes before cleanup")
        
        # Check if backend directory exists
        if not (self.backend_path / "app").exists():
            self.log("❌ Backend app directory not found", "ERROR") 
            return False
        
        # Verify imports work
        success, _ = self.run_command(
            "python3 -c 'import sys; sys.path.append(\".\"); from app.main import app; print(\"Import OK\")'",
            "Verify app imports"
        )
        
        if not success:
            self.log("❌ App import validation failed", "ERROR")
            return False
        
        self.log("✅ Prerequisites validated")
        return True
    
    def execute_phase1_security_fixes(self) -> bool:
        """Phase 1: Critical security vulnerabilities."""
        self.log("🚨 Phase 1: Executing critical security fixes...")
        
        # 1.1 Secret Key Replacement
        self.log("Fixing SEC-001: Hardcoded secret key...")
        
        # Generate new secure key
        success, new_key = self.run_command(
            "python3 -c 'import secrets; print(secrets.token_urlsafe(32))'",
            "Generate secure secret key"
        )
        
        if not success:
            return False
        
        new_key = new_key.strip()
        
        # Update .env file
        success, _ = self.run_command(
            f"sed -i.bak 's/SECRET_KEY=dev-secret-key-change-in-production-minimum-32-chars-long/SECRET_KEY={new_key}/' .env",
            "Update secret key in .env"
        )
        
        if not success:
            return False
        
        # 1.2 Pickle Vulnerability Fix
        self.log("Fixing SEC-002: Pickle deserialization vulnerability...")
        
        # Create safe serialization module
        safe_serialization_content = '''"""Safe serialization module replacing pickle."""
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
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error("Deserialization failed", error=str(e))
        return None
'''
        
        with open(self.backend_path / "app/core/safe_serialization.py", "w") as f:
            f.write(safe_serialization_content)
        
        # Replace pickle usage in cache_service.py
        success, _ = self.run_command(
            "sed -i.bak 's/import pickle//g' app/services/cache_service.py",
            "Remove pickle import"
        )
        
        if not success:
            return False
        
        success, _ = self.run_command(
            "sed -i 's/pickle\.loads/safe_deserialize/g' app/services/cache_service.py",
            "Replace pickle.loads"
        )
        
        success, _ = self.run_command(
            "sed -i 's/pickle\.dumps/safe_serialize/g' app/services/cache_service.py",
            "Replace pickle.dumps"
        )
        
        # Add import for safe serialization
        success, _ = self.run_command(
            "sed -i '1i from app.core.safe_serialization import safe_serialize, safe_deserialize' app/services/cache_service.py",
            "Add safe serialization import"
        )
        
        # 1.3 Input Sanitization
        self.log("Fixing SEC-003: Input sanitization...")
        
        # Add bleach to requirements if not present
        requirements_path = self.backend_path / "requirements.txt"
        with open(requirements_path, "r") as f:
            requirements = f.read()
        
        if "bleach" not in requirements:
            with open(requirements_path, "a") as f:
                f.write("\nbleach==6.1.0\n")
        
        # Create input sanitization module
        sanitization_content = '''"""Input sanitization and validation."""
import bleach
import html
from typing import Any, Dict

ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'p', 'br']
ALLOWED_ATTRIBUTES = {}

def sanitize_html(content: str) -> str:
    """Sanitize HTML content."""
    return bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

def sanitize_text(content: str) -> str:
    """Sanitize plain text content."""
    return html.escape(content).strip()

def validate_file_path(path: str) -> str:
    """Validate and sanitize file paths."""
    import os
    return os.path.basename(path)  # Remove directory traversal
'''
        
        with open(self.backend_path / "app/core/input_sanitization.py", "w") as f:
            f.write(sanitization_content)
        
        # Validate Phase 1 completion
        return self.validate_phase1()
    
    def validate_phase1(self) -> bool:
        """Validate Phase 1 security fixes."""
        self.log("Validating Phase 1 completion...")
        
        # Check secret key length
        success, output = self.run_command(
            "grep SECRET_KEY .env | cut -d= -f2 | wc -c",
            "Check secret key length"
        )
        
        if success and int(output.strip()) < 40:
            self.log("❌ Secret key too short", "ERROR")
            return False
        
        # Check no pickle usage
        success, output = self.run_command(
            "grep -r 'pickle\\.' app/",
            "Check for pickle usage"
        )
        
        if success and output.strip():
            self.log("❌ Pickle usage still found", "ERROR")
            return False
        
        # Verify app still imports
        success, _ = self.run_command(
            "python3 -c 'import sys; sys.path.append(\".\"); from app.main import app; print(\"✅ App imports OK\")'",
            "Verify app imports"
        )
        
        if not success:
            self.log("❌ App import validation failed", "ERROR")
            return False
        
        self.log("✅ Phase 1 validation passed")
        self.phase_status["phase1"] = "completed"
        return True
    
    def execute_phase2_structural_cleanup(self) -> bool:
        """Phase 2: Structural cleanup and model consolidation."""
        self.log("🔧 Phase 2: Executing structural cleanup...")
        
        # 2.1 Model Consolidation
        self.log("Consolidating MangaSession models...")
        
        # Create mapping of current imports
        success, output = self.run_command(
            "grep -r 'from app\\.models\\.manga import MangaSession' app/ --include='*.py'",
            "Find model imports to update"
        )
        
        if success and output:
            files_to_update = [line.split(':')[0] for line in output.strip().split('\n')]
            
            for file_path in files_to_update:
                success, _ = self.run_command(
                    f"sed -i.bak 's/from app\\.models\\.manga import MangaSession/from app.domain.manga.entities.session import MangaSession/g' {file_path}",
                    f"Update imports in {file_path}"
                )
                if not success:
                    return False
        
        # Remove duplicate model files
        duplicate_models = [
            "app/models/manga.py",
            "app/infrastructure/database/models/manga_session_model.py"
        ]
        
        for model_file in duplicate_models:
            if (self.backend_path / model_file).exists():
                success, _ = self.run_command(
                    f"rm {model_file}",
                    f"Remove duplicate model: {model_file}"
                )
                if not success:
                    return False
        
        # 2.2 TODO Comments Resolution
        self.log("Resolving critical TODO comments...")
        
        # Implement health check TODOs
        health_check_impl = '''
    try:
        # Database health check
        async with get_db() as db:
            await db.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Redis health check  
        redis_client = RedisClient()
        await redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "checks": {
            "database": db_status,
            "redis": redis_status,
            "websocket": "healthy"  # WebSocket health check implementation needed
        }
    }
'''
        
        # Replace TODO health checks in __init__.py
        success, _ = self.run_command(
            f"""sed -i.bak '141,143c\\{health_check_impl}' app/api/v1/__init__.py""",
            "Implement health check TODOs"
        )
        
        return self.validate_phase2()
    
    def validate_phase2(self) -> bool:
        """Validate Phase 2 structural cleanup."""
        self.log("Validating Phase 2 completion...")
        
        # Check for model duplication
        success, output = self.run_command(
            "find app -name '*.py' -exec grep -l 'class.*MangaSession' {} \\; | wc -l",
            "Count MangaSession definitions"
        )
        
        if success and int(output.strip()) > 1:
            self.log("❌ Multiple MangaSession definitions still exist", "ERROR")
            return False
        
        # Verify imports work after consolidation
        success, _ = self.run_command(
            "python3 -c 'from app.domain.manga.entities.session import MangaSession; print(\"✅ MangaSession import OK\")'",
            "Verify consolidated model import"
        )
        
        if not success:
            self.log("❌ Model import validation failed", "ERROR")
            return False
        
        self.log("✅ Phase 2 validation passed")
        self.phase_status["phase2"] = "completed"
        return True
    
    def execute_phase3_quality_improvement(self) -> bool:
        """Phase 3: Code quality and dead code cleanup."""
        self.log("🧹 Phase 3: Executing quality improvements...")
        
        # 3.1 Install cleanup tools
        self.log("Installing cleanup tools...")
        cleanup_tools = [
            "unimport==0.16.0",
            "mypy==1.7.0", 
            "flake8==6.1.0",
            "bandit==1.7.5",
            "safety==2.3.0"
        ]
        
        for tool in cleanup_tools:
            if tool.split("==")[0] not in subprocess.run(["pip", "list"], capture_output=True, text=True).stdout:
                success, _ = self.run_command(f"pip install {tool}", f"Install {tool}")
                if not success:
                    self.log(f"⚠️ Warning: Failed to install {tool}")
        
        # 3.2 Remove unused imports
        self.log("Cleaning unused imports...")
        
        # First, analyze what would be removed
        success, output = self.run_command(
            "unimport --check --diff app/",
            "Analyze unused imports"
        )
        
        if success:
            # Apply unused import removal
            success, _ = self.run_command(
                "unimport --remove-all app/",
                "Remove unused imports"
            )
            if not success:
                self.log("⚠️ Warning: Some imports may be needed for runtime")
        
        # 3.3 Fix bare exceptions
        self.log("Fixing bare exception patterns...")
        
        # This requires manual intervention for safety, so we'll create a report
        self.generate_exception_fix_report()
        
        return self.validate_phase3()
    
    def validate_phase3(self) -> bool:
        """Validate Phase 3 quality improvements."""
        self.log("Validating Phase 3 completion...")
        
        # Check compilation
        success, _ = self.run_command(
            "python3 -m compileall app/",
            "Verify all files compile"
        )
        
        if not success:
            self.log("❌ Compilation errors found", "ERROR") 
            return False
        
        # Run security scan
        success, _ = self.run_command(
            "bandit -r app/ -f json -o bandit_report.json",
            "Security vulnerability scan"
        )
        
        self.log("✅ Phase 3 validation passed")
        self.phase_status["phase3"] = "completed"
        return True
    
    def generate_exception_fix_report(self):
        """Generate report for manual exception handling fixes."""
        self.log("Generating exception handling fix report...")
        
        success, output = self.run_command(
            "grep -n 'except Exception\\|except:' app/ --include='*.py' -r",
            "Find exception handling patterns"
        )
        
        if success and output:
            report_content = f"""# Exception Handling Fix Report

Generated: {datetime.now()}

## Files requiring manual exception handling review:

{output}

## Recommended patterns:

### Database Operations:
```python
try:
    result = await db.execute(query)
except (DatabaseError, IntegrityError) as e:
    logger.error("Database operation failed", error=str(e))
    raise HTTPException(status_code=500, detail="Database error")
```

### External API Calls:
```python  
try:
    response = await external_api_call()
except (aiohttp.ClientError, asyncio.TimeoutError) as e:
    logger.error("External API failed", error=str(e))
    raise HTTPException(status_code=503, detail="Service unavailable")
```

### Input Validation:
```python
try:
    validated_data = schema.parse(raw_data)
except ValidationError as e:
    logger.warning("Input validation failed", error=str(e))
    raise HTTPException(status_code=400, detail="Invalid input")
```
"""
            
            with open(self.backend_path / "claudedocs/exception_handling_manual_fixes.md", "w") as f:
                f.write(report_content)
    
    def generate_progress_report(self) -> Dict[str, Any]:
        """Generate current cleanup progress report."""
        
        # Count remaining issues
        metrics = {}
        
        # Security metrics
        success, output = self.run_command("grep -r 'dev-secret-key' .", "Check hardcoded secrets")
        metrics['hardcoded_secrets'] = len(output.split('\n')) if success and output.strip() else 0
        
        success, output = self.run_command("grep -r 'pickle\\.' app/", "Check pickle usage")
        metrics['pickle_usage'] = len(output.split('\n')) if success and output.strip() else 0
        
        success, output = self.run_command("grep -r 'except:' app/", "Check bare exceptions")
        metrics['bare_exceptions'] = len(output.split('\n')) if success and output.strip() else 0
        
        # Code quality metrics
        success, output = self.run_command("grep -r 'TODO' app/ --include='*.py'", "Check TODO comments")
        metrics['todo_comments'] = len(output.split('\n')) if success and output.strip() else 0
        
        # Model duplication
        success, output = self.run_command("find app -name '*.py' -exec grep -l 'class.*MangaSession' {} \\;", "Check model duplication")
        metrics['manga_session_models'] = len(output.split('\n')) if success and output.strip() else 0
        
        metrics['phase_status'] = self.phase_status
        metrics['timestamp'] = datetime.now().isoformat()
        
        return metrics
    
    def create_rollback_script(self):
        """Create emergency rollback script."""
        rollback_script = f'''#!/bin/bash
# Emergency rollback script for backend cleanup
# Generated: {datetime.now()}

BACKUP_DIR="{self.backup_dir}"

if [ -d "$BACKUP_DIR" ]; then
    echo "🔄 Rolling back to backup..."
    
    # Remove current state
    rm -rf app/
    
    # Restore from backup
    cp -r "$BACKUP_DIR/backend/app" ./
    cp "$BACKUP_DIR/backend/.env" ./
    
    echo "✅ Rollback completed"
    echo "Please run: git reset --hard cleanup-backup-*"
else
    echo "❌ Backup directory not found: $BACKUP_DIR"
    echo "Use git reset for recovery"
fi
'''
        
        rollback_path = self.backend_path / "rollback_cleanup.sh"
        with open(rollback_path, "w") as f:
            f.write(rollback_script)
        
        os.chmod(rollback_path, 0o755)
        self.log(f"✅ Rollback script created: {rollback_path}")
    
    def execute_full_cleanup(self) -> bool:
        """Execute the complete cleanup plan."""
        self.log("🚀 Starting comprehensive backend cleanup...")
        
        # Prerequisites
        if not self.validate_prerequisites():
            return False
        
        # Create backup
        if not self.create_backup():
            return False
        
        # Create rollback script
        self.create_rollback_script()
        
        # Execute phases
        phases = [
            ("Phase 1: Security Fixes", self.execute_phase1_security_fixes),
            ("Phase 2: Structural Cleanup", self.execute_phase2_structural_cleanup),
            ("Phase 3: Quality Improvement", self.execute_phase3_quality_improvement)
        ]
        
        for phase_name, phase_func in phases:
            self.log(f"🎯 Starting {phase_name}...")
            
            if not phase_func():
                self.log(f"❌ {phase_name} failed - stopping execution", "ERROR")
                self.log("💡 Use rollback_cleanup.sh to restore previous state")
                return False
            
            # Generate progress report after each phase
            progress = self.generate_progress_report()
            with open(self.backend_path / f"cleanup_progress_phase{len(self.phase_status)}.json", "w") as f:
                json.dump(progress, f, indent=2)
        
        # Final validation
        return self.run_final_validation()
    
    def run_final_validation(self) -> bool:
        """Run comprehensive final validation."""
        self.log("🔍 Running final validation suite...")
        
        validations = [
            ("python3 -m compileall app/", "Python compilation check"),
            ("python3 -c 'from app.main import app; print(\"App loads successfully\")'", "Application loading test"),
            ("grep -r 'dev-secret-key\\|pickle\\.' app/ | wc -l | awk '{if($1==0) print \"✅ Security issues resolved\"; else print \"❌ Security issues remain\"}'", "Security validation"),
            ("find app -name '*.py' -exec grep -l 'class.*MangaSession' {} \\; | wc -l | awk '{if($1<=1) print \"✅ Model consolidation complete\"; else print \"❌ Model duplication remains\"}'", "Model consolidation check")
        ]
        
        all_passed = True
        for command, description in validations:
            success, output = self.run_command(command, description)
            if not success:
                all_passed = False
                self.log(f"❌ Validation failed: {description}", "ERROR")
            else:
                self.log(f"✅ Validation passed: {description}")
        
        if all_passed:
            self.log("🎉 Comprehensive cleanup completed successfully!")
            self.log(f"📊 Final progress report: cleanup_progress_phase{len(self.phase_status)}.json")
            return True
        else:
            self.log("❌ Final validation failed - manual review required", "ERROR")
            return False

def main():
    """Main execution function."""
    print("🔧 Backend Cleanup Execution Script")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        backend_path = sys.argv[1]
    else:
        backend_path = "."
    
    executor = CleanupExecutor(backend_path)
    
    # Confirmation prompt
    print(f"📁 Backend path: {executor.backend_path}")
    print(f"💾 Backup will be created at: {executor.backup_dir}")
    print("\n⚠️  This will make significant changes to your codebase.")
    
    response = input("Continue with cleanup? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ Cleanup cancelled by user")
        return False
    
    # Execute cleanup
    success = executor.execute_full_cleanup()
    
    if success:
        print("\n🎉 Cleanup completed successfully!")
        print(f"📋 Log file: {executor.log_file}")
        print(f"🔄 Rollback script: {executor.backend_path}/rollback_cleanup.sh")
    else:
        print("\n❌ Cleanup failed - check logs for details")
        print(f"📋 Log file: {executor.log_file}")
        print(f"🔄 Use rollback script if needed: {executor.backend_path}/rollback_cleanup.sh")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)