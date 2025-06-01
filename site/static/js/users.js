// Users management JS

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('user-modal');
    const addUserBtn = document.getElementById('add-user');
    const closeBtn = modal.querySelector('.close');
    const form = document.getElementById('user-form');
    
    // Open modal when "Add User" button is clicked
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function() {
            // Clear form for new user
            form.reset();
            document.getElementById('modal-title').textContent = 'Add User';
            document.getElementById('user-uuid').value = ''; // Clear UUID for new user
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
    
    // Handle edit user buttons
    const editButtons = document.querySelectorAll('.edit-user');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const uuid = this.getAttribute('data-uuid');
            // In a real app, you'd fetch user data from the server
            // For now, we'll just open the modal
            document.getElementById('modal-title').textContent = 'Edit User';
            document.getElementById('user-uuid').value = uuid;
            modal.style.display = 'block';
        });
    });
    
    // Handle delete user buttons
    const deleteButtons = document.querySelectorAll('.delete-user');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const uuid = this.getAttribute('data-uuid');
            if (confirm('Are you sure you want to delete this user?')) {
                // In a real app, you'd send a request to delete the user
                console.log('Deleting user:', uuid);
            }
        });
    });
    
    // Handle reset token buttons
    const resetButtons = document.querySelectorAll('.reset-token');
    resetButtons.forEach(button => {
        button.addEventListener('click', function() {
            const uuid = this.getAttribute('data-uuid');
            if (confirm('Are you sure you want to reset this user\'s token?')) {
                // In a real app, you'd send a request to reset the token
                console.log('Resetting token for user:', uuid);
            }
        });
    });
    
    // Form submission
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // In a real app, you'd submit form data to the server
            const formData = new FormData(form);
            const userData = {};
            
            for (const [key, value] of formData.entries()) {
                userData[key] = value;
            }
            
            console.log('User data:', userData);
            
            // Close modal after submission
            modal.style.display = 'none';
            
            // In a real app, you'd reload data or update the UI
        });
    }
});
