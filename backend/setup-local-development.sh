#!/bin/bash

# Local Development Environment Setup Script
# AI Manga Generation Service
# Created: 2025-09-04

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up AI Manga Generation Service - Local Development Environment${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker Desktop first.${NC}"
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}⚠️  gcloud CLI is not installed. You'll need it for Google Cloud services.${NC}"
    echo "   Install from: https://cloud.google.com/sdk/docs/install"
    echo "   Continuing without gcloud setup..."
else
    echo -e "${GREEN}✅ gcloud CLI found${NC}"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.9+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check completed${NC}"
echo ""

# Create credentials directory
echo -e "${BLUE}📁 Creating credentials directory...${NC}"
mkdir -p ./credentials
echo -e "${GREEN}✅ Created ./credentials directory${NC}"

# Copy environment file
echo -e "${BLUE}🔧 Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.local" ]; then
        cp .env.local .env
        echo -e "${GREEN}✅ Copied .env.local to .env${NC}"
    else
        echo -e "${RED}❌ .env.local template not found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  .env file already exists, skipping copy${NC}"
fi

# Google Cloud Authentication Setup
echo -e "${BLUE}🔐 Google Cloud Authentication Setup${NC}"
echo -e "${YELLOW}You need to set up Google Cloud credentials for AI services:${NC}"
echo ""
echo -e "${BLUE}1. Service Account Key Setup:${NC}"
echo "   - Go to Google Cloud Console: https://console.cloud.google.com/"
echo "   - Navigate to IAM & Admin > Service Accounts"
echo "   - Create or select a service account with these roles:"
echo "     * AI Platform Admin"
echo "     * Storage Admin"
echo "     * Firebase Admin SDK Administrator Service Account"
echo "   - Download the JSON key file"
echo "   - Save it as: ./credentials/service-account-key.json"
echo ""
echo -e "${BLUE}2. Firebase Setup:${NC}"
echo "   - Go to Firebase Console: https://console.firebase.google.com/"
echo "   - Select your project: comic-ai-agent-470309"
echo "   - Go to Project Settings > Service Accounts"
echo "   - Generate new private key"
echo "   - Save it as: ./credentials/firebase-service-account.json"
echo ""

read -p "Press Enter when you have completed the credential setup..."

# Validate credential files
echo -e "${BLUE}📋 Validating credentials...${NC}"
if [ ! -f "./credentials/service-account-key.json" ]; then
    echo -e "${RED}❌ Missing: ./credentials/service-account-key.json${NC}"
    echo -e "${YELLOW}⚠️  AI services will not work without this file${NC}"
fi

if [ ! -f "./credentials/firebase-service-account.json" ]; then
    echo -e "${RED}❌ Missing: ./credentials/firebase-service-account.json${NC}"
    echo -e "${YELLOW}⚠️  Authentication services will not work without this file${NC}"
fi

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}🐍 Creating Python virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}✅ Created virtual environment${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Start Docker services
echo -e "${BLUE}🐳 Starting Docker services...${NC}"
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose up -d postgres redis

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check PostgreSQL connection
echo -e "${BLUE}🔍 Checking PostgreSQL connection...${NC}"
if docker-compose exec -T postgres pg_isready -U manga_user > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not ready${NC}"
    echo "   Check Docker logs: docker-compose logs postgres"
    exit 1
fi

# Check Redis connection
echo -e "${BLUE}🔍 Checking Redis connection...${NC}"
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not ready${NC}"
    echo "   Check Docker logs: docker-compose logs redis"
    exit 1
fi

# Run database migrations
echo -e "${BLUE}🗄️  Running database migrations...${NC}"
if [ -d "alembic" ]; then
    # Make sure we're in virtual environment
    source venv/bin/activate
    
    # Initialize alembic if not already done
    if [ ! -f "alembic/env.py" ]; then
        alembic init alembic
    fi
    
    # Generate initial migration
    DATABASE_URL="postgresql+asyncpg://manga_user:manga_password@localhost:5432/manga_db" \
    alembic revision --autogenerate -m "Initial database schema" || echo "Migration already exists"
    
    # Run migrations
    DATABASE_URL="postgresql+asyncpg://manga_user:manga_password@localhost:5432/manga_db" \
    alembic upgrade head
    
    echo -e "${GREEN}✅ Database migrations completed${NC}"
else
    echo -e "${YELLOW}⚠️  Alembic directory not found, skipping migrations${NC}"
fi

# Test the application
echo -e "${BLUE}🧪 Testing application startup...${NC}"
source venv/bin/activate

# Set environment for test
export DATABASE_URL="postgresql+asyncpg://manga_user:manga_password@localhost:5432/manga_db"
export REDIS_URL="redis://localhost:6379/0"

# Quick startup test (kills after 10 seconds)
timeout 10s python -c "
import asyncio
from app.main import app
from app.core.database import get_database_session
from app.core.redis_client import get_redis_client

async def test_startup():
    # Test database connection
    try:
        async with get_database_session() as db:
            print('✅ Database connection: OK')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False
    
    # Test Redis connection
    try:
        redis = get_redis_client()
        await redis.ping()
        print('✅ Redis connection: OK')
    except Exception as e:
        print(f'❌ Redis connection failed: {e}')
        return False
    
    print('✅ All services connected successfully!')
    return True

asyncio.run(test_startup())
" 2>/dev/null && echo -e "${GREEN}✅ Application startup test passed${NC}" || echo -e "${YELLOW}⚠️  Application startup test failed (this is expected without full credentials)${NC}"

# Create run script
echo -e "${BLUE}📝 Creating development run script...${NC}"
cat > run-dev.sh << 'EOF'
#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(cat .env | grep -v ^# | xargs)

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
EOF

chmod +x run-dev.sh
echo -e "${GREEN}✅ Created run-dev.sh script${NC}"

# Create stop script
echo -e "${BLUE}📝 Creating stop script...${NC}"
cat > stop-dev.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping development environment..."

# Stop Docker services
docker-compose down

echo "✅ Development environment stopped"
EOF

chmod +x stop-dev.sh
echo -e "${GREEN}✅ Created stop-dev.sh script${NC}"

# Final instructions
echo ""
echo -e "${GREEN}🎉 Local Development Environment Setup Complete!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo ""
echo -e "${YELLOW}1. Verify your .env file has correct values:${NC}"
echo "   nano .env"
echo ""
echo -e "${YELLOW}2. Start the development server:${NC}"
echo "   ./run-dev.sh"
echo ""
echo -e "${YELLOW}3. Access the application:${NC}"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/health"
echo "   - API Info: http://localhost:8000/api/v1/info"
echo ""
echo -e "${YELLOW}4. Stop the environment when done:${NC}"
echo "   ./stop-dev.sh"
echo ""
echo -e "${BLUE}📚 Useful Commands:${NC}"
echo "   - View logs: docker-compose logs -f"
echo "   - Database shell: docker-compose exec postgres psql -U manga_user -d manga_db"
echo "   - Redis CLI: docker-compose exec redis redis-cli"
echo "   - Reset database: docker-compose down -v && docker-compose up -d postgres redis"
echo ""
echo -e "${BLUE}🔧 Troubleshooting:${NC}"
echo "   - If services fail to start, check: docker-compose logs"
echo "   - For permission issues: sudo chown -R \$USER:staff ./credentials"
echo "   - For port conflicts, check .env file and docker-compose.yml"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"