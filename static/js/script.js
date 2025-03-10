document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading');
    const vectorStoreSelect = document.getElementById('vector-store-select');
    const refreshVectorStoresButton = document.getElementById('refresh-vector-stores');
    
    let threadId = null;
    let assistantId = null;
    let currentVectorStoreId = null;
    
    // Load vector stores
    loadVectorStores();
    
    // Initialize the chat
    initializeChat();
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    refreshVectorStoresButton.addEventListener('click', loadVectorStores);
    
    vectorStoreSelect.addEventListener('change', async () => {
        const selectedVectorStoreId = vectorStoreSelect.value;
        
        if (selectedVectorStoreId && selectedVectorStoreId !== currentVectorStoreId) {
            try {
                loadingIndicator.style.display = 'flex';
                
                const response = await fetch('/api/set-vector-store', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        vector_store_id: selectedVectorStoreId
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    currentVectorStoreId = selectedVectorStoreId;
                    
                    // Reset the chat
                    threadId = null;
                    assistantId = null;
                    
                    // Clear chat messages except the welcome message
                    while (chatMessages.children.length > 1) {
                        chatMessages.removeChild(chatMessages.lastChild);
                    }
                    
                    // Initialize a new chat
                    initializeChat();
                    
                    addSystemMessage(`Vector store changed successfully. You are now using "${vectorStoreSelect.options[vectorStoreSelect.selectedIndex].text}".`);
                } else {
                    addErrorMessage(data.error || 'Failed to change vector store');
                    // Reset the select to the current vector store
                    vectorStoreSelect.value = currentVectorStoreId;
                }
            } catch (error) {
                addErrorMessage('Network error: ' + error.message);
                // Reset the select to the current vector store
                vectorStoreSelect.value = currentVectorStoreId;
            } finally {
                loadingIndicator.style.display = 'none';
            }
        }
    });
    
    // Load vector stores
    async function loadVectorStores() {
        try {
            vectorStoreSelect.disabled = true;
            vectorStoreSelect.innerHTML = '<option value="">Loading vector stores...</option>';
            
            const response = await fetch('/api/vector-stores');
            const data = await response.json();
            
            if (response.ok) {
                const vectorStores = data.vector_stores;
                currentVectorStoreId = data.current_vector_store_id;
                
                // Clear the select
                vectorStoreSelect.innerHTML = '';
                
                if (vectorStores.length === 0) {
                    vectorStoreSelect.innerHTML = '<option value="">No vector stores found</option>';
                    vectorStoreSelect.disabled = true;
                    return;
                }
                
                // Add options for each vector store
                vectorStores.forEach(store => {
                    const option = document.createElement('option');
                    option.value = store.id;
                    option.textContent = store.name || store.id;
                    vectorStoreSelect.appendChild(option);
                });
                
                // Select the current vector store
                if (currentVectorStoreId) {
                    vectorStoreSelect.value = currentVectorStoreId;
                }
                
                vectorStoreSelect.disabled = false;
            } else {
                addErrorMessage(data.error || 'Failed to load vector stores');
                vectorStoreSelect.innerHTML = '<option value="">Error loading vector stores</option>';
                vectorStoreSelect.disabled = true;
            }
        } catch (error) {
            addErrorMessage('Network error: ' + error.message);
            vectorStoreSelect.innerHTML = '<option value="">Error loading vector stores</option>';
            vectorStoreSelect.disabled = true;
        }
    }
    
    // Initialize chat by creating a thread
    async function initializeChat() {
        try {
            loadingIndicator.style.display = 'flex';
            
            const response = await fetch('/api/start-thread', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                threadId = data.thread_id;
                assistantId = data.assistant_id;
                console.log('Chat initialized with thread ID:', threadId);
            } else {
                addErrorMessage(data.error || 'Failed to initialize chat');
            }
        } catch (error) {
            addErrorMessage('Network error: ' + error.message);
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }
    
    // Send a message to the assistant
    async function sendMessage() {
        const message = userInput.value.trim();
        
        if (!message) return;
        if (!threadId || !assistantId) {
            addErrorMessage('Chat not initialized yet. Please try again in a moment.');
            return;
        }
        
        // Add user message to chat
        addMessage(message, 'user');
        userInput.value = '';
        
        try {
            loadingIndicator.style.display = 'flex';
            
            const response = await fetch('/api/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    thread_id: threadId,
                    assistant_id: assistantId,
                    message: message
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                addMessage(data.response, 'assistant');
            } else {
                addErrorMessage(data.error || 'Failed to get response');
            }
        } catch (error) {
            addErrorMessage('Network error: ' + error.message);
        } finally {
            loadingIndicator.style.display = 'none';
            scrollToBottom();
        }
    }
    
    // Add a message to the chat
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    // Add a system message
    function addSystemMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    // Add an error message
    function addErrorMessage(error) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = `Error: ${error}`;
        messageContent.style.color = '#e74c3c';
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    // Scroll to the bottom of the chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}); 