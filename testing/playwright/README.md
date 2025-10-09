# LAMB Playwright Tests

Automated browser tests for the LAMB platform.

## Test Suites

### End User Feature Tests
Complete test suite for the end_user feature (users who are automatically redirected to Open WebUI).

**Location:** `end_user_tests/`

**Quick Start:**
```bash
cd end_user_tests
./run_end_user_tests.sh
```

See [end_user_tests/README_END_USER_TESTS.md](end_user_tests/README_END_USER_TESTS.md) for detailed documentation.

### Other Tests

| Test File | Purpose |
|-----------|---------|
| `login.js` | Basic login test and session capture |
| `create_assistant.js` | Test assistant creation flow |
| `create_kb.js` | Test knowledge base creation |
| `ingest_file.js` | Test file ingestion to knowledge base |
| `query_kb.js` | Test knowledge base querying |
| `remove_kb.js` | Test knowledge base deletion |

## Installation

```bash
npm install
```

## Running Tests

### Individual Tests
```bash
node login.js http://localhost:5173
node create_assistant.js http://localhost:5173
```

### End User Test Suite
```bash
cd end_user_tests
node test_end_user_full_suite.js http://localhost:5173
```

## Requirements

- Node.js
- Playwright
- LAMB backend running (port 9099)
- LAMB frontend running (port 5173)
- Open WebUI running (port 8080)

## Test Data

Admin credentials:
- **Email:** `admin@owi.com`
- **Password:** `admin`

## Documentation

- [End User Tests](end_user_tests/README_END_USER_TESTS.md) - Complete end_user feature testing
- [Main LAMB Docs](../../Documentation/) - Full platform documentation

