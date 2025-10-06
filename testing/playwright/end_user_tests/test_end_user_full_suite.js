/**
 * Test Suite: Complete End User Feature Testing
 * 
 * This script runs a complete test suite for the end_user feature:
 * 1. Create an end_user
 * 2. Test end_user login and redirect
 * 3. Compare creator vs end_user behavior
 * 4. Clean up (optional)
 * 
 * Usage: node test_end_user_full_suite.js [base_url]
 * Example: node test_end_user_full_suite.js http://localhost:5173
 */

const { spawn } = require('child_process');
const fs = require('fs');

const BASE_URL = process.argv[2] || 'http://localhost:5173';

console.log('\n' + '='.repeat(60));
console.log('  LAMB End User Feature - Complete Test Suite');
console.log('='.repeat(60) + '\n');
console.log(`Base URL: ${BASE_URL}\n`);

// Helper function to run a test script
function runTest(scriptName, args = []) {
  return new Promise((resolve, reject) => {
    console.log(`\n${'─'.repeat(60)}`);
    console.log(`Running: ${scriptName}`);
    console.log('─'.repeat(60) + '\n');
    
    const child = spawn('node', [scriptName, ...args], {
      stdio: 'inherit',
      cwd: __dirname
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        console.log(`\n✅ ${scriptName} completed successfully\n`);
        resolve();
      } else {
        console.log(`\n❌ ${scriptName} failed with code ${code}\n`);
        reject(new Error(`${scriptName} failed`));
      }
    });
    
    child.on('error', (error) => {
      console.error(`\n❌ Error running ${scriptName}:`, error);
      reject(error);
    });
  });
}

(async () => {
  const startTime = Date.now();
  const results = {
    startTime: new Date().toISOString(),
    tests: [],
    totalTests: 3,
    passed: 0,
    failed: 0
  };
  
  try {
    // Test 1: Create End User
    console.log('\n📝 TEST 1/3: Create End User');
    try {
      await runTest('test_end_user_creation.js', [BASE_URL]);
      results.tests.push({ name: 'create_end_user', status: 'passed' });
      results.passed++;
    } catch (error) {
      results.tests.push({ name: 'create_end_user', status: 'failed', error: error.message });
      results.failed++;
      throw error; // Stop if creation fails
    }
    
    // Wait a moment
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Test 2: End User Login
    console.log('\n🔐 TEST 2/3: End User Login and Redirect');
    try {
      await runTest('test_end_user_login.js', [BASE_URL]);
      results.tests.push({ name: 'end_user_login', status: 'passed' });
      results.passed++;
    } catch (error) {
      results.tests.push({ name: 'end_user_login', status: 'failed', error: error.message });
      results.failed++;
    }
    
    // Wait a moment
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Test 3: Creator vs End User Comparison
    console.log('\n⚖️  TEST 3/3: Creator vs End User Comparison');
    try {
      await runTest('test_creator_vs_enduser.js', [BASE_URL]);
      results.tests.push({ name: 'creator_vs_enduser', status: 'passed' });
      results.passed++;
    } catch (error) {
      results.tests.push({ name: 'creator_vs_enduser', status: 'failed', error: error.message });
      results.failed++;
    }
    
  } catch (error) {
    console.error('\n❌ Test suite stopped due to critical failure');
  }
  
  // Final Results
  const endTime = Date.now();
  const duration = ((endTime - startTime) / 1000).toFixed(2);
  
  results.endTime = new Date().toISOString();
  results.durationSeconds = duration;
  results.allPassed = results.failed === 0;
  
  console.log('\n' + '='.repeat(60));
  console.log('  FINAL RESULTS');
  console.log('='.repeat(60) + '\n');
  
  console.log(`Total Tests: ${results.totalTests}`);
  console.log(`Passed: ${results.passed} ✅`);
  console.log(`Failed: ${results.failed} ❌`);
  console.log(`Duration: ${duration}s`);
  console.log('\n');
  
  // Display individual test results
  console.log('Individual Test Results:');
  results.tests.forEach((test, index) => {
    const icon = test.status === 'passed' ? '✅' : '❌';
    console.log(`  ${index + 1}. ${test.name}: ${icon} ${test.status.toUpperCase()}`);
    if (test.error) {
      console.log(`     Error: ${test.error}`);
    }
  });
  console.log('\n');
  
  // Save final results
  fs.writeFileSync(
    'test_end_user_full_suite_results.json',
    JSON.stringify(results, null, 2)
  );
  console.log('Full results saved to: test_end_user_full_suite_results.json\n');
  
  if (results.allPassed) {
    console.log('🎉 ALL TESTS PASSED! End user feature is working correctly.\n');
    process.exit(0);
  } else {
    console.log('⚠️  SOME TESTS FAILED. Please review the results above.\n');
    process.exit(1);
  }
})();

