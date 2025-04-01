const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const { Cluster } = require('puppeteer-cluster');

const OUTPUT_DIR = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.resolve(__dirname, '../data/pdfs/output');
const CSV_FILE = process.argv[3]
  ? path.resolve(process.argv[3])
  : path.resolve(__dirname, '../data/csv/to_download.csv');
const COOKIES_FILE = path.resolve(__dirname, '../cookies.json');

// Clean or create the output folder
if (fs.existsSync(OUTPUT_DIR)) {
  fs.readdirSync(OUTPUT_DIR).forEach(file => {
    const filePath = path.join(OUTPUT_DIR, file);
    if (fs.lstatSync(filePath).isFile()) {
      fs.unlinkSync(filePath); // Delete existing PDF files
    }
  });
  console.log(`🧹 Cleaned existing files in: ${OUTPUT_DIR}`);
} else {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  console.log(`📂 Created new output folder: ${OUTPUT_DIR}`);
}

// Read and parse CSV into a list of records
const readCSV = filePath => {
  return new Promise((resolve, reject) => {
    const results = [];
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', data => results.push(data))
      .on('end', () => resolve(results))
      .on('error', reject);
  });
};

// Load cookies from cookies.json into Puppeteer
const loadCookies = async (page, cookiesFile) => {
  const rawCookies = fs.readFileSync(cookiesFile);
  const cookies = JSON.parse(rawCookies).map(cookie => {
    // Validate sameSite value or remove it
    const validSameSite = ['Strict', 'Lax', 'None'];
    if (!validSameSite.includes(cookie.sameSite)) {
      delete cookie.sameSite;
    }
    return cookie;
  });
  await page.setCookie(...cookies);
};

const main = async () => {
  // Launch the cluster.
  // Using CONCURRENCY_CONTEXT reuses browser contexts for efficiency.
  const cluster = await Cluster.launch({
    concurrency: Cluster.CONCURRENCY_CONTEXT,
    maxConcurrency: 15, // You can increase this gradually; with 8 cores, 10–15 is a good starting point.
    puppeteerOptions: { headless: true }
  });

  // Define the task for downloading a PDF.
  await cluster.task(async ({ page, data: { url, filename } }) => {
    // Load cookies for authenticated sessions.
    await loadCookies(page, COOKIES_FILE);
    console.log(`🧪 Downloading from: ${url} as ${filename}`);

    // Navigate to the URL.
    await page.goto(url, { waitUntil: 'networkidle2' });

    // Save as PDF.
    const filePath = path.join(OUTPUT_DIR, filename);
    await page.pdf({ path: filePath, format: 'A4' });
    console.log(`✅ Downloaded: ${filename}`);
  });

  // Read CSV file
  const records = await readCSV(CSV_FILE);
  console.log(`📊 Found ${records.length} records in ${CSV_FILE}`);

  // Queue each download task.
  for (const record of records) {
    const url = record['Hyperlink']?.trim();
    const rawName = record['PDF Name']?.trim();

    if (!url || !url.startsWith('http')) {
      console.error(`⚠️ Skipping invalid URL: ${url}`);
      fs.appendFileSync('data/failed_downloads.csv', `${url},${rawName},Invalid URL\n`);
      continue;
    }
    if (!rawName || rawName.toLowerCase() === 'nan') {
      console.error(`⚠️ Skipping invalid filename: ${rawName}`);
      continue;
    }
    const filename = `${rawName}.pdf`;
    cluster.queue({ url, filename });
  }

  await cluster.idle();
  await cluster.close();
};

main().catch(console.error);
