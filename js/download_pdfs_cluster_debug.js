// download_pdfs_cluster_debug.js

const fs        = require('fs');
const path      = require('path');
const csv       = require('csv-parser');
const puppeteer = require('puppeteer');             
const { Cluster } = require('puppeteer-cluster');

// ─── Injected: load .env and default OUTPUT_DIR to PDF_TELE ─────────────────
const dotenv = require('dotenv');
dotenv.config({ path: path.resolve(__dirname, '../.env') });
const sharepointPdfDir = process.env.PDF_TELE;
// ───────────────────────────────────────────────────────────────────────────────

// Grab args and debug flag
// Grab raw args and debug flag
const rawArgs = process.argv.slice(2);
const debug   = rawArgs.includes('--debug');

// Remove the debug flag from the usable args list
const args = rawArgs.filter(a => a !== '--debug');

// Now decide which is which:
// If only one arg remains, assume that's the CSV path and default OUTPUT_DIR
let OUTPUT_DIR, CSV_FILE;
if (args.length === 1) {
  CSV_FILE   = args[0];
  OUTPUT_DIR = process.env.PDF_TELE;              // from your .env
} else {
  [OUTPUT_DIR, CSV_FILE] = args;
}

// Resolve and report
OUTPUT_DIR = path.resolve(OUTPUT_DIR);
CSV_FILE   = path.resolve(CSV_FILE);

if (debug) {
  console.log(`🛠️  [DEBUG] OUTPUT_DIR = ${OUTPUT_DIR}`);
  console.log(`🛠️  [DEBUG] CSV_FILE   = ${CSV_FILE}`);
}


// If no OUTPUT_DIR was passed, default to the SharePoint-synced folder
if (!OUTPUT_DIR) {
  OUTPUT_DIR = sharepointPdfDir;
}

// Resolve and report
OUTPUT_DIR = path.resolve(OUTPUT_DIR);
CSV_FILE   = path.resolve(CSV_FILE);
if (debug) {
  console.log(`🛠️  [DEBUG] OUTPUT_DIR = ${OUTPUT_DIR}`);
  console.log(`🛠️  [DEBUG] CSV_FILE   = ${CSV_FILE}`);
}

// 🍥 Read & parse CSV
const readCSV = filePath => new Promise((resolve, reject) => {
  const results = [];
  fs.createReadStream(filePath)
    .pipe(csv())
    .on('data', data => results.push(data))
    .on('end', () => resolve(results))
    .on('error', reject);
});

// 🔁 Clean/create output folder
if (fs.existsSync(OUTPUT_DIR)) {
  fs.readdirSync(OUTPUT_DIR).forEach(file => {
    const filePath = path.join(OUTPUT_DIR, file);
    if (fs.lstatSync(filePath).isFile()) fs.unlinkSync(filePath);
  });
  console.log(`🧹 Cleaned existing files in: ${OUTPUT_DIR}`);
} else {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`📂 Created new output folder: ${OUTPUT_DIR}`);
}

// ─── Injected: explicit Chrome path support ───────────────────────────────────
// Prefer an override, otherwise use Puppeteer’s own Chromium binary:
const chromePath = process.env.CHROME_PATH || puppeteer.executablePath();
if (debug) console.log(`🛠️  [DEBUG] Using Chrome executable at: ${chromePath}`);
// ───────────────────────────────────────────────────────────────────────────────

(async () => {
  // 1) Read CSV
  const records = await readCSV(CSV_FILE);
  console.log(`📊 Found ${records.length} records in ${CSV_FILE}`);
  if (debug) {
    console.log("🛠️  [DEBUG] First 5 CSV rows:");
    records.slice(0,5).forEach((r,i) => {
      console.log(`   ${i+1}: URL='${r.Hyperlink}', Name='${r['PDF Name']}'`);
    });
  }

  // 2) Launch cluster with explicit puppeteer import and executablePath
  const cluster = await Cluster.launch({
    concurrency:    Cluster.CONCURRENCY_CONTEXT,
    maxConcurrency: 10,
    puppeteer,                                       
    puppeteerOptions: {
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
  });

  // 3) Define task
  await cluster.task(async ({ page, data }) => {
    const { url, filename } = data;
    if (debug) console.log(`🛠️  [DEBUG] Starting download: ${filename}`);

    try {
      // ─── Robust cookie loading ─────────────────────────────────────────────────
      const rawCookies = JSON.parse(
        fs.readFileSync(path.resolve(__dirname, '../cookies.json'))
      );
      const cookies = rawCookies.map(c => {
        const ck = { name: c.name, value: c.value };
        if (c.url)        ck.url      = c.url;
        if (c.domain)     ck.domain   = c.domain;
        if (c.path)       ck.path     = c.path;
        if (c.expires)    ck.expires  = c.expires;
        if (typeof c.httpOnly === 'boolean') ck.httpOnly = c.httpOnly;
        if (typeof c.secure   === 'boolean') ck.secure   = c.secure;
        if (c.sameSite)    ck.sameSite = c.sameSite;
        return ck;
      });
      await page.browserContext().setCookie(...cookies);
      // ──────────────────────────────────────────────────────────────────────────

      // Navigate and save PDF
      await page.goto(url, { waitUntil: 'networkidle2' });
      const filePath = path.join(OUTPUT_DIR, filename);
      await page.pdf({ path: filePath, format: 'A4' });
      console.log(`✅ Downloaded: ${filename}`);
    } catch (err) {
      console.error(`❌ Failed: ${filename}`, err.message);
      fs.appendFileSync(
        'data/failed_downloads.csv',
        `${url},${filename},${err.message}\n`
      );
    }
  });

  // 4) Queue tasks
  for (let i = 0; i < records.length; i++) {
    const rec     = records[i];
    const url     = rec.Hyperlink && rec.Hyperlink.trim();
    const rawName = rec['PDF Name'] && rec['PDF Name'].trim();
    if (!url || !url.startsWith('http')) {
      console.warn(`⚠️ Skipping invalid URL at row ${i+1}: ${url}`);
      continue;
    }
    if (!rawName || rawName.toLowerCase() === 'nan') {
      console.warn(`⚠️ Skipping invalid filename at row ${i+1}: ${rawName}`);
      continue;
    }
    const filename = `${rawName}.pdf`;
    if (debug) console.log(`🛠️  [DEBUG] Queueing [${i+1}/${records.length}]: ${filename}`);
    cluster.queue({ url, filename });
  }

  // 5) Await completion
  await cluster.idle();
  await cluster.close();
  console.log("🎉 All downloads complete.");
})().catch(err => {
  console.error("Fatal error in download script:", err);
  process.exit(1);
});
