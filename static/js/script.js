document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading');
    const vectorStoreSelect = document.getElementById('vector-store-select');
    const refreshVectorStoresButton = document.getElementById('refresh-vector-stores');
    
    // Tab elements
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    // Search elements
    const searchQuery = document.getElementById('search-query');
    const maxResults = document.getElementById('max-results');
    const rewriteQuery = document.getElementById('rewrite-query');
    const searchButton = document.getElementById('search-button');
    const searchResults = document.getElementById('search-results');
    
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
        if (e.key === 'Enter' && !e.shiftKey && window.activeTab === 'chat') {
            e.preventDefault();
            sendMessage();
        }
    });
    
    refreshVectorStoresButton.addEventListener('click', loadVectorStores);
    
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            console.log('Tab clicked:', button.getAttribute('data-tab'));
            
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            const tabPane = document.getElementById(`${tabId}-tab`);
            
            console.log('Tab pane element:', tabPane);
            
            if (tabPane) {
                tabPane.classList.add('active');
                
                // Set the current active tab in a global variable
                window.activeTab = tabId;
                console.log('Active tab set to:', window.activeTab);
                
                // Focus the appropriate input field based on the active tab
                if (tabId === 'chat') {
                    setTimeout(() => userInput.focus(), 100);
                } else if (tabId === 'search') {
                    setTimeout(() => searchQuery.focus(), 100);
                }
            } else {
                console.error(`Tab pane with ID "${tabId}-tab" not found`);
            }
        });
    });
    
    // Initialize the active tab
    window.activeTab = 'chat';
    
    // Search functionality
    searchButton.addEventListener('click', performSearch);
    searchQuery.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch();
        }
    });
    
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
        // Only proceed if we're in the chat tab
        if (window.activeTab !== 'chat') {
            console.log('Not in chat tab, ignoring send message request');
            return;
        }
        
        const message = userInput.value.trim();
        if (!message) return;
        
        // Check if chat is initialized
        if (!threadId || !assistantId) {
            addErrorMessage('Chat not initialized. Please try refreshing the page.');
            return;
        }
        
        try {
            // Clear input
            userInput.value = '';
            
            // Add user message to chat
            addMessage(message, 'user');
            
            // Show loading indicator
            loadingIndicator.style.display = 'flex';
            
            // Send message to server
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
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to send message');
            }
            
            // Add assistant response to chat
            addMessage(data.response, 'assistant');
        } catch (error) {
            console.error('Error sending message:', error);
            addErrorMessage(error.message);
        } finally {
            loadingIndicator.style.display = 'none';
            scrollToBottom();
        }
    }
    
    // Sanitize and format markdown content
    function sanitizeMarkdown(content) {
        if (!content) return '';
        
        // Replace source references like 【4:0†source】 with proper markdown links
        content = content.replace(/【(\d+):(\d+)†source】/g, '[[Source $1:$2]](#)');
        
        // Ensure headers have spaces after the # symbols
        content = content.replace(/###(?=[^\s])/g, '### ');
        content = content.replace(/##(?=[^\s])/g, '## ');
        content = content.replace(/#(?=[^\s])/g, '# ');
        
        // Fix bullet points that might not have proper spacing
        content = content.replace(/\n-(?=[^\s])/g, '\n- ');
        
        // Add line breaks before headers for better formatting
        content = content.replace(/([^\n])(\n#{1,6}\s)/g, '$1\n\n$2');
        
        // Use marked.js to convert markdown to HTML
        try {
            // Set options for marked to preserve line breaks
            marked.setOptions({
                breaks: true,
                gfm: true
            });
            
            // Convert markdown to HTML
            const htmlContent = marked.parse(content);
            return htmlContent;
        } catch (error) {
            console.error('Error parsing markdown:', error);
            return content;
        }
    }
    
    // Add a message to the chat
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (role === 'assistant') {
            // For assistant messages, use innerHTML to render markdown
            messageContent.innerHTML = sanitizeMarkdown(content);
            
            // Make all links open in a new tab
            const links = messageContent.querySelectorAll('a');
            links.forEach(link => {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            });
        } else {
            // For user messages, just use text content
            messageContent.textContent = content;
        }
        
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
    
    async function performSearch() {
        const query = searchQuery.value.trim();
        if (!query) {
            alert('Please enter a search query');
            return;
        }
        
        try {
            loadingIndicator.style.display = 'flex';
            
            const response = await fetch('/api/search-vector-store', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    max_results: parseInt(maxResults.value) || 10,
                    rewrite_query: rewriteQuery.checked
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to search vector store');
            }
            
            displaySearchResults(data);
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = `
                <div class="no-results">
                    <p>Error: ${error.message}</p>
                </div>
            `;
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }
    
    function displaySearchResults(results) {
        // Handle case where no results are found
        if (!results || (results.data && results.data.length === 0)) {
            searchResults.innerHTML = `
                <div class="no-results">
                    <p>No results found for your query</p>
                </div>
            `;
            return;
        }
        
        let html = `<h3>Search Results</h3>`;
        
        // Handle the format from search_vector_store.py
        if (results.data && Array.isArray(results.data)) {
            // Format from the original implementation
            results.data.forEach((item, index) => {
                html += createSearchResultHTML(item, index + 1);
            });
        } else if (results.data) {
            // Alternative format
            const items = results.data;
            Object.keys(items).forEach((key, index) => {
                const item = items[key];
                html += createSearchResultHTML(item, index + 1);
            });
        } else {
            // Format directly from search_vector_store.py
            const items = results;
            if (items && Array.isArray(items)) {
                items.forEach((item, index) => {
                    html += createSearchResultHTML(item, index + 1);
                });
            }
        }
        
        searchResults.innerHTML = html;
        
        // Add event listeners to any interactive elements in the search results
        const resultLinks = searchResults.querySelectorAll('a');
        resultLinks.forEach(link => {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        });
    }
    
    function createSearchResultHTML(item, index) {
        let html = `
            <div class="search-result">
                <div class="search-result-header">
                    <div class="search-result-title">
                        Result ${index}: ${item.filename || 'Unnamed Document'}
                    </div>
                    <div class="search-result-meta">
        `;
        
        // Add score if present
        if (item.score !== undefined) {
            const scoreDisplay = typeof item.score === 'number' 
                ? (item.score * 100).toFixed(2) + '%' 
                : item.score;
            html += `<span>Score: ${scoreDisplay}</span>`;
        }
        
        // Add file ID if present
        if (item.file_id) {
            html += `<span>File ID: ${item.file_id}</span>`;
        }
        
        html += `</div></div>`;
        
        // Add content if present
        if (item.content) {
            html += `<div class="search-result-content">`;
            
            if (Array.isArray(item.content)) {
                // Handle array of content items
                item.content.forEach(content => {
                    if (content.type === 'text') {
                        // Process text content
                        let text = content.text || '';
                        
                        // Replace \n\n with proper paragraph breaks
                        text = text.replace(/\n\n/g, '</p><p>');
                        
                        // Replace single \n with <br>
                        text = text.replace(/\n/g, '<br>');
                        
                        // Wrap in paragraph tags if not already
                        if (!text.startsWith('<p>')) {
                            text = '<p>' + text + '</p>';
                        }
                        
                        // Render markdown content
                        const formattedText = sanitizeMarkdown(text);
                        html += `<div class="markdown-content">${formattedText}</div>`;
                    }
                });
            } else if (typeof item.content === 'string') {
                // Handle string content
                let text = item.content;
                
                // Replace \n\n with proper paragraph breaks
                text = text.replace(/\n\n/g, '</p><p>');
                
                // Replace single \n with <br>
                text = text.replace(/\n/g, '<br>');
                
                // Wrap in paragraph tags if not already
                if (!text.startsWith('<p>')) {
                    text = '<p>' + text + '</p>';
                }
                
                // Render markdown content
                const formattedText = sanitizeMarkdown(text);
                html += `<div class="markdown-content">${formattedText}</div>`;
            }
            
            html += `</div>`;
        }
        
        // Add attributes if present
        if (item.attributes && Object.keys(item.attributes).length > 0) {
            html += `<div class="search-result-attributes">`;
            
            for (const [key, value] of Object.entries(item.attributes)) {
                html += `<div><strong>${key}:</strong> ${value}</div>`;
            }
            
            html += `</div>`;
        }
        
        html += `</div>`;
        return html;
    }
}); 