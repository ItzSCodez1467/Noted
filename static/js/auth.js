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
    if (!token || !validateToken(token)) {
        alert('User not logged in. Cannot fetch user data.');
        console.log("While getting userData, token was not mentioned");
        window.location = '/login'
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

function getAuthHeaders(token, content_type='application/json') {
        if (!token || !validateToken(token)) {
            alert('User not logged in. Cannot create authorization headers.');
            console.log("While getting userData, token was not mentioned");
            window.location = '/login'
            return null;
        };

        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': content_type
        };
}