// Initialize speech recognition
let recognition;
let listeningActive = false;

// Function to add visualizer effects
function animateVisualizer(isActive) {
    const bars = document.querySelectorAll('.visualizer-bar');
    
    if (isActive) {
        bars.forEach(bar => {
            setInterval(() => {
                const height = Math.floor(Math.random() * 40) + 5;
                bar.style.height = `${height}px`;
            }, 100);
        });
    } else {
        bars.forEach(bar => {
            bar.style.height = '5px';
        });
    }
}

// Function to add a message to the chat log
function addMessage(text, sender) {
    const chatLog = document.getElementById('chat-log');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'lisa-message');
    messageDiv.textContent = sender === 'user' ? `You: ${text}` : `Lisa: ${text}`;
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Function to show typing indicator
function showTypingIndicator() {
    const chatLog = document.getElementById('chat-log');
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('typing-indicator');
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';
    chatLog.appendChild(typingDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Function to remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Function to get AI response from server
async function getAIResponse(userInput) {
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: userInput }),
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }
        
        const data = await response.json();
        removeTypingIndicator();
        return data.response;
    } catch (error) {
        console.error('Error getting AI response:', error);
        removeTypingIndicator();
        return "I'm having trouble connecting to my backend. Please try again later.";
    }
}

// Function to start voice recognition
function startListening() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        addMessage("Speech recognition is not supported in your browser.", "lisa");
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    listeningActive = true;
    document.getElementById('status').textContent = "Listening...";
    document.getElementById('speak-btn').classList.add('pulse');
    animateVisualizer(true);
    
    recognition.onstart = function() {
        document.getElementById('status').textContent = "Listening...";
    };
    
    recognition.onresult = async function(event) {
        const text = event.results[0][0].transcript;
        addMessage(text, "user");
        document.getElementById('status').textContent = "Processing...";
        
        if (text.toLowerCase().includes("stop")) {
            stopConversation();
            return;
        }
        
        const response = await getAIResponse(text);
        addMessage(response, "lisa");
        
        if (listeningActive) {
            document.getElementById('status').textContent = "Click the Speak button to start";
            document.getElementById('speak-btn').classList.remove('pulse');
            setTimeout(() => {
                if (listeningActive) {
                    recognition.start();
                    document.getElementById('status').textContent = "Listening...";
                    document.getElementById('speak-btn').classList.add('pulse');
                }
            }, 1000);
        }
    };
    
    recognition.onerror = function(event) {
        document.getElementById('status').textContent = "Error occurred in recognition: " + event.error;
        document.getElementById('speak-btn').classList.remove('pulse');
        animateVisualizer(false);
    };
    
    recognition.onend = function() {
        if (listeningActive) {
            document.getElementById('status').textContent = "Recognition ended, restarting...";
            setTimeout(() => {
                if (listeningActive) {
                    recognition.start();
                }
            }, 1000);
        }
    };
    
    recognition.start();
}

// Function to stop the conversation
function stopConversation() {
    listeningActive = false;
    
    if (recognition) {
        recognition.stop();
    }
    
    document.getElementById('status').textContent = "Conversation stopped.";
    document.getElementById('speak-btn').classList.remove('pulse');
    animateVisualizer(false);
    
    addMessage("Goodbye! Conversation stopped.", "Lisa");
}

// Function to handle text input submission
async function handleTextSubmit() {
    const textInput = document.getElementById('text-message');
    const userText = textInput.value.trim();
    
    if (userText) {
        addMessage(userText, "user");
        textInput.value = '';
        
        if (userText.toLowerCase().includes("stop")) {
            stopConversation();
            return;
        }
        
        const response = await getAIResponse(userText);
        addMessage(response, "Lisa");
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initial greeting
    const initialMessage = "Hi, I am Lisa. How can I help you?";
    addMessage(initialMessage, "lisa");
    
    // Button event listeners
    document.getElementById('speak-btn').addEventListener('click', startListening);
    document.getElementById('stop-btn').addEventListener('click', stopConversation);
    document.getElementById('send-btn').addEventListener('click', handleTextSubmit);
    
    // Text input event listener
    document.getElementById('text-message').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleTextSubmit();
        }
    });
    
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('change', function() {
        document.body.classList.toggle('dark-mode');
    });
    
    // Create visualizer bars
    const visualizer = document.getElementById('visualizer');
    visualizer.innerHTML = '';
    for (let i = 0; i < 15; i++) {
        const bar = document.createElement('div');
        bar.classList.add('visualizer-bar');
        visualizer.appendChild(bar);
    }
});