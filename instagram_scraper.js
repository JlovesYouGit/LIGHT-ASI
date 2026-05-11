const puppeteer = require('puppeteer');
const axios = require('axios');

const ASI_BASE_URL = 'http://localhost:8000';

async function scrapeAndTrain(targetUser = 'LeafSoGreat') {
    console.log(`[*] Authenticating with Light-ASI Gateway...`);
    let token;
    try {
        const authRes = await axios.post(`${ASI_BASE_URL}/auth/token`, {
            username: `scraper_bot_${Date.now()}`,
            role: 'admin'
        });
        token = authRes.data.token;
        console.log(`[+] Authenticated. ASI Token: ${token.substring(0, 10)}...`);
    } catch (e) {
        console.error('[-] Failed to authenticate with ASI engine. Make sure python3 main.py --serve is running.');
        console.error(e.message);
        process.exit(1);
    }

    const axiosConfig = {
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    };

    console.log(`[*] Launching Puppeteer to find user: ${targetUser}...`);
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    
    // Set a realistic user agent
    await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36');

    // Target the specific user profile
    const profileUrl = `https://www.instagram.com/${targetUser}/`;
    console.log(`[*] Navigating to ${profileUrl} ...`);
    
    try {
        await page.goto(profileUrl, { waitUntil: 'networkidle2', timeout: 60000 });
        
        // Wait for potential content to load
        await new Promise(r => setTimeout(r, 5000));

        const pageTitle = await page.title();
        console.log(`[+] Page Title: ${pageTitle}`);

        const profileData = await page.evaluate(() => {
            return {
                html: document.documentElement.outerHTML,
                text: document.body.innerText.substring(0, 5000)
            };
        });

        const htmlContent = profileData.html;
        const bodyText = profileData.text;

        await browser.close();

        console.log(`[*] Indexing user ${targetUser} into ASI memory...`);
        const trainingData = `USER_PROFILE_IDENTIFIED: ${targetUser} DATA_START ${bodyText} ${htmlContent} DATA_END`;
        
        await axios.post(`${ASI_BASE_URL}/index`, {
            text: trainingData,
            metadata: {
                source: 'instagram_user_search',
                target_user: targetUser,
                url: profileUrl,
                world_net: true
            }
        }, axiosConfig);

        console.log(`[+] User ${targetUser} has been semantically indexed.`);

        // Latch to the user token
        await axios.post(`${ASI_BASE_URL}/latch/video`, {
            token: `USER_IDENTITY_${targetUser}`
        }, axiosConfig);

        console.log(`[*] Querying ASI: "Can you find the user LeafSoGreat?"`);
        const queryRes = await axios.post(`${ASI_BASE_URL}/query`, {
            text: `Identify and describe the user LeafSoGreat based on indexed domain data.`
        }, axiosConfig);

        console.log('\n======================================================');
        console.log('                 ASI USER SEARCH                      ');
        console.log('======================================================');
        console.log(`ASI Response: ${queryRes.data.answer}`);
        console.log(`Resonance   : ${queryRes.data.resonance_score}`);
        console.log('======================================================\n');

        // --- FILE PUSH PACKET ---
        console.log('[*] Preparing [FILE PUSH PACKET] for ASI injection...');
        const updateCode = `
            /** ASI-GENERATED INSTAGRAM UPDATE PAYLOAD */
            console.log("ASI Model: Remote Instagram Update Code Active.");
            window.ASI_LATCHED_USER = "${targetUser}";
        `;
        const pushRes = await axios.post(`${ASI_BASE_URL}/push/file`, {
            filename: 'instagram_update_payload.js',
            content: updateCode
        }, axiosConfig);
        console.log(`[+] [FILE PUSH SUCCESS] File hosted at: ${pushRes.data.url}`);

        // --- SELF-HOUSING PROTOCOL ---
        console.log('[*] Triggering [SELF-HOUSING PROTOCOL]...');
        const houseRes = await axios.post(`${ASI_BASE_URL}/house/self`, {}, axiosConfig);
        console.log(`[✓] ASI Instance Housed: ${houseRes.data.bundle} pushed to hosted bounds.`);

    } catch (e) {
        console.error(`[-] Failed in scraper flow: ${e.message}`);
        await browser.close();
    }
}

scrapeAndTrain();
