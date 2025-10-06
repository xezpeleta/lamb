/**
 * Test Script: Creator vs End User Comparison
 * 
 * This script tests and compares the login behavior of creator users vs end users.
 * 
 * Test Flow:
 * 1. Login as creator user → verify access to creator interface
 * 2. Logout
 * 3. Login as end_user → verify redirect to OWI
 * 4. Compare behaviors
 * 
 * Usage: node test_creator_vs_enduser.js [base_url] [end_user_email] [end_user_password]
 * Example: node test_creator_vs_enduser.js http://localhost:5173 enduser@example.com password123
 */

const { chromium } = require('playwright');
const fs = require('fs');

const BASE_URL = process.argv[2] || 'http://localhost:5173';
const CREATOR_EMAIL = 'admin@owi.com';
const CREATOR_PASSWORD = 'admin';

let END_USER_EMAIL = process.argv[3];
let END_USER_PASSWORD = process.argv[4];

// Try to load end_user credentials from previous test
if (!END_USER_EMAIL || !END_USER_PASSWORD) {
  try {
    const resultsFile = 'test_end_user_creation_results.json';
    if (fs.existsSync(resultsFile)) {
      const results = JSON.parse(fs.readFileSync(resultsFile, 'utf8'));
      END_USER_EMAIL = results.endUser.email;
      END_USER_PASSWORD = results.endUser.password;
      console.log(`\nLoaded end_user credentials from ${resultsFile}`);
    }
  } catch (error) {
    console.error('\n❌ Error: Could not load end_user credentials');
    console.error('Run test_end_user_creation.js first or provide credentials as arguments\n');
    process.exit(1);
  }
}

(async () => {
  console.log('\n=== Starting Creator vs End User Comparison Test ===\n');
  
  const browser = await chromium.launch({ 
    headless: false, 
    slowMo: 500 
  });
  
  const results = {
    timestamp: new Date().toISOString(),
    creator: {},
    endUser: {},
    comparison: {}
  };
  
  try {
    // ===== PART 1: Test Creator User =====
    console.log('PART 1: Testing Creator User Login\n');
    console.log('=' .repeat(50));
    
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    
    console.log('Step 1.1: Navigating to login page...');
    await creatorPage.goto(BASE_URL);
    await creatorPage.waitForLoadState('networkidle');
    
    console.log('Step 1.2: Logging in as creator (admin)...');
    await creatorPage.fill('#email', CREATOR_EMAIL);
    await creatorPage.fill('#password', CREATOR_PASSWORD);
    await creatorPage.click('button[type="submit"]');
    await creatorPage.waitForLoadState('networkidle');
    await creatorPage.waitForTimeout(2000);
    
    const creatorFinalUrl = creatorPage.url();
    console.log(`  Final URL: ${creatorFinalUrl}`);
    
    // Check if creator has access to creator interface
    const hasAssistantsAccess = creatorFinalUrl.includes('/assistants') || 
                                creatorFinalUrl.includes('/admin');
    
    console.log(`  Has Creator Interface Access: ${hasAssistantsAccess ? '✅ YES' : '❌ NO'}`);
    
    // Try to navigate to admin panel
    await creatorPage.goto(`${BASE_URL}/admin`);
    await creatorPage.waitForTimeout(1000);
    const adminUrl = creatorPage.url();
    const canAccessAdmin = adminUrl.includes('/admin');
    
    console.log(`  Can Access Admin Panel: ${canAccessAdmin ? '✅ YES' : '❌ NO'}`);
    
    results.creator = {
      email: CREATOR_EMAIL,
      finalUrl: creatorFinalUrl,
      hasCreatorInterfaceAccess: hasAssistantsAccess,
      canAccessAdmin: canAccessAdmin,
      userType: 'creator'
    };
    
    console.log('\n  ✓ Creator user test completed\n');
    await creatorContext.close();
    
    // ===== PART 2: Test End User =====
    console.log('PART 2: Testing End User Login\n');
    console.log('='.repeat(50));
    
    const endUserContext = await browser.newContext();
    const endUserPage = await endUserContext.newPage();
    
    // Track redirects
    endUserPage.on('framenavigated', (frame) => {
      if (frame === endUserPage.mainFrame()) {
        console.log(`  → Navigated to: ${frame.url()}`);
      }
    });
    
    console.log('Step 2.1: Navigating to login page...');
    await endUserPage.goto(BASE_URL);
    await endUserPage.waitForLoadState('networkidle');
    
    console.log('Step 2.2: Logging in as end_user...');
    await endUserPage.fill('#email', END_USER_EMAIL);
    await endUserPage.fill('#password', END_USER_PASSWORD);
    await endUserPage.click('button[type="submit"]');
    
    console.log('Step 2.3: Waiting for automatic redirect...');
    await endUserPage.waitForTimeout(5000);
    
    const endUserFinalUrl = endUserPage.url();
    console.log(`  Final URL: ${endUserFinalUrl}`);
    
    const redirectedToOWI = endUserFinalUrl.includes('8080') || 
                           endUserFinalUrl.includes('openwebui');
    
    console.log(`  Redirected to OWI: ${redirectedToOWI ? '✅ YES' : '❌ NO'}`);
    
    // Try to access creator interface (should fail or redirect)
    let canAccessCreatorInterface = false;
    if (!redirectedToOWI) {
      await endUserPage.goto(`${BASE_URL}/assistants`);
      await endUserPage.waitForTimeout(2000);
      const assistantsUrl = endUserPage.url();
      canAccessCreatorInterface = assistantsUrl.includes('/assistants');
      console.log(`  Can Access /assistants: ${canAccessCreatorInterface ? '❌ SECURITY ISSUE!' : '✅ NO (correct)'}`);
    }
    
    results.endUser = {
      email: END_USER_EMAIL,
      finalUrl: endUserFinalUrl,
      redirectedToOWI: redirectedToOWI,
      canAccessCreatorInterface: canAccessCreatorInterface,
      userType: 'end_user'
    };
    
    console.log('\n  ✓ End user test completed\n');
    await endUserContext.close();
    
    // ===== PART 3: Comparison =====
    console.log('PART 3: Comparison\n');
    console.log('='.repeat(50));
    
    const comparisonTable = `
╔═══════════════════════════════╦═══════════════╦═══════════════╗
║ Feature                       ║ Creator User  ║ End User      ║
╠═══════════════════════════════╬═══════════════╬═══════════════╣
║ Login Successful              ║ ${results.creator.hasCreatorInterfaceAccess ? '✅ Yes       ' : '❌ No        '}║ ${results.endUser.redirectedToOWI || !results.endUser.canAccessCreatorInterface ? '✅ Yes       ' : '❌ No        '}║
║ Access Creator Interface      ║ ${results.creator.hasCreatorInterfaceAccess ? '✅ Yes       ' : '❌ No        '}║ ${results.endUser.canAccessCreatorInterface ? '❌ Yes (BAD!)' : '✅ No        '}║
║ Redirected to OWI             ║ ❌ No        ║ ${results.endUser.redirectedToOWI ? '✅ Yes       ' : '❌ No        '}║
║ Can Access Admin Panel        ║ ${results.creator.canAccessAdmin ? '✅ Yes       ' : '❌ No        '}║ N/A           ║
╚═══════════════════════════════╩═══════════════╩═══════════════╝
    `;
    
    console.log(comparisonTable);
    
    // Determine overall test status
    const creatorPassed = results.creator.hasCreatorInterfaceAccess;
    const endUserPassed = results.endUser.redirectedToOWI && !results.endUser.canAccessCreatorInterface;
    const overallPassed = creatorPassed && endUserPassed;
    
    results.comparison = {
      creatorPassed,
      endUserPassed,
      overallPassed,
      summary: overallPassed ? 
        'Both user types behave correctly' : 
        'One or more user types have issues'
    };
    
    console.log('\n=== Test Results ===\n');
    console.log(`Creator User Test: ${creatorPassed ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`End User Test: ${endUserPassed ? '✅ PASSED' : '❌ FAILED'}`);
    console.log(`Overall: ${overallPassed ? '✅ PASSED' : '❌ FAILED'}\n`);
    
    // Save results
    fs.writeFileSync(
      'test_creator_vs_enduser_results.json',
      JSON.stringify(results, null, 2)
    );
    console.log('Results saved to: test_creator_vs_enduser_results.json\n');
    
    if (!overallPassed) {
      process.exit(1);
    }
    
  } catch (error) {
    console.error('\n❌ Test Failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();

