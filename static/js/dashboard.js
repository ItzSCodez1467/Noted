// Function to fetch tag information based on tag index
async function getTagInfo(tagIdx) {
    try {
        const token = getToken();  // Retrieve token
        const response = await fetch(`/getTag/${tagIdx}`, {
            method: 'GET',
            headers: getAuthHeaders(token)  // Authorization with token
        });
        
        const result = await response.json();  // Parse the response
        
        // Check if the response contains an error
        if (response.status !== 200 || !result.data || !result.data.tag_name) {
            console.error(`Error fetching tag info: ${result.error || 'No tag data found'}`);
            return { tag_name: 'N/A', tag_color: '#000000' };  // Return default values if there's an error or missing data
        }
        
        // Access the tag information from the data object
        const tagData = result.data;
        
        return {
            tag_name: tagData.tag_name || 'N/A',
            tag_color: tagData.tag_color || '#000000'
        };  // Fallback to 'N/A' and black color if fields are missing
        
    } catch (error) {
        console.error('Error fetching tag info:', error);
        return { tag_name: 'N/A', tag_color: '#000000' };  // Default values in case of a fetch failure
    }
}


// Function to truncate text
function truncateText(text, max = 18) {
    if (text.length > max) {
        return text.substring(0, max) + '...';
    }
    return text;
}

// Function to create a note card HTML
async function createNoteCard(noteData) {
    const tagInfo = await getTagInfo(noteData.tag);  // Fetch tag details from API
    
    // Function to check if a color is dark
    function isColorDark(color) {
        // Convert hex color to RGB
        const rgb = parseInt(color.substring(1), 16);
        const r = (rgb >> 16) & 0xff;
        const g = (rgb >>  8) & 0xff;
        const b = (rgb >>  0) & 0xff;
        
        // Calculate luminance
        const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        
        // Return true if luminance is less than a threshold (adjust as needed)
        return luminance < 128;
    }

    // Determine text color based on tag color brightness
    const textColor = isColorDark(tagInfo.tag_color) ? '#FFFFFF' : '#000000';

    return `
      <div class="card" style="width: 18rem; margin-bottom: 20px;">
        <div class="card-header" style="color: ${textColor};">
          <span class="tag-circle" style="background-color: ${tagInfo.tag_color}; border-radius: 50%; display: inline-block; width: 15px; height: 15px; margin-right: 10px;"></span>
          Tagged: ${tagInfo.tag_name || 'N/A'}
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

// Function to load notes from the server
function loadNotes() {
    const token = getToken();  // Get authentication token

    fetch('/getNotes', {
        method: 'POST',
        headers: getAuthHeaders(token)  // Set authorization headers
    })
    .then(response => {
        if (response.status === 401) {
            // Handle 401 Unauthorized
            alert("Session expired or invalid. Please log in again.");
            window.location = '/login';  // Redirect to login page
            throw new Error("Unauthorized");  // Stop further processing
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

        if (data.length !== 0) {
            ncm.setAttribute('hidden', '');  // Hide no content message if there are notes
        } else {
            ncm.removeAttribute('hidden');  // Show no content message if there are no notes
        }

        // Generate HTML for each note and append to container
        data.forEach(async note => {
            const noteHtml = await createNoteCard(note);
            container.innerHTML += noteHtml;
        });
    })
    .catch(error => {
        console.error('Error fetching notes:', error);
        alert("Error Fetching Notes: " + error);
    });
}

// Event listener when DOM content is loaded
document.addEventListener('DOMContentLoaded', async () => {
    // Validate token and check user authentication
    const token = getToken();
    const isValid = await validateToken(token);

    if (isValid === false) {
        console.log('No Auth Token Found!');
        window.location = '/login';  // Redirect to login if token is invalid or missing
    } else {
        console.log('Auth Token Found! Access allowed.');
        
        // Get user data and display welcome message
        try {
            const userData = await getUserData(token);
            document.getElementById('welcomeHead').innerText = `Welcome ${userData.username}!`;
            loadNotes();  // Load notes if user authentication is valid
        } catch (error) {
            console.error('Error fetching user data:', error);
            alert("Error Fetching User Data: " + error);
        }
    }
});
