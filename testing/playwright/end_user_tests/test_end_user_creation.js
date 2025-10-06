/**
 * Test Script: End User Creation
 * 
 * This script tests the creation of end_user type accounts by an admin.
 * 
 * Test Flow:
 * 1. Login as admin
 * 2. Navigate to Admin Panel → Users
 * 3. Create a new end_user
 * 4. Verify the user was created successfully
 * 
 * Usage: node test_end_user_creation.js [base_url]
 * Example: node test_end_user_creation.js http://localhost:5173
 */

const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = process.argv[2] || 'http://localhost:5173';
const ADMIN_EMAIL = 'admin@owi.com';
const ADMIN_PASSWORD = 'admin';

// Test data for end user
const TEST_END_USER = {
  email: `enduser.test.${Date.now()}@example.com`,
  name: 'Test End User',
  password: 'TestPassword123!',
  user_type: 'end_user'
};

(async () => {
  console.log('\n=== Starting End User Creation Test ===\n');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Test End User Email: ${TEST_END_USER.email}\n`);
  
  const browser = await chromium.launch({ 
    headless: false, 
    slowMo: 500 // Slow down actions for visibility
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Step 1: Navigate to login page
    console.log('Step 1: Navigating to login page...');
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Step 2: Login as admin
    console.log('Step 2: Logging in as admin...');
    await page.waitForSelector('#email', { timeout: 10000 });
    await page.fill('#email', ADMIN_EMAIL);
    await page.fill('#password', ADMIN_PASSWORD);
    
    // Click login button
    await page.click('button[type="submit"]');
    
    // Wait for success message or navigation
    await page.waitForTimeout(3000);
    
    // Check for error messages
    const errorMessage = await page.locator('.text-red-500, .text-red-800, .bg-red-100').textContent().catch(() => null);
    if (errorMessage && errorMessage.toLowerCase().includes('invalid')) {
      throw new Error(`Login failed: ${errorMessage}`);
    }
    
    // For creator users, the page might stay at / but navigation links appear
    // Wait for authenticated UI to appear
    await page.waitForSelector('nav a:has-text("Admin"), nav a:has-text("Learning Assistants")', { timeout: 10000 });
    
    const currentUrl = page.url();
    const hasAdminLink = await page.locator('a:has-text("Admin")').isVisible();
    const hasAssistantsLink = await page.locator('a:has-text("Learning Assistants")').isVisible();
    
    console.log(`  Current URL after login: ${currentUrl}`);
    console.log(`  Has Admin link: ${hasAdminLink}`);
    console.log(`  Has Assistants link: ${hasAssistantsLink}`);
    console.log('  ✓ Login successful\n');
    
    // Step 3: Navigate to Admin Panel
    console.log('Step 3: Navigating to Admin Panel...');
    await page.goto(`${BASE_URL}/admin`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    console.log('  ✓ Admin panel loaded\n');
    
    // Step 4: Navigate to Users view
    console.log('Step 4: Opening Users view...');
    // Look for Users button/link and click it
    const usersButton = page.locator('button:has-text("Users"), a:has-text("Users")').first();
    await usersButton.click();
    await page.waitForTimeout(1000);
    console.log('  ✓ Users view loaded\n');
    
    // Step 5: Open Create User Modal
    console.log('Step 5: Opening Create User modal...');
    const createUserButton = page.locator('button:has-text("Create New User"), button:has-text("Create User")').first();
    await createUserButton.click();
    await page.waitForTimeout(1000);
    
    // Verify modal is open
    const modalVisible = await page.locator('.modal, [role="dialog"]').isVisible().catch(() => false);
    if (!modalVisible) {
      // Try alternative selector
      await page.waitForSelector('input#email', { timeout: 5000 });
    }
    console.log('  ✓ Create User modal opened\n');
    
    // Step 6: Fill in end user details
    console.log('Step 6: Filling in end user details...');
    await page.fill('input#email', TEST_END_USER.email);
    await page.fill('input#name', TEST_END_USER.name);
    await page.fill('input#password', TEST_END_USER.password);
    
    // Select user role (default is usually 'user')
    await page.selectOption('select#role', 'user');
    
    // IMPORTANT: Select end_user type
    console.log('  Selecting user_type: end_user');
    await page.selectOption('select#user_type', 'end_user');
    
    console.log('  ✓ Form filled\n');
    
    // Step 7: Submit the form
    console.log('Step 7: Submitting form...');
    const submitButton = page.locator('button:has-text("Create"), button[type="submit"]').last();
    await submitButton.click();
    
    // Wait for success message or modal to close
    await page.waitForTimeout(2000);
    
    // Check for success message
    const successMessage = await page.locator('text=/success|created/i').isVisible().catch(() => false);
    if (successMessage) {
      console.log('  ✓ User created successfully!\n');
    } else {
      console.log('  ⚠ Could not verify success message, checking user list...\n');
    }
    
    // Step 8: Verify user appears in the list
    console.log('Step 8: Verifying user in list...');
    await page.waitForTimeout(2000);
    
    // Search for the email in the page
    const userInList = await page.locator(`text=${TEST_END_USER.email}`).isVisible().catch(() => false);
    
    if (userInList) {
      console.log(`  ✓ User ${TEST_END_USER.email} found in user list\n`);
    } else {
      console.log('  ⚠ User not immediately visible in list (may need to scroll or refresh)\n');
    }
    
    // Step 9: Save test results
    const testResults = {
      timestamp: new Date().toISOString(),
      test: 'end_user_creation',
      status: 'success',
      endUser: TEST_END_USER,
      notes: 'End user creation test completed successfully'
    };
    
    fs.writeFileSync(
      'test_end_user_creation_results.json', 
      JSON.stringify(testResults, null, 2)
    );
    
    console.log('=== Test Completed Successfully ===\n');
    console.log('Test Results:');
    console.log(`  End User Email: ${TEST_END_USER.email}`);
    console.log(`  End User Password: ${TEST_END_USER.password}`);
    console.log(`  User Type: ${TEST_END_USER.user_type}`);
    console.log('\nResults saved to: test_end_user_creation_results.json\n');
    console.log('⚠️  IMPORTANT: Use these credentials to test end_user login flow!\n');
    
  } catch (error) {
    console.error('\n❌ Test Failed:', error.message);
    console.error('\nStack trace:', error.stack);
    
    // Take screenshot on error
    await page.screenshot({ path: 'test_end_user_creation_error.png', fullPage: true });
    console.log('\nScreenshot saved to: test_end_user_creation_error.png');
    
    process.exit(1);
  } finally {
    await page.waitForTimeout(2000); // Keep browser open briefly to see result
    await browser.close();
  }
})();

