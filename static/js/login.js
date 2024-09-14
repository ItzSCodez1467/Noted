document.addEventListener('DOMContentLoaded', async () => {
    const token = getToken();
    const isValid = await validateToken(token);

    if (isValid === false) {
        console.log('No Auth Token Found!');
    } else {
        console.log('Auth Token Found! Redirecting to Dashboard.');
        window.location = "/dash"; // Redirect after successful validation
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

document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    // Get the reCAPTCHA response
    const recaptchaResponse = grecaptcha.getResponse();
    
    if (recaptchaResponse.length === 0) {
        alert('Please complete the reCAPTCHA');
        return; // Stop form submission if reCAPTCHA is not completed
    }

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const isValid = basicValidation(username, password);

    if (!isValid) {
        return; // Stop form submission if validation fails
    }

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('g-recaptcha-response', recaptchaResponse); // Append reCAPTCHA response

    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();

        if (data.status === 201) {
            alert("Successfully Logged In!");
            setToken(data.token);
            window.location = '/dash';  // Redirect after successful login
        } else {
            alert("Login Failed: " + data.error);
        }
    } catch (error) {
        alert("Login Failed: " + error);
    }
});
