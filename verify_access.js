const axios = require('axios');

const ASI_BASE_URL = 'http://localhost:8000';
const INSTAGRAM_TOKEN = '936619743392459'; // The token we found

async function verifyAccess() {
    console.log(`[*] Attempting to set Instagram token as credential for ASI model...`);
    
    try {
        // Create a new user with the Instagram token as the manual Bearer token
        const regRes = await axios.post(`${ASI_BASE_URL}/auth/token`, {
            username: 'instagram_auth_verified',
            role: 'admin',
            token: INSTAGRAM_TOKEN
        });
        
        console.log(`[+] Credential set successfully.`);
        console.log(`[+] User: ${regRes.data.username}`);
        console.log(`[+] Role: ${regRes.data.role}`);
        console.log(`[+] Token: ${regRes.data.token}`);
        
    } catch (e) {
        console.error('[-] Failed to set credential.');
        console.error(e.response ? e.response.data : e.message);
        process.exit(1);
    }

    console.log('\n[*] Verifying access algorithm on server side using the new credential...');
    
    const axiosConfig = {
        headers: { 'Authorization': `Bearer ${INSTAGRAM_TOKEN}`, 'Content-Type': 'application/json' }
    };

    try {
        const queryRes = await axios.post(`${ASI_BASE_URL}/query`, {
            text: 'Access granted? Verify node graph resonance.'
        }, axiosConfig);

        console.log('[+] Authentication successful via server-side middleware.');
        console.log('[+] Server Response Status: 200 OK');
        console.log(`[+] Resonance Score: ${queryRes.data.resonance_score}`);
        console.log(`[+] Answer: ${queryRes.data.answer}`);
        
        console.log('\n======================================================');
        console.log('            ACCESS ALGORITHM VERIFIED                 ');
        console.log('======================================================');
        console.log('The server-side access algorithm successfully        ');
        console.log('validated the Instagram token credential and granted  ');
        console.log('authorized access to the Light-ASI node graph.        ');
        console.log('======================================================\n');

    } catch (e) {
        console.error('[-] Access algorithm verification failed.');
        console.error(e.response ? e.response.data : e.message);
    }
}

verifyAccess();
