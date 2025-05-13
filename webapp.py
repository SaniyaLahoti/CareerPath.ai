from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import uuid
from dotenv import load_dotenv
import groq
import threading

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')

# In-memory storage
roadmaps = {}
chat_history = {}

# Initialize Groq client
client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

# Get user ID
def get_user_id():
    if not request.cookies.get('user_id'):
        return str(uuid.uuid4())
    return request.cookies.get('user_id')

# Create default roadmap
def create_default_roadmap():
    return {
        "nodes": [
            {"id": "root", "label": "Computer Science", "type": "category"},
            {"id": "ai", "label": "AI Engineer", "type": "category"},
            {"id": "fullstack", "label": "Full Stack Developer", "type": "category"},
            {"id": "blockchain", "label": "Blockchain", "type": "category"},
            {"id": "devops", "label": "DevOps", "type": "category"},
            {"id": "what_is_ai", "label": "What is AI Engineer", "type": "topic"},
            {"id": "or", "label": "OR", "type": "decision"},
            {"id": "ai_option", "label": "AI", "type": "topic"},
            {"id": "ml_option", "label": "ML", "type": "topic"},
            {"id": "tasks", "label": "Tasks of an AI Engineer", "type": "topic"},
            {"id": "prompt_eng", "label": "Prompt Engineering", "type": "subtopic"},
            {"id": "agents", "label": "Building Agents", "type": "subtopic"},
            {"id": "rag", "label": "RAG", "type": "subtopic"},
            {"id": "genai", "label": "Generative AI", "type": "subtopic"},
            {"id": "ml", "label": "Machine Learning", "type": "category"},
            {"id": "foundation", "label": "Build a foundation in Python and statistics", "type": "topic"},
            {"id": "coursera", "label": "Coursera", "type": "resource"},
            {"id": "applications", "label": "Explore real-world AI applications", "type": "topic"},
            {"id": "skin_cancer", "label": "skin cancer classification", "type": "resource"},
            {"id": "neural_networks", "label": "neural networks", "type": "resource"},
            {"id": "fuzzy_logic", "label": "fuzzy logic", "type": "resource"},
            {"id": "experiment", "label": "Experiment with neural networks and CNNs", "type": "topic"},
            {"id": "edx", "label": "edX", "type": "resource"}
        ],
        "edges": [
            {"from": "root", "to": "ai"},
            {"from": "root", "to": "fullstack"},
            {"from": "root", "to": "blockchain"},
            {"from": "root", "to": "devops"},
            {"from": "ai", "to": "what_is_ai"},
            {"from": "what_is_ai", "to": "or"},
            {"from": "or", "to": "ai_option"},
            {"from": "or", "to": "ml_option"},
            {"from": "ai", "to": "tasks"},
            {"from": "tasks", "to": "prompt_eng"},
            {"from": "tasks", "to": "agents"},
            {"from": "tasks", "to": "rag"},
            {"from": "tasks", "to": "genai"},
            {"from": "root", "to": "ml"},
            {"from": "ml", "to": "foundation"},
            {"from": "foundation", "to": "coursera"},
            {"from": "foundation", "to": "applications"},
            {"from": "applications", "to": "skin_cancer"},
            {"from": "applications", "to": "neural_networks"},
            {"from": "applications", "to": "fuzzy_logic"},
            {"from": "applications", "to": "experiment"},
            {"from": "experiment", "to": "edx"}
        ],
        "nodeDetails": {
            "what_is_ai": {
                "content": "AI Engineers develop and implement AI and machine learning solutions. They bridge the gap between data science and production systems.",
                "resources": ["https://www.coursera.org/articles/ai-engineer"]
            },
            "foundation": {
                "content": "Learn the fundamentals of Python programming and statistics for ML",
                "resources": ["Coursera"]
            },
            "applications": {
                "content": "Practical applications of AI in different domains",
                "resources": ["skin cancer classification", "neural networks", "fuzzy logic"]
            },
            "experiment": {
                "content": "Hands-on practice with neural networks and convolutional neural networks",
                "resources": ["edX"]
            }
        }
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/roadmap')
def get_roadmap():
    user_id = get_user_id()
    if user_id not in roadmaps:
        roadmaps[user_id] = create_default_roadmap()
    
    return jsonify(roadmaps[user_id])

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = get_user_id()
    message = data.get('message', '')
    
    # Initialize chat history if needed
    if user_id not in chat_history:
        chat_history[user_id] = [
            {"role": "system", "content": "You are a friendly, empathetic career guidance expert at CareerPath.AI. Your style is concise, warm, and supportive."}
        ]
    
    # Add user message to history
    chat_history[user_id].append({"role": "user", "content": message})
    
    # Get roadmap
    if user_id not in roadmaps:
        roadmaps[user_id] = create_default_roadmap()
    
    roadmap = roadmaps[user_id]
    
    # Send message to Groq
    try:
        response = client.chat.completions.create(
            messages=chat_history[user_id],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=800
        )
        ai_response = response.choices[0].message.content
        
        # Add AI response to history
        chat_history[user_id].append({"role": "assistant", "content": ai_response})
        
        # Update roadmap based on user message (simplified for demo)
        update_roadmap(user_id, message, roadmap)
        
        return jsonify({
            "response": ai_response,
            "roadmap": roadmap
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_roadmap(user_id, message, roadmap):
    """Update the roadmap based on user message"""
    message_lower = message.lower()
    
    # Check for AI/ML related interests
    if any(term in message_lower for term in ["ai", "machine learning", "artificial intelligence", "ml"]):
        # Add more specific AI nodes
        new_node_id = f"ai_{uuid.uuid4().hex[:8]}"
        
        if "reinforcement" in message_lower:
            new_topic = "Reinforcement Learning"
            new_content = "Using trial and error to train AI systems through rewards and penalties."
        elif "nlp" in message_lower or "language" in message_lower:
            new_topic = "Natural Language Processing"
            new_content = "Teaching computers to understand and generate human language."
        elif "vision" in message_lower or "image" in message_lower:
            new_topic = "Computer Vision"
            new_content = "Enabling computers to interpret and understand visual information."
        elif "robotics" in message_lower or "robot" in message_lower:
            new_topic = "Robotics AI"
            new_content = "AI systems that control physical machines and robots."
        else:
            new_topic = f"AI: {message[:20]}..."
            new_content = "Specialized AI topic based on your interest."
        
        # Add new node
        roadmap["nodes"].append({
            "id": new_node_id,
            "label": new_topic,
            "type": "topic"
        })
        
        # Connect to appropriate parent
        if any(node["label"] == "AI Engineer" for node in roadmap["nodes"]):
            parent_id = next(node["id"] for node in roadmap["nodes"] if node["label"] == "AI Engineer")
        else:
            parent_id = "ai"
        
        # Add edge
        roadmap["edges"].append({
            "from": parent_id,
            "to": new_node_id
        })
        
        # Add details
        roadmap["nodeDetails"][new_node_id] = {
            "content": new_content,
            "resources": ["Online courses", "Research papers", "Practice projects"]
        }
    
    # Check for web development interests
    elif any(term in message_lower for term in ["web", "javascript", "frontend", "backend", "full stack"]):
        new_node_id = f"web_{uuid.uuid4().hex[:8]}"
        
        if "frontend" in message_lower:
            new_topic = "Frontend Development"
            new_content = "Creating user interfaces with HTML, CSS, and JavaScript."
            resources = ["MDN Web Docs", "Frontend Masters", "CSS-Tricks"]
        elif "backend" in message_lower:
            new_topic = "Backend Development"
            new_content = "Server-side programming, APIs, and databases."
            resources = ["Node.js docs", "Express.js", "PostgreSQL tutorials"]
        else:
            new_topic = "Web Development"
            new_content = "Building web applications and websites."
            resources = ["The Odin Project", "freeCodeCamp", "Web.dev"]
        
        # Add new node
        roadmap["nodes"].append({
            "id": new_node_id,
            "label": new_topic,
            "type": "topic"
        })
        
        # Connect to appropriate parent
        if any(node["label"] == "Full Stack Developer" for node in roadmap["nodes"]):
            parent_id = next(node["id"] for node in roadmap["nodes"] if node["label"] == "Full Stack Developer")
        else:
            parent_id = "fullstack"
        
        # Add edge
        roadmap["edges"].append({
            "from": parent_id,
            "to": new_node_id
        })
        
        # Add details
        roadmap["nodeDetails"][new_node_id] = {
            "content": new_content,
            "resources": resources
        }

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Create static folder if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Create templates folder if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Start the server
    app.run(debug=True, port=5050)
