#!/bin/bash
# Complete E2E Test Suite Runner
# Runs all E2E tests individually due to GTK application registration limitations

set -e

cd "$(dirname "$0")"
source .venv/bin/activate

echo "========================================"
echo "HyprBind E2E Test Suite"
echo "========================================"
echo ""

# Initialize counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
START_TIME=$(date +%s)

# Function to run a test and track results
run_test() {
    local test_path="$1"
    local test_name="$2"

    echo "Running: $test_name"

    if pytest "$test_path" -v --tb=short 2>&1 | tee /tmp/pytest_output.txt | grep -q "PASSED"; then
        # Count number of passed tests
        local passed=$(grep -c "PASSED" /tmp/pytest_output.txt || echo 0)
        PASSED_TESTS=$((PASSED_TESTS + passed))
        TOTAL_TESTS=$((TOTAL_TESTS + passed))
        echo "  ✓ Passed ($passed tests)"
    else
        # Count number of failed tests
        local failed=$(grep -c "FAILED\|ERROR" /tmp/pytest_output.txt || echo 1)
        FAILED_TESTS=$((FAILED_TESTS + failed))
        TOTAL_TESTS=$((TOTAL_TESTS + failed))
        echo "  ✗ Failed ($failed tests)"
    fi
    echo ""
}

# Infrastructure tests (can run together)
echo "=== Infrastructure Tests ==="
run_test "tests/e2e/test_app_lifecycle.py tests/e2e/test_gtk_utils.py" "Infrastructure (app_lifecycle + gtk_utils)"

# Workflow tests (must run individually)
echo "=== Workflow Tests ==="
run_test "tests/e2e/test_add_binding.py::test_add_binding_end_to_end" "Add Binding"
run_test "tests/e2e/test_edit_binding.py::test_edit_binding_end_to_end" "Edit Binding"
run_test "tests/e2e/test_delete_binding.py::test_delete_binding_with_confirmation" "Delete Binding"
run_test "tests/e2e/test_mode_switching.py::test_safe_to_live_mode_switch" "Safe to Live Mode Switch"
run_test "tests/e2e/test_mode_switching.py::test_live_to_safe_mode_switch" "Live to Safe Mode Switch"
run_test "tests/e2e/test_config_lifecycle.py::test_load_and_save_config" "Config Lifecycle"

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Print summary
echo "========================================"
echo "Test Suite Summary"
echo "========================================"
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Elapsed Time: ${ELAPSED}s"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi
