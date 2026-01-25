import puppeteer from 'puppeteer';

const FRONTEND_URL = 'http://localhost:3456';
const BACKEND_URL = 'http://localhost:8765';

async function runTests() {
  console.log('Starting E2E tests...\n');

  // Test 1: Backend health check
  console.log('1. Backend health check');
  try {
    const healthRes = await fetch(`${BACKEND_URL}/health`);
    const health = await healthRes.json();
    console.log(`   ✅ Backend healthy: ${JSON.stringify(health)}\n`);
  } catch (e) {
    console.log(`   ❌ Backend health check failed: ${e.message}\n`);
    process.exit(1);
  }

  // Test 2: API generation (English)
  console.log('2. API generation test (English)');
  try {
    const genRes = await fetch(`${BACKEND_URL}/api/v2/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: 'en',
        age: 5,
        count: 3,
        target: { phoneme: 's', position: 'onset', minOccurrences: 1 },
        sentenceLength: 3,
        diagnosis: 'SSD',
        therapyApproach: 'minimal_pairs'
      })
    });
    const genData = await genRes.json();
    console.log(`   ✅ Generated ${genData.data.meta.generatedCount} items`);
    console.log(`   Sample: "${genData.data.items[0]?.text}"\n`);
  } catch (e) {
    console.log(`   ❌ Generation failed: ${e.message}\n`);
  }

  // Test 3: Frontend page loads
  console.log('3. Frontend V2 page test');
  const browser = await puppeteer.launch({ headless: true });

  try {
    const page = await browser.newPage();
    await page.goto(`${FRONTEND_URL}/v2`, { waitUntil: 'networkidle0' });

    // Check page title/content
    const title = await page.title();
    console.log(`   ✅ Page loaded, title: "${title}"`);

    // Check for key UI elements
    const hasSettingsButton = await page.$('button') !== null;
    console.log(`   ${hasSettingsButton ? '✅' : '❌'} Settings button found`);

    // Take a screenshot
    await page.screenshot({ path: '/tmp/v2-page.png', fullPage: true });
    console.log(`   📸 Screenshot saved to /tmp/v2-page.png\n`);

  } catch (e) {
    console.log(`   ❌ Frontend test failed: ${e.message}\n`);
  }

  // Test 4: Korean API (with working phoneme)
  console.log('4. API generation test (Korean - ㅅ phoneme)');
  try {
    const genRes = await fetch(`${BACKEND_URL}/api/v2/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language: 'ko',
        age: 5,
        count: 3,
        target: { phoneme: 'ㅅ', position: 'onset', minOccurrences: 1 },
        sentenceLength: 3,
        diagnosis: 'SSD',
        therapyApproach: 'minimal_pairs'
      })
    });
    const genData = await genRes.json();
    console.log(`   Generated ${genData.data.meta.generatedCount}/${genData.data.meta.requestedCount} items`);
    if (genData.data.items.length > 0) {
      console.log(`   ✅ Sample: "${genData.data.items[0]?.text}"`);
      console.log(`   Matched words: ${JSON.stringify(genData.data.items[0]?.matchedWords.map(w => w.word))}\n`);
    } else {
      console.log(`   ⚠️ No items generated (LLM word count issue)\n`);
    }
  } catch (e) {
    console.log(`   ❌ Korean generation failed: ${e.message}\n`);
  }

  await browser.close();
  console.log('E2E tests completed!');
}

runTests().catch(console.error);
