// Container management JS

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('container-modal');
    const addContainerBtn = document.getElementById('add-container');
    const closeBtn = modal.querySelector('.close');
    const form = document.getElementById('container-form');
    
    // Open modal when "Add Container" button is clicked
    if (addContainerBtn) {
        addContainerBtn.addEventListener('click', function() {
            // Clear form for new container
            form.reset();
            document.getElementById('modal-title').textContent = 'Add Container';
            modal.style.display = 'block';
        });
    }
    
    // Close modal when X button is clicked
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside the content
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Handle edit container buttons
    const editButtons = document.querySelectorAll('.edit-container');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const name = this.getAttribute('data-name');
            // In a real app, you'd fetch container data from the server
            // For now, we'll just open the modal
            document.getElementById('modal-title').textContent = 'Edit Container';
            document.getElementById('container-name').value = name;
            modal.style.display = 'block';
        });
    });
    
    // Handle delete container buttons
    const deleteButtons = document.querySelectorAll('.delete-container');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const name = this.getAttribute('data-name');
            if (confirm('Are you sure you want to delete this container?')) {
                // In a real app, you'd send a request to delete the container
                console.log('Deleting container:', name);
            }
        });
    });
    
    // Form submission
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // In a real app, you'd submit form data to the server
            const formData = new FormData(form);
            const containerData = {};
            
            for (const [key, value] of formData.entries()) {
                // Special handling for checkbox
                if (key === 'shared') {
                    containerData[key] = value === 'on';
                } else {
                    containerData[key] = value;
                }
            }
            
            console.log('Container data:', containerData);
            
            // Close modal after submission
            modal.style.display = 'none';
            
            // In a real app, you'd reload data or update the UI
        });
    }
});
