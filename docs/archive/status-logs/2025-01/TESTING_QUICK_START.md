# 🧪 Testing Quick Start Guide

**0711 Intelligence Platform - E2E Testing**

---

## ⚡ Quick Commands

```bash
# 1. Install dependencies
pip install pytest pytest-asyncio pytest-cov httpx websockets minio

# 2. Start services
./START_ALL.sh

# 3. Run E2E tests
./run_e2e_tests.sh
```

---

## 🎯 Common Use Cases

### Run All E2E Tests

```bash
./run_e2e_tests.sh
```

### Run Fast Tests Only (Skip Slow)

```bash
./run_e2e_tests.sh fast
```

### Run Specific Test Suite

```bash
# Onboarding flow
./run_e2e_tests.sh onboarding

# Data ingestion
./run_e2e_tests.sh ingestion

# Chat interactions
./run_e2e_tests.sh chat

# Customer isolation
./run_e2e_tests.sh isolation

# MCP orchestration
./run_e2e_tests.sh mcp

# Authentication
./run_e2e_tests.sh auth
```

### Run All Tests with Coverage

```bash
./run_all_tests.sh
```

### Run Specific Test Type

```bash
# Unit tests only
./run_all_tests.sh --unit

# Integration tests
./run_all_tests.sh --integration

# E2E tests
./run_all_tests.sh --e2e
```

---

## 📁 Test Structure

```
tests/
├── e2e/                                    # End-to-end tests
│   ├── test_complete_onboarding_flow.py   # 9 tests
│   ├── test_data_ingestion_flow.py        # 9 tests
│   ├── test_chat_interaction_flow.py      # 15 tests
│   ├── test_customer_isolation.py         # 11 tests
│   ├── test_mcp_orchestration.py          # 13 tests
│   └── test_authentication_flow.py        # 12 tests
├── utils/                                  # Test utilities
│   ├── api_client.py                      # HTTP clients
│   ├── websocket_client.py                # WebSocket client
│   └── docker_manager.py                  # Docker management
└── fixtures/                               # Test data
    └── sample_data/                        # Sample files
```

**Total: 69 E2E tests**

---

## 🔍 Run Individual Tests

```bash
# Single file
pytest tests/e2e/test_chat_interaction_flow.py -v

# Single test
pytest tests/e2e/test_chat_interaction_flow.py::TestChatInteractionFlow::test_rest_chat_basic -v

# With debug output
pytest tests/e2e/test_chat_interaction_flow.py -vv --log-cli-level=DEBUG
```

---

## 🏷️ Test Markers

```bash
# E2E tests
pytest -m e2e -v

# E2E but not slow
pytest -m "e2e and not slow" -v

# Integration tests
pytest -m integration -v

# Unit tests
pytest -m unit -v
```

---

## 🐛 Troubleshooting

### Services Not Running

```bash
# Check health
curl http://localhost:4080/health
curl http://localhost:4010/health

# Start services
./START_ALL.sh

# Check logs
tail -f /tmp/0711_api.log
tail -f /tmp/0711_console_backend.log
```

### Tests Failing

```bash
# Run with verbose output
pytest -vv tests/e2e/

# Skip failing test
pytest -v -k "not test_failing"

# Run only one test
pytest tests/e2e/test_chat_interaction_flow.py::TestChatInteractionFlow::test_rest_chat_basic
```

### Reset Test Environment

```bash
# Stop all services
./STOP_ALL.sh

# Clean up Docker
docker-compose down -v

# Restart
./START_ALL.sh
```

---

## 📊 Coverage

```bash
# Generate HTML coverage report
./run_all_tests.sh

# Open report
firefox htmlcov/index.html

# Terminal coverage report
pytest --cov=ingestion --cov=lakehouse --cov=mcps --cov-report=term-missing
```

---

## 🔧 Configuration

### Environment Variables

Set in `pytest.ini` or override:

```bash
TEST_API_BASE=http://localhost:4080
TEST_CONSOLE_BASE=http://localhost:4010
TEST_MINIO_ENDPOINT=localhost:4050
TEST_MINIO_ACCESS_KEY=0711admin
TEST_MINIO_SECRET_KEY=0711secret
```

### Test Timeout

Default: 300 seconds (5 minutes)

Change in `pytest.ini`:
```ini
timeout = 600  # 10 minutes
```

---

## 📚 Documentation

- **Comprehensive Guide**: `tests/README.md`
- **Implementation Summary**: `E2E_TESTING_SUMMARY.md`
- **This Quick Start**: `TESTING_QUICK_START.md`

---

## 💡 Tips

1. **Run fast tests first** for quick feedback: `./run_e2e_tests.sh fast`
2. **Use markers** to run specific test types: `pytest -m "e2e and not slow"`
3. **Check service health** before running tests
4. **Run with coverage** periodically to track progress
5. **Use `-vv` flag** for detailed output when debugging

---

## 🎯 Test Scenarios Covered

✅ Complete onboarding flow (signup → deployment)
✅ Data ingestion (upload → process → lakehouse)
✅ Real-time chat (REST + WebSocket)
✅ Customer isolation (multi-tenancy)
✅ MCP orchestration (CTAX, LAW, TENDER)
✅ Authentication & authorization (JWT, permissions)

**69 comprehensive E2E tests ready to use!** 🚀

---

## 🚀 Next Steps

1. Run tests: `./run_e2e_tests.sh`
2. Check coverage: `./run_all_tests.sh`
3. Read docs: `tests/README.md`
4. Write new tests as needed
5. Keep tests updated with new features

**Happy testing!** 🧪
