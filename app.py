from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import pyttsx3
import ollama
import threading
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize the text-to-speech engine
engine = pyttsx3.init()
engine.setProperty("rate", 170)

# Try to configure a female voice
voices = engine.getProperty('voices')
selected_voice = None

for voice in voices:
    if "samantha" in voice.name.lower():
        selected_voice = voice
        break

if not selected_voice:
    # Default to the first female voice if Samantha isn't found
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():
            selected_voice = voice
            break

if selected_voice:
    engine.setProperty('voice', selected_voice.id)
    logger.info(f"Using voice: {selected_voice.name}")
else:
    logger.info("No female voice found, using default voice.")

# Function to speak text using pyttsx3
def speak_text(text):
    """Speak the provided text using the configured TTS engine"""
    try:
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        logger.error(f"Error in speak_text: {e}")
        return False

# Function to get AI response using Ollama
def get_ai_response(user_input):
    """Get AI response using Ollama or fallback responses"""
    if "your name" in user_input.lower():
        return "My name is Lisa."
    elif "who developed you" in user_input.lower():
        return "I was developed by Robo Miracle."
    else:
        try:
            # Use the correct model name 'llama3.2'
            response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": user_input}])
            logger.info(f"Ollama Response: {response}")

            # Handle the response format
            if 'message' in response:
                return response['message']['content']
            elif 'content' in response:
                return response['content']
            else:
                return "Received unexpected response format from Ollama."
        except Exception as e:
            logger.error(f"Error in AI response: {e}")
            return "I am having trouble connecting to my AI backend. Please try again later."

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get AI response
@app.route('/api/response', methods=['POST'])
def api_response():         
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get AI response
    response = get_ai_response(user_input)
    
    # Start a thread to speak the response (so it doesn't block the API response)
    threading.Thread(target=speak_text, args=(response,)).start()
    
    return jsonify({'response': response})

# API endpoint for speech-to-text (optional if you want to use server-side STT instead of browser)
@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    # Save the file temporarily
    temp_path = "temp_audio.wav"
    audio_file.save(temp_path)                
    
    # Use speech recognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            os.remove(temp_path)  # Clean up temp file
            return jsonify({'text': text})
        except sr.UnknownValueError:
            os.remove(temp_path)  # Clean up temp file
            return jsonify({'error': 'Could not understand audio'}), 400
        except Exception as e:
            os.remove(temp_path)  # Clean up temp file
            logger.error(f"Error in speech recognition: {e}")
            return jsonify({'error': str(e)}), 500

# Create templates directory and HTML file
def setup_templates():
    """Create the necessary directory structure and template files"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    # Create directories if they don't exist
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'css'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'js'), exist_ok=True)
    
    # Create index.html
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lisa - Web Voice Assistant</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <div class="theme-switch">
        <label class="switch">
            <input type="checkbox" id="theme-toggle">
            <span class="slider"></span>
        </label>
    </div>

    <div class="container">
        <div class="header">
            <h1>Lisa - Voice Assistant</h1>
        </div>
        
        <div class="chat-container">
            <div class="chat-log" id="chat-log">
                <!-- Messages will appear here -->
            </div>
            
            <div class="visualizer" id="visualizer">
                <!-- Voice visualization bars -->
            </div>
            
            <div class="status" id="status">Click the Speak button to start</div>
            
            <div class="controls">
                <div class="text-input">
                    <input type="text" id="text-message" placeholder="Type your message...">
                    <button class="send-btn" id="send-btn">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M22 2L11 13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
                
                <button class="btn btn-primary" id="speak-btn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" fill="white"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Speak
                </button>
                
                <button class="btn btn-danger" id="stop-btn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
                        <rect x="6" y="6" width="12" height="12" fill="white"/>
                    </svg>
                    Stop
                </button>
            </div>
        </div>
    </div>

    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>""")
    
    # Create CSS file
    with open(os.path.join(static_dir, 'css', 'styles.css'), 'w') as f:
        f.write(""":root {
    --primary-color: #007BFF;
    --accent-color: #00E5FF;
    --dark-color: #333;
    --light-color: #f0f0f0;
    --danger-color: #DC3545;
    --success-color: #28a745;
    --L-message: #E3F2FD;
    --user-message: #FFF8E1;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Arial', sans-serif;
}

body {
    background-color: #f5f5f5;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

.container {
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 20px;
    flex: 1;
    display: flex;
    flex-direction: column;
}

.header {
    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
    padding: 20px;
    color: white;
    border-radius: 10px 10px 0 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.chat-container {
    flex: 1;
    background-color: white;
    border-radius: 0 0 10px 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.chat-log {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background-color: white;
}

.message {
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 20px;
    max-width: 80%;
    animation: fadeIn 0.3s ease-in-out;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    word-wrap: break-word;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.user-message {
    background-color: var(--user-message);
    align-self: flex-end;
    margin-left: auto;
    border-bottom-right-radius: 5px;
}

.lisa-message {
    background-color: var(--lisa-message);
    align-self: flex-start;
    border-bottom-left-radius: 5px;
}

.status {
    text-align: center;
    padding: 10px;
    font-size: 14px;
    color: var(--dark-color);
    background-color: rgba(240, 240, 240, 0.8);
    border-top: 1px solid #e0e0e0;
}

.controls {
    display: flex;
    gap: 10px;
    padding: 15px;
    background-color: #f8f8f8;
    border-top: 1px solid #e0e0e0;
}

.btn {
    padding: 12px 24px;
    border: none;
    border-radius: 30px;
    cursor: pointer;
    font-weight: bold;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
}

.btn-danger {
    background-color: var(--danger-color);
    color: white;
}

.btn i {
    margin-right: 8px;
}

.pulse {
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(0, 123, 255, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
}

.typing-indicator {
    display: flex;
    align-items: center;
    padding: 10px 20px;
    margin-bottom: 10px;
}

.typing-indicator span {
    height: 8px;
    width: 8px;
    float: left;
    margin: 0 1px;
    background-color: #9E9EA1;
    display: block;
    border-radius: 50%;
    opacity: 0.4;
}

.typing-indicator span:nth-of-type(1) {
    animation: typing 1s infinite;
}

.typing-indicator span:nth-of-type(2) {
    animation: typing 1s 0.33s infinite;
}

.typing-indicator span:nth-of-type(3) {
    animation: typing 1s 0.66s infinite;
}

@keyframes typing {
    0% { opacity: 0.4; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.2); }
    100% { opacity: 0.4; transform: scale(1); }
}

.text-input {
    flex: 1;
    display: flex;
}

#text-message {
    flex: 1;
    padding: 12px 20px;
    border: 1px solid #ddd;
    border-radius: 30px;
    font-size: 16px;
    transition: all 0.3s;
}

#text-message:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.send-btn {
    background-color: var(--primary-color);
    color: white;
    border: none;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    margin-left: 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
}

.send-btn:hover {
    background-color: #0056b3;
    transform: scale(1.05);
}

.visualizer {
    height: 60px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
}

.visualizer-bar {
    background-color: var(--accent-color);
    width: 4px;
    height: 10px;
    margin: 0 2px;
    border-radius: 2px;
    transition: height 0.2s ease;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 10px;
        max-width: 100%;
    }
    
    .message {
        max-width: 90%;
    }
    
    .controls {
        flex-direction: column;
    }
    
    .text-input {
        margin-bottom: 10px;
    }
}

/* Dark mode toggle */
.theme-switch {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 100;
}

.switch {
    position: relative;
    display: inline-block;
    width: 60px;
    height: 34px;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .4s;
    border-radius: 34px;
}

.slider:before {
    position: absolute;
    content: "";
    height: 26px;
    width: 26px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
}

input:checked + .slider {
    background-color: var(--primary-color);
}

input:checked + .slider:before {
    transform: translateX(26px);
}

/* Dark mode styles */
body.dark-mode {
    background-color: #121212;
    color: #f0f0f0;
}

body.dark-mode .header {
    background: linear-gradient(135deg, #304FFE, #00B0FF);
}

body.dark-mode .chat-container {
    background-color: #1E1E1E;
}

body.dark-mode .chat-log {
    background-color: #1E1E1E;
}

body.dark-mode .controls {
    background-color: #2D2D2D;
    border-top: 1px solid #3D3D3D;
}

body.dark-mode .status {
    background-color: rgba(45, 45, 45, 0.8);
    color: #e0e0e0;
    border-top: 1px solid #3D3D3D;
}

body.dark-mode .user-message {
    background-color: #455A64;
    color: #f0f0f0;
}

body.dark-mode .lisa-message {
    background-color: #263238;
    color: #f0f0f0;
}

body.dark-mode #text-message {
    background-color: #333;
    color: #f0f0f0;
    border: 1px solid #555;
}

body.dark-mode #text-message:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.25);
}""")
    
    # Create JavaScript file
    with open(os.path.join(static_dir, 'js', 'app.js'), 'w') as f:
        f.write("""// Initialize speech recognition
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
});""")
    
    logger.info("Templates and static files created successfully.")

if __name__ == "__main__":                      
    # Set up the templates and static files
    setup_templates()
    
    # Run the Flask app
    app.run(debug=True, port=5000)