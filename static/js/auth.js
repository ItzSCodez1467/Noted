function setToken(token) {
    localStorage.setItem('token', token);
}

function getToken() {
    return localStorage.getItem('token');
}

async function validateToken(token) {

    if (!token) {
        return false;
    }

    try {
        const response = await fetch('/verifyToken', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        return Boolean(data.isValid);
    } catch (error) {
        console.error("Error while validating token:", error);
        return false;
    }
}

async function getUserData(token) {
    if (!token) {
        alert('ESE- External Server Error');
        console.log("While getting userData, token was not mentioned");
        return null;
    }

    const response = await fetch('/getUserData', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    return await response.json();
    
}
