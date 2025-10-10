const { chromium } = require('playwright');
const fs = require('fs');

const baseUrl = process.argv[2] || 'http://localhost:5173/';

(async () => {
    // Load session data for authentication
    let sessionData = null;
    if (fs.existsSync('session_data.json')) {
        sessionData = JSON.parse(fs.readFileSync('session_data.json', 'utf-8'));
    }

    const SLOW_MO = process.env.SLOW_MO ? parseInt(process.env.SLOW_MO, 10) : 500;
    const browser = await chromium.launch({ headless: false, slowMo: SLOW_MO });
    const context = await browser.newContext({ viewport: { width: 1438, height: 1148 } });
    const page = await context.newPage();
    page.setDefaultTimeout(5000);

    // Set session/localStorage if available
    if (sessionData) {
        await page.goto(baseUrl);
        await page.evaluate((data) => {
            for (const [key, value] of Object.entries(data.localStorage)) {
                localStorage.setItem(key, value);
            }
            for (const [key, value] of Object.entries(data.sessionStorage)) {
                sessionStorage.setItem(key, value);
            }
        }, sessionData);
        await page.reload();
        await page.waitForLoadState('networkidle');
    }

    // Go to organizations admin page
    await page.goto(baseUrl + 'admin?view=organizations');

    // Click "Create Organization"
    await page.getByRole('button', { name: 'Create Organization' }).click();

    // Fill in organization details
    await page.getByRole('textbox', { name: 'Slug *' }).fill('org-test-1');
    await page.getByRole('textbox', { name: 'Name *' }).fill('org test 1');
    await page.getByLabel('Organization Admin *').selectOption(['user1 (user1@test.com) - member']);
    // Disable MCP Enabled
    await page.getByRole('checkbox', { name: 'MCP Enabled' }).click();

    // Submit the form
    await page.locator('form').getByRole('button', { name: 'Create Organization' }).click();

    // Wait for success alert
    await page.waitForSelector('text=Organization created successfully!', { timeout: 5000 });

    await browser.close();

})().catch(err => {
    console.error(err);
    process.exit(1);
});
