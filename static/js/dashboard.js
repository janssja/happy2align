// Dashboard.js - Voor dashboard.html
document.addEventListener('DOMContentLoaded', function() {
    // Nieuwe sessie aanmaken
    const createSessionBtn = document.getElementById('createSessionBtn');
    const sessionTopicInput = document.getElementById('sessionTopic');
    
    if (createSessionBtn) {
        createSessionBtn.addEventListener('click', function() {
            const topic = sessionTopicInput.value.trim();
            
            if (!topic) {
                alert('Vul een onderwerp in voor de sessie.');
                return;
            }
            
            // API call naar backend
            fetch('/dashboard/sessions/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic: topic }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    if (data.message) {
                        alert(data.message);
                    }
                } else {
                    // Redirect naar nieuwe sessie
                    window.location.href = `/dashboard/sessions/${data.session.id}`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Er is een fout opgetreden bij het aanmaken van de sessie.');
            });
        });
    }
});
