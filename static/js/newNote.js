async function getTags() {
    try {
        const req = await fetch('/getTags', {
            method: 'POST',
            headers: getAuthHeaders(getToken())
        });

        const res = await req.json();

        if (res.status !== 200 || !res.data) {
            console.log(res);
            alert("Error Fetching Tags");
            return [];
        }

        return res.data;
    } catch (error) {
        console.log(error);
        alert("Error Fetching Tags.");
        return [];
    }
}

async function createCustomOption(data) {
    return `
    <div class="dropdown-item" 
         data-tag-idx="${data.tag_idx}" 
         style="color: ${data.tag_color || 'black'};">
        ${data.tag_name}
    </div>
    `;
}

document.addEventListener('DOMContentLoaded', async () => {
    const token = getToken();
    const isValid = await validateToken(token);

    if (isValid === false) {
        document.location = '/login.html';
        return;
    }

    const container = document.getElementById('dropdown-items');
    const searchInput = document.getElementById('search-tags');

    const data = await getTags();

    // Render all options initially
    data.forEach(async tag => {
        container.innerHTML += await createCustomOption(tag);
    });

    // Show the dropdown after loading options
    container.classList.add('show');

    // Add event listener for search functionality
    searchInput.addEventListener('input', () => {
        const filter = searchInput.value.toLowerCase();
        const items = container.getElementsByClassName('dropdown-item');

        // Filter items based on search input
        Array.from(items).forEach(item => {
            const tagName = item.textContent.toLowerCase();
            if (tagName.includes(filter)) {
                item.style.display = "";  // Show matching item
            } else {
                item.style.display = "none";  // Hide non-matching item
            }
        });
    });

    // Handle selection of a tag
    container.addEventListener('click', (event) => {
        const option = event.target.closest('.dropdown-item');
        if (option) {
            const tagIdx = option.getAttribute('data-tag-idx');
            document.getElementById('selected-tag-idx').value = tagIdx;

            // Optionally close the dropdown or highlight the selected item
            console.log(`Selected Tag IDX: ${tagIdx}`);
        }
    });
});

document.getElementById('newNoteForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formdata = new FormData();
    formdata.append('note_name', document.getElementById('name').value);
    formdata.append('note_content', document.getElementById('content').value);
    formdata.append('tag', document.getElementById('selected-tag-idx').getAttribute('value'));
    formdata.append('g-recaptcha-response', grecaptcha.getResponse());

})