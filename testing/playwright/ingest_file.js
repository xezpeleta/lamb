const { chromium } = require('playwright');
const fs = require('fs');
const https = require('https');
const path = require('path');

const PDF_URL = 'https://www.euskadi.eus/web01-bopv/es/bopv2/datos/2025/09/2503764a.pdf';
const PDF_DEST = '/tmp/ikasiker.pdf';

function downloadPDF(url, dest) {
    return new Promise((resolve, reject) => {
        const file = fs.createWriteStream(dest);
        https.get(url, (response) => {
            if (response.statusCode !== 200) {
                reject(new Error(`Failed to get '${url}' (${response.statusCode})`));
                return;
            }
            response.pipe(file);
            file.on('finish', () => {
                file.close(resolve);
            });
        }).on('error', (err) => {
            fs.unlink(dest, () => reject(err));
        });
    });
}

(async () => {
    // Step 1: Download the PDF first
    if (!fs.existsSync(PDF_DEST)) {
        console.log('Downloading ikasiker.pdf...');
        try {
            await downloadPDF(PDF_URL, PDF_DEST);
            console.log('Downloaded ikasiker.pdf to /tmp.');
        } catch (err) {
            console.error('Failed to download PDF:', err);
            process.exit(1);
        }
    } else {
        console.log('ikasiker.pdf already exists in /tmp.');
    }

    const browser = await chromium.launch({ headless: false, slowMo: 1000 });
    const context = await browser.newContext({
        viewport: { width: 1438, height: 1148 },
    });
    const page = await context.newPage();
    const timeout = 5000;
    
    // Set default timeout
    page.setDefaultTimeout(timeout);

    // Load session data from session_data.json if available
    try {
        if (fs.existsSync('session_data.json')) {
            const sessionData = JSON.parse(fs.readFileSync('session_data.json', 'utf-8'));
            console.log('Loaded session data.');
            
            // Set localStorage and sessionStorage data
            await page.goto('http://localhost:5173/');
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

    // Navigate to the knowledge base detail page
    await page.goto('http://localhost:5173/knowledgebases?view=detail&id=1');

    // Click on the "Ingest Content" button/tab
    await page.getByRole('button', { name: 'Ingest Content' }).click();

    // Click the file upload input
    await page.locator('#file-upload-input-inline').click({
        position: { x: 89, y: 29 }
    });

    // Upload the file
    await page.locator('#file-upload-input-inline').setInputFiles(PDF_DEST);


    // Click and fill the description field
    await page.locator('#param-description-inline').click({
        position: { x: 403, y: 19 }
    });

    await page.locator('#param-description-inline').fill('Pliego de la convocatoria Ikasiker de becas para alumnado en formación');

    // Tab to next field
    await page.keyboard.press('Tab');

    // Fill the citation field
    await page.locator('#param-citation-inline').fill('Convocatoria Ikasiker 2025/2026');

    // Click the Upload File button
    await page.locator('div.border-t > div.px-4 button').click({
        position: { x: 53.7890625, y: 24 }
    });

    await browser.close();

})().catch(err => {
    console.error(err);
    process.exit(1);
});