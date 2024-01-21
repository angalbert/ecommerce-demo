document.addEventListener('DOMContentLoaded', function() {
    const contentDropdown = document.getElementById('content-dropdown');
    let saveButton = document.getElementById('save-changes');

    tinymce.init({
        selector: 'textarea#editable-content',
        plugins: 'advlist autolink lists link image charmap print preview anchor',
        toolbar: 'undo redo | formatselect | bold underline italic | alignleft aligncenter alignright | bullist numlist outdent indent | link image',
        height: 400,
        setup: function(editor) {
            editor.on('init', function(e) {
              fetchContentByID("1");
              console.log("Loaded initial textbox content");
            });
          }
    });
    
    fetchDropdown();
    console.log("Loaded dropdown");

    function fetchDropdown () {fetch('/get_content_dropdown')
        .then(response => response.json())
        .then(data => {
            const content = data.content
            contentDropdown.selectedIndex = 0;
            content.forEach(item => {
                const option = document.createElement('option');
                option.value = item[0];
                option.textContent = item[1];
                contentDropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching dropdown options:', error);
        });
    }

    function fetchContentByID(selectedID) {
        fetch(`/get_content_by_id/${selectedID}`)
            .then(response => response.json())
            .then(data => {
                let content = data.content[0];
                tinymce.get('editable-content').setContent(content); // internally updates at editable-content
            })
            .catch(error => {
                console.error('Error fetching content:', error);
            });
    }
    
    // function fetchInitialContent() {
    //         fetch('/fetch_index_content')
    //         .then(response => response.json())
    //         .then(data => {
    //             const textarea = document.getElementById('editable-content');
    //             textarea.value = data.content;
    //         })
    //         .catch(error => {
    //             console.error('Error fetching content:', error);
    //         });
    //     }

    contentDropdown.addEventListener('change', function(event) {
        const selectedID = event.target.value;
        console.log("Selected ID from dropdown:", event.target.value);
        console.log("document.getElementById('editable-content').value (before fetchcontentbyid): ", document.getElementById('editable-content').value);
        fetchContentByID(selectedID);
        console.log("fetchContentByID called in Event Listener");
    });

    saveButton.addEventListener('click', function() {
        let editedContent = tinymce.get('editable-content').getContent();
        let selectedID = contentDropdown.value;
        console.log(editedContent);

        fetch('/edit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: selectedID, content: editedContent })
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Error updating content!');
        })
        .then(data => {
            alert('Content updated successfully!');
            document.getElementById('editable-content').value = editedContent;
        })
        .catch(error => {
            alert(error.message);
        });
    });
});