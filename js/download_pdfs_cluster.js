const fs        = require('fs');
const path      = require('path');
const csv       = require('csv-parser');
const puppeteer = require('puppeteer');
const { Cluster } = require('puppeteer-cluster');
const dotenv    = require('dotenv');

// ─── Load .env and default OUTPUT_DIR to PDF_TELE ───────────────────────────
dotenv.config({ path: path.resolve(__dirname, '../.env') });
const sharepointPdfDir = process.env.PDF_TELE;
// ───────────────────────────────────────────────────────────────────────────────

// Parse CLI args (either: [OUTPUT_DIR, CSV_FILE] or just [CSV_FILE])
const args = process.argv.slice(2).filter(a => a !== '--debug');
let [OUTPUT_DIR, CSV_FILE] = args;
if (!CSV_FILE) {
  CSV_FILE   = OUTPUT_DIR;
  OUTPUT_DIR = sharepointPdfDir;
}

// Resolve paths
OUTPUT_DIR = path.resolve(OUTPUT_DIR);
CSV_FILE   = path.resolve(CSV_FILE);

// Read & parse CSV
const readCSV = fp => new Promise((res, rej) => {
  const rows = [];
  fs.createReadStream(fp)
    .pipe(csv())
    .on('data', d => rows.push(d))
    .on('end', () => res(rows))
    .on('error', rej);
});

// Clean/create output folder
if (fs.existsSync(OUTPUT_DIR)) {
  fs.readdirSync(OUTPUT_DIR).forEach(f => {
    const p = path.join(OUTPUT_DIR, f);
    if (fs.lstatSync(p).isFile()) fs.unlinkSync(p);
  });
} else {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Launch Puppeteer‐Cluster
(async () => {
  const records = await readCSV(CSV_FILE);

  const cluster = await Cluster.launch({
    concurrency:    Cluster.CONCURRENCY_CONTEXT,
    maxConcurrency: 10,
    puppeteer,
    puppeteerOptions: {
      headless: true,
      args: ['--no-sandbox','--disable-setuid-sandbox']
    }
  });

  // Robust cookie loading + PDF download task
  await cluster.task(async ({ page, data }) => {
    const { url, filename } = data;

    // normalize cookies
    const rawCookies = JSON.parse(
      fs.readFileSync(path.resolve(__dirname, '../cookies.json'))
    );
    const cookies = rawCookies.map(c => {
      const ck = { name: c.name, value: c.value };
      if (c.url)      ck.url      = c.url;
      if (c.domain)   ck.domain   = c.domain;
      if (c.path)     ck.path     = c.path;
      if (c.expires)  ck.expires  = c.expires;
      if (typeof c.httpOnly === 'boolean') ck.httpOnly = c.httpOnly;
      if (typeof c.secure   === 'boolean') ck.secure   = c.secure;
      if (c.sameSite) ck.sameSite = c.sameSite;
      return ck;
    });
    await page.browserContext().setCookie(...cookies);

    // navigate & save PDF
    await page.goto(url, { waitUntil: 'networkidle2' });
    await page.pdf({ path: path.join(OUTPUT_DIR, filename), format: 'A4' });
    console.log(`✅ Downloaded: ${filename}`);
  });

  // enqueue
  records.forEach((rec, i) => {
    const url     = (rec.Hyperlink || '').trim();
    const rawName = (rec['PDF Name']  || '').trim();
    if (!url.startsWith('http') || !rawName) return;
    cluster.queue({ url, filename: `${rawName}.pdf` });
  });

  await cluster.idle();
  await cluster.close();
  console.log('🎉 All done.');
})();
