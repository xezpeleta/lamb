# Organization Tests

This directory contains Playwright tests and documentation for organization-related functionality in LAMB.

## Contents

### Test Files

1. **`test_org_admin_navigation.js`**
   - Tests organization admin navigation link visibility
   - Reproduces bug where org admin link is missing from navigation
   - Validates that org admins can access the org admin dashboard

### Documentation

2. **`org_admin_navigation_bug.md`**
   - Complete documentation of the org admin navigation bug
   - Manual and automated reproduction steps
   - Expected vs actual behavior
   - Test execution instructions

3. **`BUG_FIX_PLAN.md`**
   - Comprehensive fix plan for the org admin navigation bug
   - Root cause analysis
   - Implementation plan with code examples
   - Testing strategy
   - Rollout plan

## Quick Start

### Running Tests

```bash
# From the playwright directory
cd /opt/lamb/testing/playwright

# Run the org admin navigation test
npx playwright test organizations/test_org_admin_navigation.js

# Run in headed mode (see the browser)
npx playwright test organizations/test_org_admin_navigation.js --headed

# Run in debug mode
npx playwright test organizations/test_org_admin_navigation.js --debug
```

### Prerequisites

1. LAMB containers must be running:
   ```bash
   cd /opt/lamb
   docker-compose up -d
   ```

2. System admin account must exist (default: admin@owi.com)

3. Playwright must be installed:
   ```bash
   cd /opt/lamb/testing/playwright
   npm install
   npx playwright install
   ```

## Current Status

### Known Issues

**Issue:** Organization Admin Navigation Link Missing (ORG-ADMIN-NAV-001)
- **Status:** Reproduced and documented
- **Severity:** Medium
- **Impact:** Org admins cannot see navigation link (but can access page directly)
- **Fix Plan:** Available in `BUG_FIX_PLAN.md`

### Test Results

**Current State (Bug Present):**
- ❌ `test_org_admin_navigation.js` - FAILING (expected)
  - Step 6 fails: Org Admin link not visible in navigation
  - Step 7 passes: Direct access to `/org-admin` works

**Expected After Fix:**
- ✅ All tests should pass
- ✅ Org admin link visible and clickable

## Bug Summary

### The Problem

When a system administrator:
1. Creates a new user
2. Creates a new organization
3. Assigns the user as organization admin

The assigned user cannot see the "Org Admin" link in the navigation menu after logging in.

### Root Cause

The backend correctly stores the organization role in the `organization_roles` table, but the login endpoint doesn't retrieve and return this data to the frontend. The frontend navigation component checks for `$user.data?.organization_role`, which is always `undefined`.

### The Fix

Add organization role to the login response by:
1. Fetching user's organization role from the database during login
2. Including it in the login response
3. Frontend will automatically use the new field (already implemented correctly)

**See `BUG_FIX_PLAN.md` for detailed implementation instructions.**

## Test Data Management

### Automated Test Data

The test creates unique data for each run:
- Email: `orgadmin_{timestamp}@test.com`
- Organization slug: `testorg_{timestamp}`

**Note:** Test data is NOT automatically cleaned up. Use the admin panel to delete test users and organizations if needed.

### Manual Cleanup

If you need to clean up test data:

1. Login as system admin
2. Go to Admin → Organizations
3. Delete test organizations (slug starts with `testorg_`)
4. Go to Admin → User Management  
5. Delete test users (email starts with `orgadmin_`)

## Architecture Context

### Related Components

- **Frontend:** `/frontend/svelte-app/src/lib/components/Nav.svelte`
- **Backend Login:** `/backend/creator_interface/main.py` (login endpoint)
- **User Creator:** `/backend/creator_interface/user_creator.py`
- **Database:** `/backend/lamb/database_manager.py`
- **Tables:** `organization_roles`, `Creator_users`, `organizations`

### Data Flow

```
User Login
    ↓
Creator Interface (/creator/login)
    ↓
UserCreatorManager.verify_user()
    ↓
[BUG: Should fetch organization_role here]
    ↓
Return login response
    ↓
Frontend userStore
    ↓
Nav.svelte checks $user.data.organization_role
    ↓
[BUG: Field is undefined, link not shown]
```

## Related Documentation

- **PRD:** `/opt/lamb/Documentation/prd.md`
  - Section 2.2.2: Organization Admin persona
  - Section 3.2: Organization Management

- **Architecture:** `/opt/lamb/Documentation/lamb_architecture.md`
  - Section 6: Authentication & Authorization
  - Section 8: Organization & Multi-Tenancy

- **Testing:** `/opt/lamb/testing/playwright/README.md`
  - General Playwright testing guidelines

## Contributing

When adding new organization tests:

1. Follow the existing test structure
2. Use timestamped test data for uniqueness
3. Document the test purpose clearly
4. Update this README with the new test

## Support

For questions or issues:
- Check the bug documentation in this directory
- Review the architecture documentation
- Check existing GitHub issues
- Create a new issue with test results

---

**Last Updated:** January 2025  
**Test Framework:** Playwright  
**LAMB Version:** 2.0

