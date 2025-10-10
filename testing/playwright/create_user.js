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

    // Go to org-admin users page
    await page.goto(baseUrl + 'org-admin?view=users');

    // Click "Create User"
    await page.getByRole('button', { name: 'Create User' }).click();

    // Fill in user details
    await page.getByRole('textbox', { name: 'Email *' }).fill('user1@test.com');
    await page.getByRole('textbox', { name: 'Name *' }).fill('user1');
    await page.getByRole('textbox', { name: 'Password *' }).fill('pepino');
    // User Type: Creator is default, Enabled is checked by default

    // Submit the form
    await page.locator('form').getByRole('button', { name: 'Create User' }).click();

    // Wait for success alert
    await page.waitForSelector('text=User created successfully!', { timeout: 5000 });

    await browser.close();

})().catch(err => {
    console.error(err);
    process.exit(1);
});
