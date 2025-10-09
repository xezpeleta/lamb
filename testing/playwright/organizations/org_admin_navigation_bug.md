# Organization Admin Navigation Link Bug - Test Documentation

## Bug Description

**Issue:** When a system administrator creates a new organization and assigns a user as the organization admin, the assigned user cannot see the "Org Admin" link in the navigation menu after logging in, even though they can access the org admin dashboard directly by navigating to `/org-admin`.

**Severity:** Medium - Functionality works but is hidden from users, causing poor user experience and discoverability issues.

**Status:** Reproduced and documented

---

## Bug Reproduction Steps (Manual)

1. **Login as System Admin**
   - Navigate to http://localhost:5173
   - Login with admin credentials (admin@owi.com / admin)

2. **Create a Standard User**
   - Go to Admin panel → User Management
   - Click "Create User"
   - Fill in: Email, Name, Password
   - Keep Role as "User" and User Type as "Creator"
   - Submit the form

3. **Create Organization with User as Org Admin**
   - Go to Admin panel → Organizations
   - Click "Create Organization"
   - Fill in: Slug (e.g., "testorg"), Name (e.g., "Test Organization")
   - In "Organization Admin" dropdown, select the newly created user
   - Submit the form

4. **Logout and Login as Org Admin**
   - Logout from admin account
   - Login with the newly created user credentials

5. **Observe the Bug**
   - ✗ **Expected:** "Org Admin" link should be visible in the navigation bar
   - ✗ **Actual:** "Org Admin" link is NOT visible in the navigation
   - ✓ **Workaround:** User can still access `/org-admin` directly, and it works correctly

---

## Automated Test

### Test File Location
```
/opt/lamb/testing/playwright/organizations/test_org_admin_navigation.js
```

### Running the Test

#### Using Playwright directly:
```bash
cd /opt/lamb/testing/playwright
npx playwright test organizations/test_org_admin_navigation.js --headed
```

#### Using Playwright with specific browser:
```bash
npx playwright test organizations/test_org_admin_navigation.js --project=chromium
```

#### Run in debug mode:
```bash
npx playwright test organizations/test_org_admin_navigation.js --debug
```

#### View test report:
```bash
npx playwright show-report
```

### Test Scenarios

The test suite includes two test cases:

1. **`org admin should see Org Admin link in navigation`**
   - Creates a new user
   - Creates a new organization with the user as org admin
   - Logs in as the org admin
   - **Verifies** the "Org Admin" link is visible (currently fails - reproduces bug)
   - **Verifies** direct navigation to `/org-admin` works (currently passes)

2. **`org admin link should be clickable and navigate correctly`**
   - Post-fix validation test
   - Verifies the link is clickable and navigates correctly
   - Will pass once the bug is fixed

---

## Expected Test Output (Current - Bug Present)

```
Step 1: Logging in as system admin...
✓ Admin logged in successfully
Step 2: Creating new user...
✓ User created: orgadmin_1234567890@test.com
Step 3: Creating organization...
✓ Organization created: testorg_1234567890
Step 4: Logging out admin...
✓ Admin logged out
Step 5: Logging in as org admin...
✓ Org admin logged in: orgadmin_1234567890@test.com
Step 6: Checking for Org Admin link in navigation...
✗ BUG CONFIRMED: Org Admin link is NOT visible in navigation
   Expected: Org admin link should be visible for org admin users
   Actual: Navigation does not show Org Admin link
Step 7: Testing direct access to /org-admin...
✓ Org admin can access /org-admin page directly
✓ Organization dashboard loaded: Test Organization 1234567890
✓ Test completed

❌ Test FAILED: Org Admin link not visible
```

---

## Expected Test Output (After Fix)

```
Step 1: Logging in as system admin...
✓ Admin logged in successfully
Step 2: Creating new user...
✓ User created: orgadmin_1234567890@test.com
Step 3: Creating organization...
✓ Organization created: testorg_1234567890
Step 4: Logging out admin...
✓ Admin logged out
Step 5: Logging in as org admin...
✓ Org admin logged in: orgadmin_1234567890@test.com
Step 6: Checking for Org Admin link in navigation...
✓ Org Admin link is visible in navigation
Step 7: Testing direct access to /org-admin...
✓ Org admin can access /org-admin page directly
✓ Organization dashboard loaded: Test Organization 1234567890
✓ Test completed

✅ All tests PASSED
```

---

## Using MCP (Model Context Protocol) to Run Test

AI agents can use the Playwright MCP to run this test:

### Prerequisites
1. Ensure LAMB containers are running: `docker-compose up -d`
2. Ensure Playwright is installed in the testing directory
3. System admin account exists (admin@owi.com)

### MCP Commands

```javascript
// Navigate to test page
await page.goto('http://localhost:5173');

// Run test steps as documented in test file
// See test_org_admin_navigation.js for detailed implementation
```

---

## Technical Context

### Affected Components

1. **Frontend Navigation Component**
   - File: `/frontend/svelte-app/src/lib/components/Nav.svelte`
   - Issue: Does not correctly detect org admin role for showing the link

2. **Backend Organization Roles**
   - Tables: `organization_roles` (LAMB DB)
   - The backend correctly assigns the "admin" role in `organization_roles` table
   - The issue is in the frontend detection logic

3. **User Session/Token**
   - JWT token contains user ID and email
   - Frontend needs to check organization roles after login

### Related Documentation

- **PRD:** `/opt/lamb/Documentation/prd.md` - Section 2.2.2 (Organization Admin persona)
- **Architecture:** `/opt/lamb/Documentation/lamb_architecture.md` - Section 8 (Organization & Multi-Tenancy)

---

## Impact

- **User Experience:** Org admins cannot discover the org admin features without manual URL entry
- **Functionality:** Backend permissions work correctly; only UI visibility is affected
- **Workaround:** Users can bookmark or manually navigate to `/org-admin`

---

## Related Issues

None currently documented. This is a newly discovered bug.

---

## Test Maintenance

- **Test Data:** Each test run creates unique users and organizations (timestamped)
- **Cleanup:** Test data is NOT automatically deleted. Use admin panel to clean up if needed.
- **Dependencies:** Requires admin account (admin@owi.com) to exist
- **Timeouts:** Tests use generous timeouts (3-10 seconds) for stability

---

## Version Information

- **LAMB Version:** 2.0
- **Test Created:** January 2025
- **Last Updated:** January 2025
- **Test Framework:** Playwright
- **Node Version:** 18+

---

## Contact

For questions about this test or bug:
- See `/testing/playwright/README.md` for general Playwright testing guidelines
- Check LAMB architecture documentation for multi-tenancy details

