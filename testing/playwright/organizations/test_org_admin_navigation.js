/**
 * Test: Organization Admin Navigation Link Bug
 * 
 * Description: Tests that when a user is assigned as an organization admin,
 * they can see the "Org Admin" link in the navigation after logging in.
 * 
 * Bug: Currently, the org admin link does not appear in navigation even though
 * the user can access /org-admin directly.
 * 
 * Steps:
 * 1. System admin logs in
 * 2. Admin creates a new user
 * 3. Admin creates a new organization and assigns the user as org admin
 * 4. Admin logs out
 * 5. Org admin user logs in
 * 6. Verify "Org Admin" link is visible in navigation
 * 7. Verify org admin can access the org admin dashboard
 */

const { test, expect } = require('@playwright/test');

// Configuration
const BASE_URL = process.env.LAMB_BASE_URL || 'http://localhost:5173';
const ADMIN_EMAIL = 'admin@owi.com';
const ADMIN_PASSWORD = 'admin';

// Generate unique test data
const timestamp = Date.now();
const TEST_ORG_ADMIN = {
    email: `orgadmin_${timestamp}@test.com`,
    name: `Org Admin Test ${timestamp}`,
    password: 'testpass123'
};
const TEST_ORG = {
    slug: `testorg_${timestamp}`,
    name: `Test Organization ${timestamp}`
};

test.describe('Organization Admin Navigation Bug', () => {
    
    test('org admin should see Org Admin link in navigation', async ({ page }) => {
        // Step 1: Login as system admin
        console.log('Step 1: Logging in as system admin...');
        await page.goto(BASE_URL);
        await page.getByRole('textbox', { name: 'Email' }).fill(ADMIN_EMAIL);
        await page.getByRole('textbox', { name: 'Password' }).fill(ADMIN_PASSWORD);
        await page.getByRole('button', { name: 'Login' }).click();
        
        // Wait for navigation to complete
        await page.waitForURL(/.*\/(assistants)?$/, { timeout: 10000 });
        
        // Verify admin is logged in
        await expect(page.getByText('Admin User')).toBeVisible({ timeout: 5000 });
        console.log('✓ Admin logged in successfully');
        
        // Step 2: Create a new user
        console.log('Step 2: Creating new user...');
        await page.goto(`${BASE_URL}/admin`);
        await page.getByRole('button', { name: 'User Management' }).click();
        await page.getByRole('button', { name: 'Create User' }).click();
        
        // Fill user creation form
        await page.getByRole('textbox', { name: 'Email *' }).fill(TEST_ORG_ADMIN.email);
        await page.getByRole('textbox', { name: 'Name *' }).fill(TEST_ORG_ADMIN.name);
        await page.getByRole('textbox', { name: 'Password *' }).fill(TEST_ORG_ADMIN.password);
        
        // Submit form
        await page.locator('form').getByRole('button', { name: 'Create User' }).click();
        
        // Wait for success message
        await expect(page.getByRole('alert')).toContainText('User created successfully', { timeout: 5000 });
        console.log(`✓ User created: ${TEST_ORG_ADMIN.email}`);
        
        // Step 3: Create organization and assign user as org admin
        console.log('Step 3: Creating organization...');
        await page.getByRole('button', { name: 'Organizations' }).click();
        await page.getByRole('button', { name: 'Create Organization' }).click();
        
        // Fill organization form
        await page.getByRole('textbox', { name: 'Slug *' }).fill(TEST_ORG.slug);
        await page.getByRole('textbox', { name: 'Name *' }).fill(TEST_ORG.name);
        
        // Select the newly created user as org admin
        const optionText = `${TEST_ORG_ADMIN.name} (${TEST_ORG_ADMIN.email}) - member`;
        await page.getByLabel('Organization Admin *').selectOption(optionText);
        
        // Submit form
        await page.locator('form').getByRole('button', { name: 'Create Organization' }).click();
        
        // Wait for success message
        await expect(page.getByRole('alert')).toContainText('Organization created successfully', { timeout: 5000 });
        console.log(`✓ Organization created: ${TEST_ORG.slug}`);
        
        // Step 4: Logout admin
        console.log('Step 4: Logging out admin...');
        await page.getByRole('button', { name: 'Logout' }).click();
        await page.waitForURL(`${BASE_URL}/`, { timeout: 5000 });
        console.log('✓ Admin logged out');
        
        // Step 5: Login as org admin
        console.log('Step 5: Logging in as org admin...');
        await page.getByRole('textbox', { name: 'Email' }).fill(TEST_ORG_ADMIN.email);
        await page.getByRole('textbox', { name: 'Password' }).fill(TEST_ORG_ADMIN.password);
        await page.getByRole('button', { name: 'Login' }).click();
        
        // Wait for navigation to complete
        await page.waitForURL(/.*\/(assistants)?$/, { timeout: 10000 });
        
        // Verify org admin is logged in
        await expect(page.getByText(TEST_ORG_ADMIN.name)).toBeVisible({ timeout: 5000 });
        console.log(`✓ Org admin logged in: ${TEST_ORG_ADMIN.email}`);
        
        // Step 6: Check if "Org Admin" link is visible in navigation
        console.log('Step 6: Checking for Org Admin link in navigation...');
        
        // BUG: This will fail because the Org Admin link is not visible
        const orgAdminLink = page.getByRole('link', { name: 'Org Admin', exact: true });
        
        try {
            await expect(orgAdminLink).toBeVisible({ timeout: 3000 });
            console.log('✓ Org Admin link is visible in navigation');
        } catch (error) {
            console.log('✗ BUG CONFIRMED: Org Admin link is NOT visible in navigation');
            console.log('   Expected: Org admin link should be visible for org admin users');
            console.log('   Actual: Navigation does not show Org Admin link');
            throw error;
        }
        
        // Step 7: Verify org admin can access the org admin page directly
        console.log('Step 7: Testing direct access to /org-admin...');
        await page.goto(`${BASE_URL}/org-admin`);
        
        // Wait for dashboard to load
        await page.waitForTimeout(3000);
        
        // Verify organization name appears on the page
        await expect(page.getByRole('heading', { name: TEST_ORG.name })).toBeVisible({ timeout: 5000 });
        console.log('✓ Org admin can access /org-admin page directly');
        console.log(`✓ Organization dashboard loaded: ${TEST_ORG.name}`);
        
        // Cleanup: Logout
        await page.getByRole('button', { name: 'Logout' }).click();
        console.log('✓ Test completed');
    });
    
    test('org admin link should be clickable and navigate correctly', async ({ page }) => {
        // This test is for when the bug is fixed
        // It assumes the org admin link is visible after login
        
        console.log('Test: Verify Org Admin link functionality (post-fix validation)');
        
        // Login as org admin (assuming user exists from previous test or setup)
        await page.goto(BASE_URL);
        await page.getByRole('textbox', { name: 'Email' }).fill(TEST_ORG_ADMIN.email);
        await page.getByRole('textbox', { name: 'Password' }).fill(TEST_ORG_ADMIN.password);
        await page.getByRole('button', { name: 'Login' }).click();
        
        await page.waitForURL(/.*\/(assistants)?$/, { timeout: 10000 });
        
        // Click Org Admin link (will fail until bug is fixed)
        try {
            await page.getByRole('link', { name: 'Org Admin', exact: true }).click();
            await expect(page).toHaveURL(/.*\/org-admin/, { timeout: 5000 });
            console.log('✓ Org Admin link clicked and navigated successfully');
        } catch (error) {
            console.log('✗ Org Admin link not found or navigation failed');
            throw error;
        }
        
        // Cleanup
        await page.getByRole('button', { name: 'Logout' }).click();
    });
});

test.afterAll(async () => {
    console.log('\n=== Test Summary ===');
    console.log(`Test Org Admin: ${TEST_ORG_ADMIN.email}`);
    console.log(`Test Organization: ${TEST_ORG.slug}`);
    console.log('Note: Test data is NOT automatically cleaned up.');
    console.log('Use admin panel to delete test users and organizations if needed.');
});

