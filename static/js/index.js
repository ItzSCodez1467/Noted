document.addEventListener('DOMContentLoaded', async () => {
    const token = getToken();
    const isValid = await validateToken(token);

    if (isValid === false) {
        console.log('No token found.');
        document.getElementById('dboard').setAttribute('hidden', '');
        document.getElementById('sup').removeAttribute('hidden');
        document.getElementById('lin').removeAttribute('hidden');
    } else {
        console.log('Token is valid.');
        document.getElementById('dboard').removeAttribute('hidden');
        document.getElementById('sup').setAttribute('hidden', '');
        document.getElementById('lin').setAttribute('hidden', '');
    }
});
