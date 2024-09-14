function truncateText(text, max = 18) {
    if (text.length > max) {
        return text.substring(0, max) + '...';
    }
    return text;
}

function createNote(noteData) {
    return `
      <div class="card" style="width: 18rem;">
        <div class="card-header">
          Tagged: ${noteData.tag || 'N/A'}
          Last Updated: ${noteData.readable_updated_on || 'N/A'}
        </div>
        <div class="card-body">
          <h5 class="card-title">${noteData.note_title}</h5>
          <p class="card-text">${truncateText(noteData.note_text)}</p>
          <a href="/update/${noteData.note_idx}" class="btn btn-warning">Update</a>
          <a href="/delete/${noteData.note_idx}" class="btn btn-danger">Delete</a>
        </div>
      </div>
    `;
}

function loadNotes() {
    const token = getToken();

    fetch('/getNotes', {
        method: 'POST',
        headers: getAuthHeaders(token) 
    })
    .then(response => {
        if (response.status === 401) {
            // Handle 401 Unauthorized
            alert("Session expired or invalid. Please log in again.");
            window.location = '/login';  // Redirect to login page
            return; // Stop further processing
        }

        return response.json(); // Parse JSON if not 401
    })
    .then(data => {
        // Check if data is actually returned and is an array
        if (!Array.isArray(data)) {
            console.error('Expected an array but received:', data);
            alert("Error: Unexpected response format.");
            return;
        }

        const container = document.getElementById('note-container');
        const ncm = document.getElementById('ncm');

        if (data.length != 0) {
            ncm.setAttribute('hidden', '');
        } else {
            ncm.removeAttribute('hidden');

            data.forEach(note => {
                container.innerHTML += createNote(note);
            });
        }
    })
    .catch(error => {
        console.error('Error fetching notes:', error);
        alert("Error Fetching Notes: " + error);
    });
}


document.addEventListener('DOMContentLoaded', async () => {
    // Validation
    const token = getToken();
    const isValid = await validateToken(token);

    if (isValid === false) {
        console.log('No Auth Token Found!');
        window.location = '/login';
    } else {
        console.log('Auth Token Found! Access allowed.');
        
        // Get User Data
        try {
            const user_data = await getUserData(token);
            document.getElementById('welcomeHead').innerText = 'Welcome ' + user_data['username'] + '!';
            loadNotes();
        } catch (error) {
            console.error('Error fetching user data: ' + error);
            alert("Error Fetching User Data: " + error);
        }
    }
});
