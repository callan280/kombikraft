/* Render the existing viewer's BMW speed atlas and M sweep to package textures. */
'use strict';

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const artDir = path.resolve(__dirname, '../apps/kombikraft_test/art');
const browserPath = process.env.CHROME_PATH;

async function main() {
    const browser = await chromium.launch({
        executablePath: browserPath,
        headless: true,
        args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    });
    try {
        const page = await browser.newPage();
        await page.goto(process.argv[2] || 'http://127.0.0.1:8096/design?test=1');
        await page.waitForFunction(() => typeof ready !== 'undefined' && ready && FactoryRpm.status().available && assets.speedUnit, null, { timeout: 90000 });
        const result = await page.evaluate(() => {
            window.requestAnimationFrame = () => 0;
            function surface(width, height) {
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                return canvas.getContext('2d');
            }
            function exportRgba(context, name) {
                const { width, height } = context.canvas;
                const bytes = context.getImageData(0, 0, width, height).data;
                let binary = '';
                for (let i = 0; i < bytes.length; i += 16384) {
                    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 16384));
                }
                return { name, width, height, base64: btoa(binary) };
            }
            const speed = surface(1056,108);
            for (let i = 0; i < 10; i++) number(speed, i, i * 96 + 48, 52, 78);
            factorySprite(speed, assets.speedUnit, 963, 68, 60, 28.3);
            const rpm = surface(1880,300);
            for (let i = 0; i < 11; i++) {
                if (!FactoryRpm.render(rpm, { x: (i % 4) * 470, y: Math.floor(i / 4) * 100, width: 470, height: 100 }, { normalizedRpm: i / 10 })) {
                    throw new Error('Recovered RPM artwork failed to render');
                }
            }
            return {
                entries: [exportRgba(speed, 'touring-speed.rgba'), exportRgba(rpm, 'touring-rpm.rgba')],
                rpmSource: FactoryRpm.packageSha256
            };
        });

        const manifestPath = path.join(artDir, 'manifest.json');
        const manifest = JSON.parse(fs.readFileSync(manifestPath));
        manifest.images = manifest.images.filter(row => !row.name.startsWith('touring-'));
        for (const { base64, ...entry } of result.entries) {
            const data = Buffer.from(base64, 'base64');
            entry.sha256 = crypto.createHash('sha256').update(data).digest('hex');
            fs.writeFileSync(path.join(artDir, entry.name), data);
            manifest.images.push(entry);
        }
        manifest.touringRpmSource = result.rpmSource;
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
    } finally {
        await browser.close();
    }
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
