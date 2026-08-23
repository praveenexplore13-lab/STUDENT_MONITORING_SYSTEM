// ==========================================
// AI CHATBOT PAGE - JAVASCRIPT
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById('chatMessages');
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');

    let selectedFile = null;

    // ==========================================
    // SEND MESSAGE
    // ==========================================

    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message && !selectedFile) return;

        // Add user message
        let userMessage = message;
        if (selectedFile) {
            userMessage += `\n[📎 Uploaded: ${selectedFile.name}]`;
        }
        addMessage(userMessage, 'user');
        chatInput.value = '';
        chatInput.disabled = true;
        sendBtn.disabled = true;

        // Show typing indicator
        const typingId = addTypingIndicator();

        // Prepare form data
        const formData = new FormData();
        formData.append('message', message);
        if (selectedFile) {
            formData.append('file', selectedFile);
        }

        // Send to server
        fetch('/chat/api', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator(typingId);
            const reply = data.reply || 'Sorry, I could not process your request.';
            addMessage(reply, 'ai');
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
            scrollToBottom();

            // Clear file
            removeFile();
        })
        .catch(error => {
            removeTypingIndicator(typingId);
            addMessage('❌ Sorry, I encountered an error. Please try again.', 'ai');
            chatInput.disabled = false;
            sendBtn.disabled = false;
            console.error('Chat error:', error);
        });
    }

    // ==========================================
    // ADD MESSAGE
    // ==========================================

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = text;
        div.appendChild(content);
        messagesContainer.appendChild(div);
        scrollToBottom();
    }

    // ==========================================
    // TYPING INDICATOR
    // ==========================================

    function addTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message ai typing-indicator';
        div.id = 'typing-' + Date.now();
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = '<span class="typing-dots">AI is thinking...</span>';
        div.appendChild(content);
        messagesContainer.appendChild(div);
        scrollToBottom();
        return div.id;
    }

    function removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }

    // ==========================================
    // SCROLL TO BOTTOM
    // ==========================================

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // ==========================================
    // CLEAR CHAT
    // ==========================================

    window.clearChat = function() {
        if (confirm('Clear all messages?')) {
            messagesContainer.innerHTML = `
                <div class="message ai">
                    <div class="message-content">
                        👋 Chat cleared! How can I help you today?
                    </div>
                </div>
            `;
            removeFile();
        }
    };

    // ==========================================
    // FILE UPLOAD
    // ==========================================

    fileInput.addEventListener('change', function(e) {
        if (this.files && this.files.length > 0) {
            selectedFile = this.files[0];
            fileName.textContent = selectedFile.name;
            filePreview.style.display = 'flex';
        }
    });

    window.removeFile = function() {
        selectedFile = null;
        fileInput.value = '';
        filePreview.style.display = 'none';
    };

    // ==========================================
    // EVENT LISTENERS
    // ==========================================

    sendBtn.addEventListener('click', sendMessage);

    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // ==========================================
    // KEYBOARD SHORTCUT: Ctrl+Shift+C
    // ==========================================

    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && (e.key === 'c' || e.key === 'C')) {
            e.preventDefault();
            chatInput.focus();
        }
    });

    console.log('🤖 AI Chatbot Page loaded!');
});