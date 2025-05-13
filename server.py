from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import json
import uuid
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq()
client.api_key = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

# In-memory storage for roadmaps
roadmaps = {}

# Create a default roadmap structure
def get_default_roadmap():
    # Root node for the roadmap
    return {
        "id": "root",
        "title": "My Roadmap",
        "type": "ROOT",
        "content": "Your personalized career path roadmap",
        "children": [
            {
                "id": "cs",
                "title": "Computer Science",
                "type": "CATEGORY",
                "content": "Computer Science career paths and specializations",
                "children": [
                    {
                        "id": "fullstack",
                        "title": "Full Stack Developer",
                        "type": "CATEGORY",
                        "content": "Career path: Full Stack Developer",
                        "children": []
                    },
                    {
                        "id": "ai",
                        "title": "AI Engineer",
                        "type": "CATEGORY",
                        "content": "Career path: AI Engineer",
                        "children": [
                            {
                                "id": "what-is-ai",
                                "title": "What is AI Engineer",
                                "type": "TOPIC",
                                "content": "AI Engineers develop and implement AI and machine learning solutions. They bridge the gap between data science and production systems.",
                                "resources": ["https://www.coursera.org/articles/ai-engineer"],
                                "children": [
                                    {
                                        "id": "decision",
                                        "title": "OR",
                                        "type": "DECISION",
                                        "content": "Choose a specialization",
                                        "children": [
                                            {
                                                "id": "ai-opt",
                                                "title": "AI",
                                                "type": "TOPIC",
                                                "content": "Focus on AI specialization",
                                                "children": []
                                            },
                                            {
                                                "id": "ml-opt",
                                                "title": "ML",
                                                "type": "TOPIC",
                                                "content": "Focus on ML specialization",
                                                "children": []
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "id": "tasks",
                                "title": "Tasks of an AI Engineer",
                                "type": "TOPIC",
                                "content": "Key responsibilities and day-to-day tasks of an AI Engineer",
                                "children": [
                                    {
                                        "id": "prompt-eng",
                                        "title": "Prompt Engineering",
                                        "type": "SUBTOPIC",
                                        "content": "Learn about Prompt Engineering and its applications",
                                        "children": []
                                    },
                                    {
                                        "id": "agents",
                                        "title": "Building Agents",
                                        "type": "SUBTOPIC",
                                        "content": "Learn about Building Agents and its applications",
                                        "children": []
                                    },
                                    {
                                        "id": "rag",
                                        "title": "RAG",
                                        "type": "SUBTOPIC",
                                        "content": "Learn about RAG and its applications",
                                        "children": []
                                    },
                                    {
                                        "id": "genai",
                                        "title": "Generative AI",
                                        "type": "SUBTOPIC",
                                        "content": "Learn about Generative AI and its applications",
                                        "children": []
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": "blockchain",
                        "title": "Blockchain",
                        "type": "CATEGORY",
                        "content": "Career path: Blockchain",
                        "children": []
                    },
                    {
                        "id": "devops",
                        "title": "DevOps",
                        "type": "CATEGORY",
                        "content": "Career path: DevOps",
                        "children": []
                    }
                ]
            },
            {
                "id": "ml",
                "title": "Machine Learning",
                "type": "CATEGORY",
                "content": "Machine Learning learning path",
                "children": [
                    {
                        "id": "foundation",
                        "title": "Build a foundation in Python and statistics",
                        "type": "TOPIC",
                        "content": "Learn the fundamentals of Python programming and statistics for ML",
                        "resources": ["Coursera"],
                        "children": [
                            {
                                "id": "applications",
                                "title": "Explore real-world AI applications",
                                "type": "TOPIC",
                                "content": "Practical applications of AI in different domains",
                                "resources": ["skin cancer classification", "neural networks", "fuzzy logic"],
                                "children": [
                                    {
                                        "id": "nn",
                                        "title": "Experiment with neural networks and CNNs",
                                        "type": "TOPIC",
                                        "content": "Hands-on practice with neural networks and convolutional neural networks",
                                        "resources": ["edX"],
                                        "children": []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

# Get or create a roadmap for a user
def get_or_create_roadmap(user_id):
    if user_id not in roadmaps:
        roadmaps[user_id] = get_default_roadmap()
    return roadmaps[user_id]

# Find a node by ID in the roadmap
def find_node_by_id(node, node_id):
    if node["id"] == node_id:
        return node
    
    for child in node.get("children", []):
        result = find_node_by_id(child, node_id)
        if result:
            return result
    
    return None

# Add a child node to a parent node
def add_child_node(roadmap, parent_id, title, content, node_type="TOPIC", resources=None):
    parent = find_node_by_id(roadmap, parent_id)
    
    if parent:
        child = {
            "id": str(uuid.uuid4()),
            "title": title,
            "type": node_type,
            "content": content,
            "resources": resources or [],
            "children": []
        }
        parent["children"].append(child)
        return child["id"]
    
    return None

# Serve the main HTML page
@app.route('/')
def index():
    return send_from_directory('pages', 'custom.html')

# API endpoint to get a user's roadmap
@app.route('/api/roadmap/<user_id>')
def get_roadmap(user_id):
    roadmap = get_or_create_roadmap(user_id)
    return jsonify(roadmap)

# API endpoint to update a roadmap based on user message
@app.route('/api/chat', methods=['POST'])
def process_chat():
    data = request.json
    user_id = data.get('user_id', 'default_user')
    message = data.get('message', '')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    # Get the user's roadmap
    roadmap = get_or_create_roadmap(user_id)
    
    # Create messages for AI to analyze
    messages = [
        {"role": "system", "content": "You are a career advice AI. Analyze the user's message and suggest career paths."},
        {"role": "user", "content": message}
    ]
    
    try:
        # Call Groq API to get a response
        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Simple keyword analysis to update the roadmap
        lower_message = message.lower()
        
        # Create new nodes based on detected keywords
        if any(term in lower_message for term in ["ai", "machine learning", "artificial intelligence"]):
            # Add AI-specific content
            ai_node = find_node_by_id(roadmap, "ai")
            if ai_node:
                new_node_id = add_child_node(
                    roadmap,
                    "ai",
                    f"AI Interest: {message[:20]}...",
                    "Based on your interests, here are some AI career path recommendations.",
                    "TOPIC"
                )
        elif any(term in lower_message for term in ["web", "frontend", "backend", "full stack"]):
            # Add web development content
            add_child_node(
                roadmap,
                "fullstack",
                f"Web Dev: {message[:20]}...",
                "Resources and learning paths for web development.",
                "TOPIC",
                ["MDN Web Docs", "freeCodeCamp"]
            )
        elif any(term in lower_message for term in ["blockchain", "crypto"]):
            # Add blockchain content
            add_child_node(
                roadmap,
                "blockchain",
                f"Blockchain: {message[:20]}...",
                "Learning resources for blockchain technology.",
                "TOPIC",
                ["Ethereum docs", "Solidity tutorials"]
            )
        elif any(term in lower_message for term in ["devops", "cloud", "deployment"]):
            # Add DevOps content
            add_child_node(
                roadmap,
                "devops",
                f"DevOps: {message[:20]}...",
                "DevOps learning path and resources.",
                "TOPIC",
                ["Docker docs", "Kubernetes tutorials"]
            )
        
        # Return the updated roadmap and AI response
        return jsonify({
            "response": ai_response,
            "roadmap": roadmap
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
