@echo off
setlocal enabledelayedexpansion

REM ===============================================================================
REM IUH Microservices AI - Unified Automated Test Suite Runner (Windows CMD / PS)
REM Supports individual service testing, coverage threshold validation (>= 80%)
REM ===============================================================================

set "TARGET=%1"
if "%TARGET%"=="" set "TARGET=all"

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ===============================================================================
echo  IUH Microservices AI - Automated Test Runner
echo  Target: [%TARGET%]
echo ===============================================================================

set "EXIT_CODE=0"

if "%TARGET%"=="all" goto RUN_ALL
if "%TARGET%"=="auth" goto RUN_AUTH
if "%TARGET%"=="academic" goto RUN_ACADEMIC
if "%TARGET%"=="realtime" goto RUN_REALTIME
if "%TARGET%"=="doc" goto RUN_DOC
if "%TARGET%"=="flashcard" goto RUN_FLASHCARD
if "%TARGET%"=="frontend" goto RUN_FRONTEND
if "%TARGET%"=="eval" goto RUN_EVAL

echo [ERROR] Unknown test target: %TARGET%
echo Usage: run_tests.bat [all^|auth^|academic^|realtime^|doc^|flashcard^|frontend^|eval]
exit /b 1

:RUN_AUTH
echo.
echo [1/1] Running Auth Service Tests...
pytest services/auth_service/tests -v --cov=services/auth_service/app --cov-fail-under=80
if %errorlevel% neq 0 (
    echo [FAIL] Auth Service tests failed or coverage is below 80%%
    exit /b 1
)
echo [PASS] Auth Service tests completed successfully.
exit /b 0

:RUN_ACADEMIC
echo.
echo [1/1] Running Academic Chatbot Service Tests...
pytest services/academic_chatbot_service/tests -v --cov=services/academic_chatbot_service/app
if %errorlevel% neq 0 (
    echo [FAIL] Academic Chatbot Service tests failed
    exit /b 1
)
echo [PASS] Academic Chatbot Service tests completed successfully.
exit /b 0

:RUN_REALTIME
echo.
echo [1/1] Running Real-time Translation Service Tests...
pytest services/realtime_translation_service/tests -v --cov=services/realtime_translation_service/app
if %errorlevel% neq 0 (
    echo [FAIL] Real-time Translation Service tests failed
    exit /b 1
)
echo [PASS] Real-time Translation Service tests completed successfully.
exit /b 0

:RUN_DOC
echo.
echo [1/1] Running Document Translation & RAG Service Tests...
pytest services/doc_translation_service/tests -v --cov=services/doc_translation_service/app
if %errorlevel% neq 0 (
    echo [FAIL] Document Translation Service tests failed
    exit /b 1
)
echo [PASS] Document Translation Service tests completed successfully.
exit /b 0

:RUN_FLASHCARD
echo.
echo [1/1] Running Flashcard Spaced Repetition Service Tests...
pytest services/flashcard_service/tests -v --cov=services/flashcard_service/app
if %errorlevel% neq 0 (
    echo [FAIL] Flashcard Service tests failed
    exit /b 1
)
echo [PASS] Flashcard Service tests completed successfully.
exit /b 0

:RUN_FRONTEND
echo.
echo [1/1] Running Frontend Vitest Suite...
cd frontend
call npx vitest run
set "FE_STATUS=%errorlevel%"
cd ..
if %FE_STATUS% neq 0 (
    echo [FAIL] Frontend tests failed
    exit /b 1
)
echo [PASS] Frontend tests completed successfully.
exit /b 0

:RUN_EVAL
echo.
echo [1/1] Running RAG Benchmark Evaluation Suite...
pytest scripts/eval/test_rag_benchmark.py -v
if %errorlevel% neq 0 (
    echo [FAIL] RAG Benchmark Evaluation tests failed
    exit /b 1
)
echo [PASS] RAG Benchmark Evaluation completed successfully.
exit /b 0

:RUN_ALL
echo.
echo ===============================================================================
echo  Running ALL Microservices Test Suites & Quality Gates
echo ===============================================================================

echo.
echo [1/7] Testing Auth Service...
pytest services/auth_service/tests -v --cov=services/auth_service/app
if %errorlevel% neq 0 set "EXIT_CODE=1"

echo.
echo [2/7] Testing Academic Chatbot Service...
pytest services/academic_chatbot_service/tests -v --cov=services/academic_chatbot_service/app
if %errorlevel% neq 0 set "EXIT_CODE=1"

echo.
echo [3/7] Testing Real-time Translation Service...
pytest services/realtime_translation_service/tests -v --cov=services/realtime_translation_service/app
if %errorlevel% neq 0 set "EXIT_CODE=1"

echo.
echo [4/7] Testing Document Translation & RAG Service...
pytest services/doc_translation_service/tests -v --cov=services/doc_translation_service/app
if %errorlevel% neq 0 set "EXIT_CODE=1"

echo.
echo [5/7] Testing Flashcard Service...
pytest services/flashcard_service/tests -v --cov=services/flashcard_service/app
if %errorlevel% neq 0 set "EXIT_CODE=1"

echo.
echo [6/7] Testing RAG Benchmark Evaluation...
pytest scripts/eval/test_rag_benchmark.py -v
if %errorlevel% neq 0 set "EXIT_CODE=1"

echo.
echo [7/7] Testing Frontend React / Vitest...
cd frontend
call npx vitest run
if %errorlevel% neq 0 set "EXIT_CODE=1"
cd ..

echo.
echo ===============================================================================
if %EXIT_CODE% equ 0 (
    echo  [ALL TESTS PASSED] 100%% Test Suites Succeeded! System ready for deployment.
) else (
    echo  [TESTS FAILED] Some test suites failed. Please review the logs above.
)
echo ===============================================================================
exit /b %EXIT_CODE%
