// ==========================================
// CHATBOT FUNCTIONALITY (External JS)
// ==========================================

// This file contains the same code as the inline script in chat_bubble.html
// Use this if you prefer to keep JS separate.

// The main chat functionality is already in chat_bubble.html
// This file is for additional features

// Example: Add quick reply buttons
function addQuickReplies(container) {
    const replies = ['📊 Show my risk', '👤 Tell me about myself', '📈 Show summary'];
    const wrapper = document.createElement('div');
    wrapper.style.marginTop = '8px';
    
    replies.forEach(text => {
        const btn = document.createElement('button');
        btn.className = 'quick-reply';
        btn.textContent = text;
        btn.onclick = function() {
            document.getElementById('chatInput').value = text;
            document.getElementById('chatSend').click();
        };
        wrapper.appendChild(btn);
    });
    
    container.appendChild(wrapper);
}

console.log('🤖 Chat JS loaded!');