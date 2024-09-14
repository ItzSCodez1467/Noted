document.addEventListener('DOMContentLoaded', async () => {
    const token = getToken();
    const isValid = await validateToken(token);

    if (isValid === false) {
        console.log('No Auth Token Found!');
    } else {
        console.log('Auth Token Found! Redirecting to Dashboard.');
        window.location = "https://example.com/"; // Redirect after successful validation
    }
});

function basicValidation(username, password) {
    const usernamePattern = /^[A-Za-z0-9]{3,10}$/;
    const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*]).{8,12}$/;

    let isValid = true;

    if (!usernamePattern.test(username)) {
        alert('Username must be 3-10 characters long and can only contain letters and numbers.');
        isValid = false;
    }

    if (!passwordPattern.test(password)) {
        alert('Password must be 8-12 characters long, with at least one uppercase letter, one lowercase letter, and one special character.');
        isValid = false;
    }

    return isValid;
}

document.getElementById('signupForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!basicValidation(username, password)) {
        return; // Stop form submission if validation fails
    }

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.status === 201) {
            alert("Successfully Created!");
            setToken(data.token);   
            window.location = 'https://example.com';  // Redirect after successful signup
        } else {
            alert("Signup Failed: " + data.error);
        }
    } catch (error) {
        alert("Signup Failed: " + error);
    }
});
