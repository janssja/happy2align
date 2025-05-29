// Session.js - Voor session.html
document.addEventListener('DOMContentLoaded', function() {
    // Elementen ophalen
    const conversationDiv = document.getElementById('conversation');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    
    // Sessie ID ophalen uit URL
    const pathParts = window.location.pathname.split('/');
    const sessionId = pathParts[pathParts.length - 1];
    
    // Conversatiegeschiedenis
    let conversationHistory = [];
    
    // Functie om bericht toe te voegen aan conversatie
    function addMessageToConversation(sender, message, agentType = null) {
        // Bericht toevoegen aan geschiedenis
        conversationHistory.push({
            sender: sender,
            message: message,
            agentType: agentType
        });
        
        // Conversatie weergeven
        updateConversationDisplay();
    }
    
    // Functie om conversatie weer te geven
    function updateConversationDisplay() {
        conversationDiv.innerHTML = '';
        
        conversationHistory.forEach(item => {
            const messageDiv = document.createElement('div');
            messageDiv.className = item.sender === 'user' ? 'user-message' : 'agent-message';
            
            if (item.sender !== 'user' && item.agentType) {
                const agentTypeDiv = document.createElement('div');
                agentTypeDiv.className = 'agent-type';
                agentTypeDiv.textContent = item.agentType;
                messageDiv.appendChild(agentTypeDiv);
            }
            
            const messageContent = document.createElement('div');
            messageContent.textContent = item.message;
            messageDiv.appendChild(messageContent);
            
            conversationDiv.appendChild(messageDiv);
        });
        
        // Scroll naar beneden
        conversationDiv.scrollTop = conversationDiv.scrollHeight;
    }
    
    // Functie om bericht te versturen
    function sendMessage() {
        const message = userInput.value.trim();
        
        if (!message) {
            return;
        }
        
        // Bericht toevoegen aan conversatie
        addMessageToConversation('user', message);
        
        // Input veld leegmaken
        userInput.value = '';
        
        // API call naar backend
        fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                query: message
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                addMessageToConversation('agent', `Error: ${data.error}`);
            } else {
                if (data.agent_type === 'RequirementRefiner') {
                    // Toon verfijnde vereisten en volgende vraag
                    addMessageToConversation('agent', data.next_question, 'Requirement Refiner');
                } else if (data.agent_type === 'WorkflowRefiner') {
                    // Toon gegenereerde workflow
                    const workflowText = data.workflow.join('\n');
                    addMessageToConversation('agent', workflowText, 'Workflow Generator');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToConversation('agent', 'Er is een fout opgetreden bij het verwerken van je bericht.');
        });
    }
    
    // Event listeners
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});
