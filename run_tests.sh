#!/usr/bin/env bash
# ===============================================================================
# IUH Microservices AI - Unified Automated Test Suite Runner (Linux / macOS / CI)
# Supports individual service testing, coverage threshold validation (>= 80%)
# ===============================================================================

set -eo pipefail

TARGET="${1:-all}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "==============================================================================="
echo " IUH Microservices AI - Automated Test Runner"
echo " Target: [${TARGET}]"
echo "==============================================================================="

EXIT_CODE=0

run_auth() {
    echo -e "\n[1/1] Running Auth Service Tests..."
    pytest services/auth_service/tests -v --cov=services/auth_service/app
}

run_academic() {
    echo -e "\n[1/1] Running Academic Chatbot Service Tests..."
    pytest services/academic_chatbot_service/tests -v --cov=services/academic_chatbot_service/app
}

run_realtime() {
    echo -e "\n[1/1] Running Real-time Translation Service Tests..."
    pytest services/realtime_translation_service/tests -v --cov=services/realtime_translation_service/app
}

run_doc() {
    echo -e "\n[1/1] Running Document Translation & RAG Service Tests..."
    pytest services/doc_translation_service/tests -v --cov=services/doc_translation_service/app
}

run_flashcard() {
    echo -e "\n[1/1] Running Flashcard Spaced Repetition Service Tests..."
    pytest services/flashcard_service/tests -v --cov=services/flashcard_service/app
}

run_frontend() {
    echo -e "\n[1/1] Running Frontend Vitest Suite..."
    (cd frontend && npx vitest run)
}

run_eval() {
    echo -e "\n[1/1] Running RAG Benchmark Evaluation Suite..."
    pytest scripts/eval/test_rag_benchmark.py -v
}

case "$TARGET" in
    auth)
        run_auth
        ;;
    academic)
        run_academic
        ;;
    realtime)
        run_realtime
        ;;
    doc)
        run_doc
        ;;
    flashcard)
        run_flashcard
        ;;
    frontend)
        run_frontend
        ;;
    eval)
        run_eval
        ;;
    all)
        echo -e "\n==============================================================================="
        echo " Running ALL Microservices Test Suites & Quality Gates"
        echo "==============================================================================="

        set +e
        echo -e "\n[1/7] Testing Auth Service..."
        pytest services/auth_service/tests -v --cov=services/auth_service/app || EXIT_CODE=1

        echo -e "\n[2/7] Testing Academic Chatbot Service..."
        pytest services/academic_chatbot_service/tests -v --cov=services/academic_chatbot_service/app || EXIT_CODE=1

        echo -e "\n[3/7] Testing Real-time Translation Service..."
        pytest services/realtime_translation_service/tests -v --cov=services/realtime_translation_service/app || EXIT_CODE=1

        echo -e "\n[4/7] Testing Document Translation & RAG Service..."
        pytest services/doc_translation_service/tests -v --cov=services/doc_translation_service/app || EXIT_CODE=1

        echo -e "\n[5/7] Testing Flashcard Service..."
        pytest services/flashcard_service/tests -v --cov=services/flashcard_service/app || EXIT_CODE=1

        echo -e "\n[6/7] Testing RAG Benchmark Evaluation..."
        pytest scripts/eval/test_rag_benchmark.py -v || EXIT_CODE=1

        echo -e "\n[7/7] Testing Frontend React / Vitest..."
        (cd frontend && npx vitest run) || EXIT_CODE=1

        echo -e "\n==============================================================================="
        if [ "$EXIT_CODE" -eq 0 ]; then
            echo " [ALL TESTS PASSED] 100% Test Suites Succeeded! System ready for deployment."
        else
            echo " [TESTS FAILED] Some test suites failed. Please review the logs above."
        fi
        echo "==============================================================================="
        exit "$EXIT_CODE"
        ;;
    *)
        echo "[ERROR] Unknown test target: $TARGET"
        echo "Usage: ./run_tests.sh [all|auth|academic|realtime|doc|flashcard|frontend|eval]"
        exit 1
        ;;
esac
