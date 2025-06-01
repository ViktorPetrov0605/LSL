// Monitoring JS

document.addEventListener('DOMContentLoaded', function() {
    // Initialize monitoring view
    updateMonitoring();
    
    // Set up polling interval (every 5 seconds)
    setInterval(updateMonitoring, 5000);
    
    function updateMonitoring() {
        // In a real app, this would fetch data from the server's monitoring endpoint
        fetchServerStats();
        fetchClientStatus();
        fetchRunningContainers();
    }
    
    function fetchServerStats() {
        // Simulated data for demonstration
        // In a real app, you'd fetch this from the server API
        const stats = {
            cpu: Math.floor(Math.random() * 100),
            memory: Math.floor(Math.random() * 100),
            disk: Math.floor(Math.random() * 100),
        };
        
        updateStats(stats);
    }
    
    function updateStats(stats) {
        // Update CPU stats
        document.getElementById('cpu-usage').textContent = `${stats.cpu}%`;
        document.getElementById('cpu-bar').style.width = `${stats.cpu}%`;
        
        // Update Memory stats
        document.getElementById('memory-usage').textContent = `${stats.memory}%`;
        document.getElementById('memory-bar').style.width = `${stats.memory}%`;
        
        // Update Disk stats
        document.getElementById('disk-usage').textContent = `${stats.disk}%`;
        document.getElementById('disk-bar').style.width = `${stats.disk}%`;
    }
    
    function fetchClientStatus() {
        // In a real app, you'd fetch this from the server API
        // Simulated data for demonstration
        const clients = [
            {
                uuid: "client-123-abc",
                username: "user1",
                lastPing: "2 minutes ago",
                status: "Online",
                runningContainers: 2
            },
            {
                uuid: "client-456-def",
                username: "user2",
                lastPing: "5 minutes ago",
                status: "Online",
                runningContainers: 1
            }
        ];
        
        updateClientTable(clients);
    }
    
    function updateClientTable(clients) {
        const tableBody = document.getElementById('client-table-body');
        
        if (!clients || clients.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="empty-table">No clients connected</td></tr>';
            return;
        }
        
        tableBody.innerHTML = '';
        
        clients.forEach(client => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${client.uuid}</td>
                <td>${client.username}</td>
                <td>${client.lastPing}</td>
                <td>${client.status}</td>
                <td>${client.runningContainers}</td>
            `;
            tableBody.appendChild(row);
        });
    }
    
    function fetchRunningContainers() {
        // In a real app, you'd fetch this from the server API
        // Simulated data for demonstration
        const containers = [
            {
                id: "abc123",
                name: "lsl-ubuntu-123",
                image: "ubuntu:latest",
                owner: "user1",
                status: "Running"
            },
            {
                id: "def456",
                name: "lsl-nginx-456",
                image: "nginx:latest",
                owner: "user1",
                status: "Running"
            },
            {
                id: "ghi789",
                name: "lsl-python-789",
                image: "python:3.9",
                owner: "user2",
                status: "Running"
            }
        ];
        
        updateContainerTable(containers);
    }
    
    function updateContainerTable(containers) {
        const tableBody = document.getElementById('container-table-body');
        
        if (!containers || containers.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="empty-table">No containers running</td></tr>';
            return;
        }
        
        tableBody.innerHTML = '';
        
        containers.forEach(container => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${container.id}</td>
                <td>${container.name}</td>
                <td>${container.image}</td>
                <td>${container.owner}</td>
                <td>${container.status}</td>
                <td>
                    <button class="btn btn-small btn-danger stop-container" data-id="${container.id}">Stop</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // Add event listeners to the stop buttons
        document.querySelectorAll('.stop-container').forEach(button => {
            button.addEventListener('click', function() {
                const containerId = this.getAttribute('data-id');
                if (confirm('Are you sure you want to stop this container?')) {
                    // In a real app, you'd send a request to stop the container
                    console.log('Stopping container:', containerId);
                }
            });
        });
    }
});
