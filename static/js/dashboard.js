document.addEventListener('DOMContentLoaded', async () => {
    // Validation
    const token = getToken();
    const isValid = await validateToken(token);

    if (isValid === false) {
        console.log('No Auth Token Found!');
        window.location = '/login';
    } else {
        console.log('Auth Token Found! Access allowed.');
    }

    // Get User Data
    const user_data = await getUserData(getToken());

    // Dynamic Updates
    document.getElementById('welcomeHead').innerText.replace('[USR]', user_data['username']);
});

