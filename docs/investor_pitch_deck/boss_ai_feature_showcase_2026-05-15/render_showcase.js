const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

async function main() {
  const outDir = __dirname;
  const htmlPath = path.join(outDir, "showcase.html");
  const pdfPath = path.join(
    outDir,
    "gym_leader_lab_boss_ai_feature_showcase_2026-05-15.pdf"
  );
  const previewsDir = path.join(outDir, "previews");

  fs.mkdirSync(previewsDir, { recursive: true });

  const executablePath = [
    process.env.CHROMIUM_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].find((candidate) => candidate && fs.existsSync(candidate));

  const browser = await chromium.launch({
    headless: true,
    executablePath,
  });
  const page = await browser.newPage({
    viewport: { width: 1584, height: 1224 },
    deviceScaleFactor: 1,
  });

  const fileUrl = `file:///${htmlPath.replace(/\\/g, "/")}`;
  await page.goto(fileUrl, { waitUntil: "networkidle" });

  const slideCount = await page.locator(".page").count();
  if (slideCount === 0) {
    throw new Error("No .page elements found in showcase.html");
  }

  await page.pdf({
    path: pdfPath,
    width: "11in",
    height: "8.5in",
    printBackground: true,
    preferCSSPageSize: true,
  });

  const previewPages = [0, 2, 3, 5, 7, 8].filter((index) => index < slideCount);
  for (const index of previewPages) {
    const filename = `page_${String(index + 1).padStart(2, "0")}.png`;
    await page
      .locator(".page")
      .nth(index)
      .screenshot({ path: path.join(previewsDir, filename) });
  }

  await browser.close();

  console.log(`PDF: ${pdfPath}`);
  console.log(`Slides: ${slideCount}`);
  console.log(`Previews: ${previewsDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
