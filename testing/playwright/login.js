const { chromium } = require('playwright');
const fs = require('fs');

const url = process.argv[2] || 'http://localhost:5173/';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 1000 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto(url);
    await page.waitForLoadState('networkidle');
    
    // Check if already authenticated
    let authData = await page.evaluate(() => {
      return {
        localStorage: Object.fromEntries(Object.entries(localStorage)),
        sessionStorage: Object.fromEntries(Object.entries(sessionStorage)),
        cookies: document.cookie
      };
    });
    
    console.log('Initial auth data:', JSON.stringify(authData, null, 2));
    
    // If not authenticated, perform login
    if (!authData.localStorage.userToken) {
      console.log('Not authenticated, performing login...');
      
      // Get credentials from environment variables or use defaults
      const email = process.env.LOGIN_EMAIL || 'admin@owi.com';
      const password = process.env.LOGIN_PASSWORD || 'admin';
      
      // Wait for login form to be available
      await page.waitForSelector('#email');
      await page.fill('#email', email);
      await page.fill('#password', password);
      await page.click('form > button');
      
      // Wait for navigation or successful login
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000); // Give time for localStorage to be set
      
      // Get auth data after login
      const newAuthData = await page.evaluate(() => {
        return {
          localStorage: Object.fromEntries(Object.entries(localStorage)),
          sessionStorage: Object.fromEntries(Object.entries(sessionStorage)),
          cookies: document.cookie
        };
      });
      
      console.log('Auth data after login:', JSON.stringify(newAuthData, null, 2));
      
      // Save authentication data
      fs.writeFileSync('session_data.json', JSON.stringify(newAuthData, null, 2));
    } else {
      console.log('Already authenticated');
      // Save authentication data
      fs.writeFileSync('session_data.json', JSON.stringify(authData, null, 2));
    }
    console.log('Session data saved to session_data.json');
    
  } catch (err) {
    console.error('Login failed:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
