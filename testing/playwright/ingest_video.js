// Playwright script to ingest a YouTube video via the new ingestion plugin
// Assumptions (adjust selectors/names to match actual UI):
// 1. There is an "Ingest Content" button (same as file ingestion flow).
// 2. A plugin/button/tab for YouTube ingestion is labeled something like: "YouTube", "YouTube Video", or "Video URL".
// 3. There is an input for the video URL with an id such as #param-url-inline OR a data-testid OR placeholder containing "YouTube" or "Video URL".
// 4. There are optional inputs for description (#param-description-inline), citation (#param-citation-inline), and language (#param-language-inline).
// 5. The submit button lives in the same container pattern used in ingest_file.js (div.border-t > div.px-4 button) OR has accessible name like "Upload", "Ingest", or "Start".
// 6. A success indicator appears containing text like: "Ingestion started", "Ingest job created", or "Success".
//
// If any selector fails, the script will log a warning and attempt alternative strategies before exiting with error.
// Edit KNOWN_KB_ID or pass KB_ID env var if needed.

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configurable constants
const VIDEO_URL = process.env.VIDEO_URL || 'https://www.youtube.com/watch?v=cwHmVpLOqas';
const VIDEO_LANG = process.env.VIDEO_LANG || 'es';
const KNOWN_KB_ID = process.env.KB_ID || '1';
const HEADLESS = (process.env.HEADLESS || 'false').toLowerCase() === 'true';
const SLOW_MO = process.env.SLOW_MO ? parseInt(process.env.SLOW_MO, 10) : 500; // slower to observe steps
const BASE_URL = process.argv[2] || 'http://localhost:5173';

(async () => {
  const browser = await chromium.launch({ headless: HEADLESS, slowMo: SLOW_MO });
  const context = await browser.newContext({ viewport: { width: 1438, height: 1148 } });
  const page = await context.newPage();
  page.setDefaultTimeout(7000);

  // Utility: log helper
  const log = (...args) => console.log('[ingest_video]', ...args);

  // Load session data (re-use from existing auth/session capture)
  try {
    if (fs.existsSync('session_data.json')) {
      log('Loading session_data.json ...');
      const sessionData = JSON.parse(fs.readFileSync('session_data.json', 'utf-8'));
      await page.goto(BASE_URL + '/');
      await page.evaluate((data) => {
        for (const [k, v] of Object.entries(data.localStorage || {})) localStorage.setItem(k, v);
        for (const [k, v] of Object.entries(data.sessionStorage || {})) sessionStorage.setItem(k, v);
      }, sessionData);
      await page.reload();
      await page.waitForLoadState('networkidle');
      log('Session data applied.');
    } else {
      log('No session_data.json found; proceeding unauthenticated (may fail if auth required).');
    }
  } catch (e) {
    console.warn('Failed applying session data:', e);
  }

  // Navigate directly to the knowledge base detail + ingest view
  const kbUrl = `${BASE_URL}/knowledgebases?view=detail&id=${KNOWN_KB_ID}`;
  log('Navigating to KB detail:', kbUrl);
  await page.goto(kbUrl);
  await page.waitForLoadState('networkidle');

  // Open the ingest content area
  try {
    await page.getByRole('button', { name: /Ingest Content/i }).click();
    log('Opened Ingest Content pane.');
  } catch (e) {
    console.error('Could not find Ingest Content button.');
    throw e;
  }

  // --- Updated flow for youtube_transcript_ingest plugin ---
  // The UI uses a select (combobox) labeled "Ingestion Plugin". We choose the youtube option.
  async function selectYoutubePlugin() {
    log('Selecting youtube_transcript_ingest plugin via <select>');
    const pluginSelect = page.getByLabel('Ingestion Plugin');
    await pluginSelect.waitFor({ state: 'visible' });
    // Try to locate option containing youtube_transcript_ingest
    const optionLocator = pluginSelect.locator('option', { hasText: /youtube_transcript_ingest/i });
    const count = await optionLocator.count();
    if (count === 0) {
      throw new Error('youtube_transcript_ingest option not found in plugin select');
    }
    // Retrieve value attribute for stable selectOption usage
    const valueAttr = await optionLocator.first().getAttribute('value');
    if (valueAttr) {
      await pluginSelect.selectOption(valueAttr);
    } else {
      // fallback: click option directly (rarely needed)
      await pluginSelect.click();
      await optionLocator.first().click();
    }
    // Wait for layout to switch (heading or parameter field present)
    await Promise.race([
      page.getByRole('heading', { name: /Configure and Run Ingestion/i }).waitFor({ timeout: 3000 }).catch(()=>{}),
      page.getByRole('textbox', { name: /^video_url /i }).waitFor({ timeout: 3000 }).catch(()=>{}),
    ]);
    log('youtube_transcript_ingest plugin selected.');
  }

  await selectYoutubePlugin();

  // Fill required parameters using accessible names exactly as observed.
  const videoUrlInput = page.getByRole('textbox', { name: /^video_url /i });
  await videoUrlInput.waitFor();
  await videoUrlInput.fill(VIDEO_URL);
  log('Filled video_url');

  const languageInput = page.getByRole('textbox', { name: /^language /i });
  try {
    await languageInput.waitFor({ timeout: 1500 });
    await languageInput.fill(VIDEO_LANG);
    log('Set language to', VIDEO_LANG);
  } catch (e) {
    log('Language input not found or fill skipped:', e.message);
  }

  // Optional: allow overriding chunk duration via env
  if (process.env.CHUNK_DURATION) {
    const chunkSpin = page.getByRole('spinbutton', { name: /^chunk_duration /i });
    try {
      await chunkSpin.waitFor({ timeout: 1500 });
      await chunkSpin.fill(String(process.env.CHUNK_DURATION));
      log('Set chunk_duration to', process.env.CHUNK_DURATION);
    } catch (_) {
      log('Could not set chunk_duration (not found).');
    }
  }

  if (process.env.PROXY_URL) {
    const proxyInput = page.getByRole('textbox', { name: /^proxy_url /i });
    try {
      await proxyInput.waitFor({ timeout: 1500 });
      await proxyInput.fill(process.env.PROXY_URL);
      log('Set proxy_url');
    } catch (_) {
      log('Could not set proxy_url (not found).');
    }
  }

  // Run ingestion
  const runButton = page.getByRole('button', { name: /Run Ingestion/i });
  await runButton.waitFor({ state: 'visible' });
  await runButton.click();
  log('Clicked Run Ingestion');

  // Wait for success message specific to this flow
  const successTextPattern = /File uploaded and ingestion started successfully!/i;
  try {
    await page.getByText(successTextPattern).waitFor({ timeout: 8000 });
    log('Success message detected.');
  } catch (e) {
    console.warn('Success message not detected within timeout. Check server logs.');
  }

  log('YouTube ingestion script finished.');
  await browser.close();
})().catch(err => {
  console.error('[ingest_video] Error:', err);
  process.exit(1);
});
