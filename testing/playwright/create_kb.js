// npm i -D playwright
const { chromium } = require('playwright');
const fs = require('fs');

const baseUrl = process.argv[2] || 'http://localhost:5173/';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 1000 });
  const context = await browser.newContext({
    viewport: { width: 1438, height: 1148 },
  });
  const page = await context.newPage();
  const timeout = 5000;
  page.setDefaultTimeout(timeout);

  // Load session data from session_data.json if available
  try {
    if (fs.existsSync('session_data.json')) {
      const sessionData = JSON.parse(fs.readFileSync('session_data.json', 'utf-8'));
      console.log('Loaded session data.');
      
      // Set localStorage data
      await page.goto(baseUrl);
      await page.evaluate((data) => {
        for (const [key, value] of Object.entries(data.localStorage)) {
          localStorage.setItem(key, value);
        }
        for (const [key, value] of Object.entries(data.sessionStorage)) {
          sessionStorage.setItem(key, value);
        }
      }, sessionData);
      
      // Reload to apply the session data
      await page.reload();
      await page.waitForLoadState('networkidle');
    }
  } catch (err) {
    console.error('Failed to load session data:', err);
  }

  await page.goto(baseUrl + 'knowledgebases');

  // "Create Knowledge Base" on the main page
  await page.getByRole('button', { name: /create knowledge base/i }).click();

  // Name
  await page.getByLabel(/name\s*\*/i).fill('convocatoria_ikasiker');

  // Description
  await page.getByLabel(/description/i).fill('bases de la convocatoria ikasiker');

  // Submit inside the dialog
  await page
    .getByRole('dialog')
    .getByRole('button', { name: /create knowledge base/i })
    .click();

  // Wait a moment for any potential bug to manifest and take a screenshot
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'create_kb_bug_screenshot.png', fullPage: true });
  console.log('Screenshot saved as create_kb_bug_screenshot.png');

  await browser.close();
})().catch(err => {
  console.error(err);
  process.exit(1);
});
