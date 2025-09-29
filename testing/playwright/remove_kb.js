// Script: remove_kb.js
// Purpose: Removes the knowledge base named "convocatoria_ikasiker" via the UI at /knowledgebases
// Usage: node remove_kb.js
// Prereq: Run the web app locally (frontend on :5173, backend + kb server). Ensure session_data.json exists (optional) to reuse auth.

const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const context = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
  const page = await context.newPage();
  page.setDefaultTimeout(1000);

  // Rehydrate session/localStorage if available
  if (fs.existsSync('session_data.json')) {
    try {
      const sessionData = JSON.parse(fs.readFileSync('session_data.json', 'utf-8'));
      await page.goto('http://localhost:5173/');
      await page.evaluate((data) => {
        for (const [k, v] of Object.entries(data.localStorage || {})) localStorage.setItem(k, v);
        for (const [k, v] of Object.entries(data.sessionStorage || {})) sessionStorage.setItem(k, v);
      }, sessionData);
      await page.reload();
    } catch (e) {
      console.warn('Could not restore session data:', e.message);
    }
  }

  // Navigate to Knowledge Bases list
  await page.goto('http://localhost:5173/knowledgebases');
  await page.waitForLoadState('networkidle');

  // Locate the row containing the KB name
  const kbName = 'convocatoria_ikasiker';
  const row = page.getByRole('row', { name: new RegExp(`^${kbName}\\b`, 'i') });

  const exists = await row.count();
  if (!exists) {
    console.log(`Knowledge base "${kbName}" not found (already deleted?). Exiting.`);
    await browser.close();
    return;
  }

  // Click the Delete button within that row (prepare dialog handler BEFORE clicking)
  const deleteButton = row.getByRole('button', { name: /delete/i });

  // Arm a one-time dialog handler BEFORE initiating the click.
  let dialogSeen = false;
  const dialogHandled = new Promise(resolve => {
    page.once('dialog', async (dialog) => {
      dialogSeen = true;
      try {
        console.log('Confirm dialog text:', dialog.message());
        await dialog.accept();
        console.log('Confirm dialog accepted.');
      } catch (err) {
        console.error('Error handling dialog:', err);
      } finally {
        resolve();
      }
    });
  });

  await deleteButton.click();

  // Wait up to 5s for dialog to be handled
  const dialogTimeout = 5000;
  const timed = new Promise((resolve) => setTimeout(resolve, dialogTimeout));
  await Promise.race([dialogHandled, timed]);
  if (!dialogSeen) {
    console.warn(`No confirm dialog captured within ${dialogTimeout}ms; proceeding anyway.`);
  }

  // Wait for row to disappear or success message to show
  const successLocator = page.getByText(/knowledge base deleted\.?/i);
  await Promise.race([
    row.first().waitFor({ state: 'detached', timeout: 6000 }).catch(() => {}),
    successLocator.waitFor({ state: 'visible', timeout: 6000 }).catch(() => {})
  ]);

  // Re-query to avoid stale locator state (Playwright locators are live but we want fresh assertion context)
  const refreshedRow = page.getByRole('row', { name: new RegExp(`^${kbName}\\b`, 'i') });
  const stillThere = await refreshedRow.count();
  if (stillThere === 0) {
    console.log(`Knowledge base "${kbName}" successfully removed.`);
  } else {
    console.warn(`Row for "${kbName}" still present after attempted deletion.`);
    // Capture diagnostics
    try {
      const tableText = await page.locator('table').innerText();
      console.warn('Current table text:\n', tableText);
    } catch {}
    // Try a direct DELETE via fetch in page context as fallback (will no-op if lacks auth)
    process.exitCode = 1; // mark failure for CI
  }

  // Capture a screenshot for artifacts
  await page.screenshot({ path: 'remove_kb_result.png', fullPage: true });
  console.log('Screenshot saved as remove_kb_result.png');


  await browser.close();
})();
