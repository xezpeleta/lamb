# End User Feature - Playwright Tests

Comprehensive test suite for the LAMB end_user feature.

## Overview

These tests verify that:
1. Admins can create end_user type accounts
2. End users are automatically redirected to Open WebUI upon login
3. End users cannot access the creator interface
4. Creator users maintain normal access to creator interface

## Test Files

| Test File | Purpose | Run Order |
|-----------|---------|-----------|
| `test_end_user_creation.js` | Creates a test end_user via admin panel | 1st |
| `test_end_user_login.js` | Tests end_user login and redirect to OWI | 2nd |
| `test_creator_vs_enduser.js` | Compares creator vs end_user behavior | 3rd |
| `test_end_user_full_suite.js` | Runs all tests in sequence | All-in-one |

## Prerequisites

1. **LAMB Backend Running:** Port 9099
2. **LAMB Frontend Running:** Port 5173 (or your configured port)
3. **Open WebUI Running:** Port 8080 (or your configured port)
4. **Node.js and Playwright Installed:**
   ```bash
   cd /opt/lamb/testing/playwright
   npm install  # Install in parent directory
   ```

## Quick Start

### Run Complete Test Suite

```bash
cd /opt/lamb/testing/playwright/end_user_tests
node test_end_user_full_suite.js http://localhost:5173
```

This will:
- Create a test end_user
- Test end_user login and redirect
- Compare creator vs end_user behavior
- Generate comprehensive test results

### Run Individual Tests

Make sure you're in the test directory:
```bash
cd /opt/lamb/testing/playwright/end_user_tests
```

#### 1. Create End User
```bash
node test_end_user_creation.js http://localhost:5173
```

This creates a test end_user with credentials saved to `test_end_user_creation_results.json`.

#### 2. Test End User Login
```bash
# Using saved credentials from previous test
node test_end_user_login.js http://localhost:5173

# Or with explicit credentials
node test_end_user_login.js http://localhost:5173 enduser@example.com password123
```

#### 3. Compare Creator vs End User
```bash
# Using saved credentials
node test_creator_vs_enduser.js http://localhost:5173

# Or with explicit credentials
node test_creator_vs_enduser.js http://localhost:5173 enduser@example.com password123
```

## Test Credentials

### Admin (Creator User)
- **Email:** `admin@owi.com`
- **Password:** `admin`

### Test End User
Created automatically by `test_end_user_creation.js`. Credentials saved in:
- `test_end_user_creation_results.json`

Format:
```json
{
  "endUser": {
    "email": "enduser.test.1234567890@example.com",
    "password": "TestPassword123!"
  }
}
```

## Expected Behavior

### Creator User Login Flow
1. Enter credentials
2. Click login
3. **→ Redirected to `/assistants`** (creator interface)
4. Has access to all creator features

### End User Login Flow
1. Enter credentials
2. Click login
3. **→ Automatically redirected to Open WebUI** (port 8080)
4. Cannot access creator interface
5. Can only interact with published assistants

## Test Results

Each test generates a JSON results file:

- `test_end_user_creation_results.json` - Created end_user details
- `test_end_user_login_results.json` - Login test results
- `test_creator_vs_enduser_results.json` - Comparison test results
- `test_end_user_full_suite_results.json` - Complete suite results

## Understanding Test Output

### Success Indicators
- ✅ Green checkmarks indicate passed tests
- Proper redirects for each user type
- No access to creator interface for end users

### Failure Indicators
- ❌ Red X marks indicate failed tests
- Screenshots saved as `*_error.png`
- Detailed error messages in console

## Common Issues

### 1. Connection Refused
**Error:** `net::ERR_CONNECTION_REFUSED`
**Solution:** Ensure all services are running:
```bash
# Check backend
curl http://localhost:9099/status

# Check frontend
curl http://localhost:5173

# Check Open WebUI
curl http://localhost:8080
```

### 2. End User Not Redirected
**Possible Causes:**
- `user_type` not set to `'end_user'` in database
- Frontend not detecting `user_type` correctly
- `launch_url` missing in login response

**Debug:**
```sql
-- Check user_type in database
SELECT user_email, user_type FROM Creator_users WHERE user_email = 'enduser@example.com';
```

### 3. End User Can Access Creator Interface
**This is a security issue!** Check:
- Frontend login logic in `Login.svelte`
- Backend login response includes `user_type`
- User type is correctly set in database

## Manual Testing

### Test End User Creation (Manual)
1. Login as admin (`admin@owi.com` / `admin`)
2. Navigate to Admin Panel → Users
3. Click "Create New User"
4. Fill in details:
   - Email: `manual.enduser@example.com`
   - Name: Manual End User
   - Password: `SecurePass123`
   - Role: User
   - **User Type: End User (Redirects to Open WebUI)**
5. Click Create
6. Verify user appears in list

### Test End User Login (Manual)
1. Logout from admin account
2. Navigate to login page
3. Login with end user credentials
4. **Verify:** Automatically redirected to Open WebUI (port 8080)
5. **Verify:** Cannot access `http://localhost:5173/assistants`

## Cleanup

To remove test users:
1. Login as admin
2. Navigate to Admin Panel → Users
3. Find test users (email starts with `enduser.test.*`)
4. Delete test users

Or via database:
```sql
DELETE FROM Creator_users WHERE user_email LIKE 'enduser.test.%';
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Run End User Tests
  run: |
    cd testing/playwright
    npm install
    cd end_user_tests
    node test_end_user_full_suite.js http://localhost:5173
```

## Troubleshooting

### Enable Verbose Logging
Add `DEBUG=pw:api` before node command:
```bash
DEBUG=pw:api node test_end_user_creation.js
```

### Run in Headed Mode
Tests run in headed mode (headless: false) by default for visibility.
To run headless, edit the test file:
```javascript
const browser = await chromium.launch({ 
  headless: true,  // Change to true
  slowMo: 0        // Remove delay
});
```

### Check Browser Console
In test scripts, add:
```javascript
page.on('console', msg => console.log('Browser:', msg.text()));
```

## Support

For issues or questions:
1. Check test output and error screenshots
2. Review backend logs
3. Verify database schema migration completed
4. Consult main LAMB documentation

## Related Documentation

- `/opt/lamb/Documentation/end_user_feature.md` - Feature documentation
- `/opt/lamb/Documentation/prd.md` - Product requirements
- `/opt/lamb/Documentation/lamb_architecture.md` - Technical architecture

