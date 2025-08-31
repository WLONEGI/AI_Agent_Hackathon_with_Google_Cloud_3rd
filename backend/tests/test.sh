#!/bin/bash
# Backend Compliance Test Script
# 設計書準拠性テストのローカル実行用スクリプト

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_SUITE="all"
OUTPUT_DIR="test_results"
REPORT_ONLY=false
VERBOSE=false

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Backend Compliance Test Runner"
    echo ""
    echo "Options:"
    echo "  -s, --suite SUITE      Test suite to run (compliance|contracts|all) [default: all]"
    echo "  -o, --output DIR       Output directory for test results [default: test_results]"
    echo "  -r, --report-only      Generate report only, skip test execution"
    echo "  -v, --verbose          Verbose output"
    echo "  -c, --clean            Clean output directory before running"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Run all tests"
    echo "  $0 -s compliance                # Run compliance tests only"
    echo "  $0 -s contracts -v              # Run contract tests with verbose output"
    echo "  $0 -r                           # Generate report only"
    echo "  $0 -c -s all                    # Clean and run all tests"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--suite)
            TEST_SUITE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -r|--report-only)
            REPORT_ONLY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate test suite
if [[ ! "$TEST_SUITE" =~ ^(compliance|contracts|all)$ ]]; then
    echo -e "${RED}Error: Invalid test suite '$TEST_SUITE'. Must be one of: compliance, contracts, all${NC}"
    exit 1
fi

# Print header
echo -e "${BLUE}🧪 Backend Compliance Test Runner${NC}"
echo -e "${BLUE}===================================${NC}"
echo ""

# Clean output directory if requested
if [[ "$CLEAN" == true && -d "$OUTPUT_DIR" ]]; then
    echo -e "${YELLOW}🧹 Cleaning output directory: $OUTPUT_DIR${NC}"
    rm -rf "$OUTPUT_DIR"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if we're in the backend directory
if [[ ! -f "run_compliance_tests.py" ]]; then
    echo -e "${RED}❌ Error: run_compliance_tests.py not found${NC}"
    echo "Make sure you're running this script from the backend directory"
    exit 1
fi

# Check Python version
echo -e "${BLUE}🔍 Checking Python environment...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if required packages are installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
MISSING_PACKAGES=()

for package in pytest pyyaml jinja2; do
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Missing packages: ${MISSING_PACKAGES[*]}${NC}"
    echo "Installing missing packages..."
    pip3 install "${MISSING_PACKAGES[@]}"
fi

# Set environment variables
export PYTHONPATH="$(pwd)"

# Prepare command line arguments
ARGS=(--suite "$TEST_SUITE" --output-dir "$OUTPUT_DIR")

if [[ "$REPORT_ONLY" == true ]]; then
    ARGS+=(--report-only)
fi

if [[ "$VERBOSE" == true ]]; then
    echo -e "${BLUE}📋 Command: python3 run_compliance_tests.py ${ARGS[*]}${NC}"
    echo ""
fi

# Run the test runner
echo -e "${GREEN}🚀 Starting test execution...${NC}"
echo "Test Suite: $TEST_SUITE"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Execute the Python test runner
if python3 run_compliance_tests.py "${ARGS[@]}"; then
    echo ""
    echo -e "${GREEN}✅ Test execution completed successfully!${NC}"
    
    # Display results summary
    if [[ -f "$OUTPUT_DIR/test_summary.json" ]]; then
        echo ""
        echo -e "${BLUE}📊 Test Summary:${NC}"
        python3 -c "
import json
try:
    with open('$OUTPUT_DIR/test_summary.json', 'r') as f:
        summary = json.load(f)
    success_rate = (summary['successful_suites'] / summary['total_suites'] * 100) if summary['total_suites'] > 0 else 0
    print(f'  • Total Suites: {summary[\"total_suites\"]}')
    print(f'  • Successful: {summary[\"successful_suites\"]}')
    print(f'  • Success Rate: {success_rate:.1f}%')
    print(f'  • Duration: {summary[\"total_duration\"]:.2f} seconds')
except Exception as e:
    print(f'  Error reading summary: {e}')
"
    fi
    
    # Display available reports
    echo ""
    echo -e "${BLUE}📋 Available Reports:${NC}"
    for file in "$OUTPUT_DIR"/*.html "$OUTPUT_DIR"/*.json "$OUTPUT_DIR"/*.xml; do
        if [[ -f "$file" ]]; then
            echo "  • $(basename "$file")"
        fi
    done
    
    # Open HTML report if available
    if [[ -f "$OUTPUT_DIR/compliance_report.html" ]]; then
        echo ""
        echo -e "${GREEN}📊 HTML compliance report generated: $OUTPUT_DIR/compliance_report.html${NC}"
        
        # Try to open the report in browser (macOS/Linux)
        if command -v open >/dev/null 2>&1; then
            echo "Opening report in browser..."
            open "$OUTPUT_DIR/compliance_report.html"
        elif command -v xdg-open >/dev/null 2>&1; then
            echo "Opening report in browser..."
            xdg-open "$OUTPUT_DIR/compliance_report.html"
        fi
    fi
    
else
    echo ""
    echo -e "${RED}❌ Test execution failed!${NC}"
    echo "Check the output above for error details."
    exit 1
fi