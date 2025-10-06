/**
 * Test Script: End User Login and Redirect
 * 
 * This script tests that end_user type accounts are automatically redirected to Open WebUI.
 * 
 * Test Flow:
 * 1. Navigate to login page
 * 2. Login with end_user credentials
 * 3. Verify automatic redirect to Open WebUI
 * 4. Verify user does NOT have access to creator interface
 * 
 * Usage: node test_end_user_login.js [base_url] [end_user_email] [end_user_password]
 * Example: node test_end_user_login.js http://localhost:5173 enduser@example.com password123
 * 
 * Note: Run test_end_user_creation.js first to create a test end user
 */

const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = process.argv[2] || 'http://localhost:5173';
let END_USER_EMAIL = process.argv[3];
let END_USER_PASSWORD = process.argv[4];

// If credentials not provided, try to load from previous test results
if (!END_USER_EMAIL || !END_USER_PASSWORD) {
  try {
    const resultsFile = 'test_end_user_creation_results.json';
    if (fs.existsSync(resultsFile)) {
      const results = JSON.parse(fs.readFileSync(resultsFile, 'utf8'));
      END_USER_EMAIL = results.endUser.email;
      END_USER_PASSWORD = results.endUser.password;
      console.log(`\nLoaded end_user credentials from ${resultsFile}`);
    } else {
      throw new Error('No credentials provided and no results file found');
    }
  } catch (error) {
    console.error('\n❌ Error: End user credentials not provided');
    console.error('\nUsage: node test_end_user_login.js [base_url] [end_user_email] [end_user_password]');
    console.error('   OR: Run test_end_user_creation.js first to create a test user\n');
    process.exit(1);
  }
}

const OWI_BASE_URL = process.env.OWI_PUBLIC_BASE_URL || 'http://localhost:8080';

(async () => {
  console.log('\n=== Starting End User Login Test ===\n');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`End User Email: ${END_USER_EMAIL}`);
  console.log(`Expected OWI URL: ${OWI_BASE_URL}\n`);
  
  const browser = await chromium.launch({ 
    headless: false, 
    slowMo: 500 
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Track navigation for debugging
  page.on('framenavigated', (frame) => {
    if (frame === page.mainFrame()) {
      console.log(`  → Navigated to: ${frame.url()}`);
    }
  });
  
  try {
    // Step 1: Navigate to login page
    console.log('Step 1: Navigating to login page...');
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    console.log('  ✓ Login page loaded\n');
    
    // Step 2: Fill in end_user credentials
    console.log('Step 2: Entering end_user credentials...');
    await page.waitForSelector('#email', { timeout: 10000 });
    await page.fill('#email', END_USER_EMAIL);
    await page.fill('#password', END_USER_PASSWORD);
    console.log('  ✓ Credentials entered\n');
    
    // Step 3: Submit login form
    console.log('Step 3: Submitting login form...');
    const loginButton = page.locator('button[type="submit"]');
    await loginButton.click();
    
    // Step 4: Wait for redirect (important!)
    console.log('Step 4: Waiting for automatic redirect...');
    console.log('  (End users should be redirected to Open WebUI)\n');
    
    // Wait for either redirect or error message
    await Promise.race([
      page.waitForURL(new RegExp(OWI_BASE_URL), { timeout: 10000 }),
      page.waitForURL(/8080/, { timeout: 10000 }), // Also check for port 8080
      page.waitForTimeout(8000) // Give some time for redirect
    ]);
    
    await page.waitForTimeout(2000);
    
    // Step 5: Verify final URL
    const finalUrl = page.url();
    console.log('Step 5: Verifying redirect...');
    console.log(`  Final URL: ${finalUrl}\n`);
    
    // Check if redirected to OWI
    const redirectedToOWI = finalUrl.includes('8080') || finalUrl.includes('openwebui');
    
    if (redirectedToOWI) {
      console.log('  ✅ SUCCESS: User was redirected to Open WebUI!');
      console.log('  ✓ End user login working correctly\n');
    } else {
      console.log('  ⚠️  WARNING: User was NOT redirected to Open WebUI');
      console.log(`  Current URL: ${finalUrl}`);
      console.log('  Expected URL pattern: *8080* or *openwebui*\n');
      
      // Check for error messages
      const errorMessage = await page.locator('.text-red-500, .text-red-800, [class*="error"]')
        .first()
        .textContent()
        .catch(() => null);
      
      if (errorMessage) {
        console.log(`  Error message found: ${errorMessage}\n`);
      }
    }
    
    // Step 6: Verify user cannot access creator interface
    console.log('Step 6: Verifying end_user cannot access creator interface...');
    
    if (!redirectedToOWI) {
      // Try to navigate to assistants page
      await page.goto(`${BASE_URL}/assistants`);
      await page.waitForTimeout(2000);
      
      const assistantsUrl = page.url();
      if (assistantsUrl.includes('/assistants')) {
        console.log('  ❌ SECURITY ISSUE: End user can access /assistants page!');
      } else {
        console.log('  ✓ End user blocked from /assistants (redirected away)');
      }
    } else {
      console.log('  ✓ User in OWI - creator interface not accessible\n');
    }
    
    // Step 7: Save test results
    const testResults = {
      timestamp: new Date().toISOString(),
      test: 'end_user_login',
      status: redirectedToOWI ? 'success' : 'failed',
      endUserEmail: END_USER_EMAIL,
      finalUrl: finalUrl,
      redirectedToOWI: redirectedToOWI,
      expectedOWI: OWI_BASE_URL
    };
    
    fs.writeFileSync(
      'test_end_user_login_results.json', 
      JSON.stringify(testResults, null, 2)
    );
    
    console.log('=== Test Completed ===\n');
    console.log(`Status: ${redirectedToOWI ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`Results saved to: test_end_user_login_results.json\n`);
    
    if (!redirectedToOWI) {
      process.exit(1);
    }
    
  } catch (error) {
    console.error('\n❌ Test Failed:', error.message);
    console.error('\nStack trace:', error.stack);
    
    // Take screenshot on error
    await page.screenshot({ path: 'test_end_user_login_error.png', fullPage: true });
    console.log('\nScreenshot saved to: test_end_user_login_error.png');
    
    process.exit(1);
  } finally {
    await page.waitForTimeout(3000); // Keep browser open to see result
    await browser.close();
  }
})();

