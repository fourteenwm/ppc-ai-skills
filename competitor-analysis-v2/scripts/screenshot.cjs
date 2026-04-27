#!/usr/bin/env node

/**
 * Competitor Screenshot Capture (Playwright version)
 *
 * Takes full-page screenshots of competitor websites.
 * Uses Playwright for better bot detection evasion.
 * Includes retry with headful mode for bot-protected sites.
 *
 * Usage:
 *   node screenshot.cjs <url1> <url2> ... --output <folder>
 *   node screenshot.cjs --urls-file <file.txt> --output <folder>
 *
 * Features:
 *   - Better bot detection evasion than Puppeteer
 *   - Full-page screenshots with lazy-load triggering
 *   - Auto-retry with headful mode if headless fails
 *   - Batch processing with metadata JSON output
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const VIEWPORT_WIDTH = 1280;
const VIEWPORT_HEIGHT = 800;
const TIMEOUT = 30000;
const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

async function captureScreenshot(browser, url, outputPath, index, options = {}) {
    const { useUserAgent = false, waitStrategy = 'networkidle' } = options;

    const contextOptions = {
        viewport: { width: VIEWPORT_WIDTH, height: VIEWPORT_HEIGHT }
    };

    if (useUserAgent) {
        contextOptions.userAgent = USER_AGENT;
    }

    const context = await browser.newContext(contextOptions);
    const page = await context.newPage();

    try {
        console.log(`[${index}] Navigating to: ${url}${options.retry ? ' (retry with evasion)' : ''}`);

        await page.goto(url, {
            waitUntil: waitStrategy,
            timeout: TIMEOUT
        });

        // Wait for any lazy-loaded content
        await page.waitForTimeout(options.retry ? 3000 : 2000);

        // Scroll down to trigger lazy loading, then back to top
        await page.evaluate(async () => {
            await new Promise(resolve => {
                let totalHeight = 0;
                const distance = 500;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if (totalHeight >= document.body.scrollHeight) {
                        clearInterval(timer);
                        window.scrollTo(0, 0);
                        resolve();
                    }
                }, 100);
            });
        });

        // Wait a bit more after scrolling
        await page.waitForTimeout(1000);

        // Generate filename from domain
        const domain = new URL(url).hostname.replace(/^www\./, '').replace(/\./g, '-');
        const filename = `${index}-${domain}.png`;
        const filepath = path.join(outputPath, filename);

        await page.screenshot({
            path: filepath,
            fullPage: true,
            type: 'png'
        });

        console.log(`[${index}] Saved: ${filepath}`);

        // Get page title for metadata
        const title = await page.title();

        await context.close();

        return {
            success: true,
            url,
            filepath,
            filename,
            title,
            index,
            retried: options.retry || false
        };

    } catch (error) {
        console.error(`[${index}] Error capturing ${url}:`, error.message);
        await context.close();

        return {
            success: false,
            url,
            error: error.message,
            index
        };
    }
}

async function main() {
    const args = process.argv.slice(2);

    // Parse arguments
    let urls = [];
    let outputFolder = '/tmp/competitor-report/screenshots';

    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--urls-file') {
            const urlsFile = args[++i];
            if (fs.existsSync(urlsFile)) {
                const content = fs.readFileSync(urlsFile, 'utf-8');
                urls = content.split('\n')
                    .map(line => line.trim())
                    .filter(line => line && line.startsWith('http'));
            } else {
                console.error(`URLs file not found: ${urlsFile}`);
                process.exit(1);
            }
        } else if (args[i] === '--output') {
            outputFolder = args[++i];
        } else if (args[i].startsWith('http')) {
            urls.push(args[i]);
        }
    }

    if (urls.length === 0) {
        console.error('Usage: node screenshot.cjs <url1> <url2> ... --output <folder>');
        console.error('   or: node screenshot.cjs --urls-file <file.txt> --output <folder>');
        console.error('\nExample:');
        console.error('  node screenshot.cjs https://client.com https://competitor1.com https://competitor2.com --output /tmp/screenshots');
        process.exit(1);
    }

    // Create output folder
    if (!fs.existsSync(outputFolder)) {
        fs.mkdirSync(outputFolder, { recursive: true });
    }

    console.log(`\nCapturing ${urls.length} screenshots...`);
    console.log(`Output folder: ${outputFolder}\n`);

    // Launch headless browser first
    let browser = await chromium.launch({ headless: true });

    // Capture screenshots sequentially
    const results = [];
    const failedUrls = [];

    for (let i = 0; i < urls.length; i++) {
        const result = await captureScreenshot(browser, urls[i], outputFolder, i + 1);
        if (result.success) {
            results.push(result);
        } else {
            failedUrls.push({ url: urls[i], index: i + 1, error: result.error });
        }
    }

    await browser.close();

    // Retry failed URLs with headful mode + user agent + domcontentloaded
    if (failedUrls.length > 0) {
        console.log(`\nRetrying ${failedUrls.length} failed URL(s) with bot evasion...`);

        browser = await chromium.launch({ headless: false });

        for (const failed of failedUrls) {
            const result = await captureScreenshot(browser, failed.url, outputFolder, failed.index, {
                useUserAgent: true,
                waitStrategy: 'domcontentloaded',
                retry: true
            });
            results.push(result);
        }

        await browser.close();
    }

    // Sort results by index
    results.sort((a, b) => a.index - b.index);

    // Summary
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`\n${'='.repeat(50)}`);
    console.log(`Screenshots captured: ${successful.length}/${urls.length}`);

    if (failed.length > 0) {
        console.log(`\nFailed URLs:`);
        failed.forEach(f => console.log(`  - ${f.url}: ${f.error}`));
    }

    // Save metadata JSON
    const output = {
        outputFolder,
        capturedAt: new Date().toISOString(),
        totalUrls: urls.length,
        successful: successful.length,
        failed: failed.length,
        screenshots: results
    };

    const jsonPath = path.join(outputFolder, 'screenshots.json');
    fs.writeFileSync(jsonPath, JSON.stringify(output, null, 2));
    console.log(`\nMetadata saved: ${jsonPath}`);

    // Print paths for easy use
    console.log('\nScreenshot files:');
    successful.forEach(s => console.log(`  ${s.filepath}`));
}

main().catch(error => {
    console.error('Fatal error:', error.message);
    process.exit(1);
});
