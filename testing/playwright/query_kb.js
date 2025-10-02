const { chromium } = require('playwright');
const fs = require('fs');

const baseUrl = process.argv[2] || 'http://localhost:5173/';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error' || /CORS/i.test(msg.text())) {
      errors.push(msg.text());
    }
  });

  // Load session if available (token stored in localStorage)
  if (fs.existsSync('session_data.json')) {
    const sessionData = JSON.parse(fs.readFileSync('session_data.json', 'utf-8'));
    await page.goto(baseUrl);
    await page.evaluate((data) => {
      for (const [k,v] of Object.entries(data.localStorage)) localStorage.setItem(k, v);
      for (const [k,v] of Object.entries(data.sessionStorage)) sessionStorage.setItem(k, v);
    }, sessionData);
  }

  await page.goto(baseUrl + '/knowledgebases?view=detail&id=1');
  // Switch to Query tab (tab itself is just named 'Query')
  await page.getByRole('button', { name: /^Query$/ }).click({ timeout: 5000 });
  await page.waitForSelector('#query-text');
  // Enter the query text
  await page.fill('#query-text', '¿Cuántas becas Ikasiker se convocan?');
  // The action button text is currently 'Submit Query' (distinct from the tab). Use an exact match to avoid re-clicking the tab.
  try {
    await page.getByRole('button', { name: /^Submit Query$/ }).click({ timeout: 3000 });
  } catch (e) {
    console.warn('Explicit Submit Query button not found, attempting fallback Enter key. Error:', e.message);
    await page.keyboard.press('Enter');
  }

  // Wait for results heading OR network; prefer DOM signal
  try {
    await page.waitForSelector('h4:has-text("Query Results:")', { timeout: 5000 });
  } catch {
    console.warn('Query results heading not detected within timeout.');
  }

  // Screenshots for debugging (before and after results). Full viewport to capture more context
  // await page.screenshot({ path: 'query_kb.png', fullPage: true });
  try { await page.screenshot({ path: 'query_kb_results.png', fullPage: true }); } catch {}

  const corsErrors = errors.filter(e => /CORS|Access-Control-Allow-Origin|credentials mode/.test(e));
  if (corsErrors.length) {
    console.error('CORS errors detected:', corsErrors);
    await browser.close();
    process.exit(2);
  } else {
    console.log('No CORS errors detected during KB query.');
    await browser.close();
  }
})();
