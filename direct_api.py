import os
from flask import Flask, jsonify, request, session
from groq import Groq
from dotenv import load_dotenv
import json

# Create a simple app for direct API testing
app = Flask(__name__)
app.secret_key = 'direct_api_test_key'

# Load environment variables
load_dotenv()

# Sample roadmap as fallback
sample_roadmap = {
    "nodes": [
        {"id": "root", "label": "Your Career Path", "type": "root"},
        {"id": "cs", "label": "Computer Science", "type": "category", "parent": "root"}
    ],
    "nodeDetails": {
        "root": {
            "content": "This is the starting point of your personalized career roadmap.",
            "resources": ["Let's start by discussing your interests."]
        },
        "cs": {
            "content": "Computer Science is a foundational field for many technology careers.",
            "resources": ["Consider exploring programming fundamentals."]
        }
    }
}

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Direct API Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .chat-container { display: flex; flex-direction: column; height: 500px; border: 1px solid #ccc; }
            .messages { flex: 1; overflow-y: auto; padding: 10px; background: #f9f9f9; }
            .user-message { background: #e3f2fd; padding: 8px; margin: 5px; border-radius: 8px; }
            .bot-message { background: #f1f8e9; padding: 8px; margin: 5px; border-radius: 8px; }
            .input-area { display: flex; padding: 10px; background: #eee; }
            input { flex: 1; padding: 8px; }
            button { margin-left: 10px; padding: 8px 16px; background: #4caf50; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Direct Groq API Test</h1>
        <div class="chat-container">
            <div id="messages" class="messages"></div>
            <div class="input-area">
                <input type="text" id="message-input" placeholder="Type your message here..." />
                <button id="send-button">Send</button>
            </div>
        </div>
        
        <script>
            const messagesDiv = document.getElementById('messages');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            
            // Add initial bot message
            addMessage('Hello! I am your CareerPath.AI assistant. How can I help you today?', 'bot');
            
            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
            
            function addMessage(text, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = sender === 'user' ? 'user-message' : 'bot-message';
                messageDiv.textContent = text;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;
                
                // Add user message to chat
                addMessage(message, 'user');
                messageInput.value = '';
                
                // Add loading message
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'bot-message';
                loadingDiv.textContent = 'Thinking...';
                messagesDiv.appendChild(loadingDiv);
                
                try {
                    // Send to API
                    const response = await fetch('/direct-api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ message })
                    });
                    
                    const data = await response.json();
                    
                    // Remove loading message
                    messagesDiv.removeChild(loadingDiv);
                    
                    // Add bot response
                    if (data.response) {
                        addMessage(data.response, 'bot');
                    } else if (data.error) {
                        addMessage('Error: ' + data.error, 'bot');
                    }
                } catch (error) {
                    messagesDiv.removeChild(loadingDiv);
                    addMessage('Sorry, something went wrong. Please try again.', 'bot');
                    console.error(error);
                }
            }
        </script>
    </body>
    </html>
    """

@app.route('/direct-api/chat', methods=['POST'])
def direct_chat():
    try:
        print("\n============ DIRECT API ENDPOINT CALLED ============")
        
        # Get user message
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'})
        
        print(f"User message: {user_message}")
        
        # Ensure conversation history is initialized
        if 'conversation' not in session:
            session['conversation'] = []
        
        # Add user message to conversation history
        session['conversation'].append({"role": "user", "content": user_message})
        
        # Get API key
        api_key = os.getenv("GROQ_API_KEY")
        print(f"API key available: {bool(api_key)}")
        
        if not api_key:
            return jsonify({'error': 'API key not found'})
        
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": "You are CareerPath.AI, a helpful career advisor who creates personalized learning roadmaps."}
        ]
        
        # Add conversation history (up to 5 messages for simplicity)
        messages.extend(session['conversation'][-5:])
        
        print(f"Sending {len(messages)} messages to Groq API")
        print(f"Messages: {json.dumps(messages, indent=2)}")
        
        # Make API call
        response = client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract response
        bot_response = response.choices[0].message.content
        print(f"API response received: {bot_response[:100]}...")
        
        # Add bot response to conversation history
        session['conversation'].append({"role": "assistant", "content": bot_response})
        
        return jsonify({
            'response': bot_response,
            'roadmap': sample_roadmap
        })
        
    except Exception as e:
        import traceback
        print(f"Error in direct chat endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'roadmap': sample_roadmap
        })

if __name__ == '__main__':
    app.run(debug=True, port=5002)
