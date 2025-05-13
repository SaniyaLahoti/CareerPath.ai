from flask import Flask, send_from_directory, render_template, request, jsonify
import os
import json
import uuid
from dotenv import load_dotenv
import groq

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')

# Initialize Groq client if API key is available
groq_client = None
if os.getenv("GROQ_API_KEY"):
    groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

# In-memory storage for user roadmaps and chat history
roadmaps = {}
chat_history = {}

# Routes
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/roadmap', methods=['GET'])
def get_roadmap():
    user_id = request.cookies.get('user_id', str(uuid.uuid4()))
    
    # If user doesn't have a roadmap yet, create default
    if user_id not in roadmaps:
        roadmaps[user_id] = create_default_roadmap()
    
    return jsonify(roadmaps[user_id])

@app.route('/api/chat', methods=['POST'])
def process_chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    user_message = data['message']
    user_id = request.cookies.get('user_id', str(uuid.uuid4()))
    
    # Initialize chat history if needed
    if user_id not in chat_history:
        chat_history[user_id] = [
            {"role": "system", "content": "You are a friendly, empathetic career guidance expert at CareerPath.AI. Your style is concise, warm, and supportive."}
        ]
    
    # Add user message to history
    chat_history[user_id].append({"role": "user", "content": user_message})
    
    # Get or create roadmap
    if user_id not in roadmaps:
        roadmaps[user_id] = create_default_roadmap()
    
    # Store current node IDs to identify new ones later
    current_node_ids = [node["id"] for node in roadmaps[user_id]["nodes"]]
    
    # Process the message and update the roadmap
    try:
        # If Groq client is available, use LLM to generate response and update roadmap
        if groq_client:
            # First, generate the AI response
            chat_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chat_history[user_id],
                temperature=0.7,
                max_tokens=800
            )
            
            ai_response = chat_response.choices[0].message.content
            chat_history[user_id].append({"role": "assistant", "content": ai_response})
            
            # Now, ask the LLM to update the roadmap based on the user message
            roadmap_update_prompt = f"""
            As a career advisor AI, analyze this user message and update their career roadmap.
            
            User message: "{user_message}"
            
            Current roadmap: {json.dumps(roadmaps[user_id])}
            
            Add relevant nodes based on the user's interests. For each node, include:
            1. id: a unique identifier (e.g., "ai_robotics")
            2. label: a descriptive label
            3. type: one of [category, topic, subtopic, resource]
            4. parent: ID of the parent node
            
            For each new node, also add details in the nodeDetails object:
            - content: detailed description
            - resources: array of learning resources
            
            Return ONLY the complete updated roadmap JSON without any explanation.
            """
            
            # Get roadmap update from LLM
            roadmap_update = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": roadmap_update_prompt}],
                temperature=0.5,
                max_tokens=2000
            )
            
            # Try to parse the roadmap from the LLM response
            try:
                roadmap_text = roadmap_update.choices[0].message.content
                
                # Extract JSON from possible markdown formatting
                if "```json" in roadmap_text:
                    roadmap_text = roadmap_text.split("```json")[1].split("```")[0].strip()
                elif "```" in roadmap_text:
                    roadmap_text = roadmap_text.split("```")[1].split("```")[0].strip()
                
                updated_roadmap = json.loads(roadmap_text)
                roadmaps[user_id] = updated_roadmap
            except Exception as e:
                print(f"Error updating roadmap: {e}")
                # If parsing fails, keep the original roadmap
        else:
            # Fallback for when Groq API is not available
            ai_response = "I'm sorry, but the AI service is currently unavailable. Please try again later."
            roadmaps[user_id] = update_roadmap_heuristic(roadmaps[user_id], user_message)
        
        # Identify new nodes
        new_node_ids = [node["id"] for node in roadmaps[user_id]["nodes"] if node["id"] not in current_node_ids]
        
        return jsonify({
            "response": ai_response,
            "roadmap": roadmaps[user_id],
            "newNodes": new_node_ids
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def create_default_roadmap():
    """Create a default roadmap to start with"""
    return {
        "nodes": [
            {"id": "root", "label": "Technology Careers", "type": "category"},
            {"id": "ai", "label": "AI & Machine Learning", "type": "category", "parent": "root"},
            {"id": "web", "label": "Web Development", "type": "category", "parent": "root"},
            {"id": "data", "label": "Data Science", "type": "category", "parent": "root"},
            {"id": "cloud", "label": "Cloud Computing", "type": "category", "parent": "root"},
            
            # AI subtopics
            {"id": "ml", "label": "Machine Learning", "type": "topic", "parent": "ai"},
            {"id": "nlp", "label": "Natural Language Processing", "type": "topic", "parent": "ai"},
            {"id": "cv", "label": "Computer Vision", "type": "topic", "parent": "ai"},
            
            # Web Development subtopics
            {"id": "frontend", "label": "Frontend", "type": "topic", "parent": "web"},
            {"id": "backend", "label": "Backend", "type": "topic", "parent": "web"},
            {"id": "fullstack", "label": "Full Stack", "type": "topic", "parent": "web"},
            
            # Data Science subtopics
            {"id": "analytics", "label": "Data Analytics", "type": "topic", "parent": "data"},
            {"id": "visualization", "label": "Data Visualization", "type": "topic", "parent": "data"},
            
            # Cloud subtopics
            {"id": "aws", "label": "AWS", "type": "topic", "parent": "cloud"},
            {"id": "azure", "label": "Azure", "type": "topic", "parent": "cloud"}
        ],
        "nodeDetails": {
            "ai": {
                "content": "Artificial Intelligence and Machine Learning focus on creating systems that can learn from data, identify patterns, and make decisions with minimal human intervention.",
                "resources": ["Coursera Machine Learning", "Fast.ai", "DeepLearning.AI"]
            },
            "web": {
                "content": "Web development involves building and maintaining websites and web applications using various programming languages, frameworks, and tools.",
                "resources": ["MDN Web Docs", "freeCodeCamp", "The Odin Project"]
            },
            "data": {
                "content": "Data Science combines domain expertise, programming skills, and knowledge of math and statistics to extract meaningful insights from data.",
                "resources": ["Kaggle", "DataCamp", "Python Data Science Handbook"]
            },
            "cloud": {
                "content": "Cloud Computing delivers computing services including servers, storage, databases, networking, software, and analytics over the internet.",
                "resources": ["AWS Training", "Google Cloud", "Microsoft Azure Learn"]
            },
            "ml": {
                "content": "Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.",
                "resources": ["Andrew Ng's Coursera Course", "Hands-On Machine Learning with Scikit-Learn and TensorFlow"]
            },
            "nlp": {
                "content": "Natural Language Processing helps computers understand, interpret, and generate human language.",
                "resources": ["NLTK", "spaCy", "Hugging Face Transformers"]
            },
            "cv": {
                "content": "Computer Vision enables computers to derive meaningful information from digital images, videos, and other visual inputs.",
                "resources": ["PyTorch Vision", "OpenCV", "TensorFlow Object Detection API"]
            },
            "frontend": {
                "content": "Frontend development focuses on creating the user interface and experience using HTML, CSS, and JavaScript.",
                "resources": ["MDN Web Docs", "Frontend Masters", "CSS-Tricks"]
            },
            "backend": {
                "content": "Backend development involves server-side logic, databases, and application architecture.",
                "resources": ["Node.js documentation", "Django documentation", "SQL tutorials"]
            },
            "fullstack": {
                "content": "Full Stack developers work on both client and server sides, handling everything from user interfaces to databases.",
                "resources": ["The Odin Project", "freeCodeCamp Full Stack path"]
            },
            "analytics": {
                "content": "Data Analytics involves examining data sets to draw conclusions about the information they contain.",
                "resources": ["Google Analytics Academy", "DataCamp", "Tableau tutorials"]
            },
            "visualization": {
                "content": "Data Visualization is the graphical representation of information and data using visual elements like charts, graphs, and maps.",
                "resources": ["D3.js", "Tableau Public", "Microsoft Power BI"]
            },
            "aws": {
                "content": "Amazon Web Services provides on-demand cloud computing platforms and APIs to individuals, companies, and governments.",
                "resources": ["AWS Documentation", "AWS Certified Cloud Practitioner", "A Cloud Guru"]
            },
            "azure": {
                "content": "Microsoft Azure is a cloud computing service for building, testing, deploying, and managing applications and services.",
                "resources": ["Microsoft Learn", "Azure Documentation", "Pluralsight Azure courses"]
            }
        }
    }

def update_roadmap_heuristic(roadmap, message):
    """
    Fallback method to update roadmap based on simple keyword matching
    Used when LLM is not available
    """
    message_lower = message.lower()
    new_nodes = []
    
    # Check for AI/Robotics related keywords
    if ('ai' in message_lower or 'artificial intelligence' in message_lower) and ('robot' in message_lower or 'robotics' in message_lower):
        if not any(node['id'] == 'ai_robotics' for node in roadmap['nodes']):
            # Add AI Robotics node
            roadmap['nodes'].append({
                "id": "ai_robotics",
                "label": "AI Robotics",
                "type": "topic",
                "parent": "ai"
            })
            
            # Add related subtopics
            roadmap['nodes'].append({
                "id": "machine_learning_robotics",
                "label": "ML for Robotics",
                "type": "subtopic",
                "parent": "ai_robotics"
            })
            
            roadmap['nodes'].append({
                "id": "computer_vision_robotics",
                "label": "Computer Vision for Robotics",
                "type": "subtopic",
                "parent": "ai_robotics"
            })
            
            roadmap['nodes'].append({
                "id": "robot_control",
                "label": "Robot Control Systems",
                "type": "subtopic",
                "parent": "ai_robotics"
            })
            
            # Add node details
            roadmap['nodeDetails']["ai_robotics"] = {
                "content": "AI Robotics combines artificial intelligence with robotics to create intelligent machines that can perform tasks in the physical world.",
                "resources": [
                    "MIT OpenCourseWare Robotics",
                    "Stanford AI for Robotics",
                    "Robotics: Computational Motion Planning"
                ]
            }
            
            roadmap['nodeDetails']["machine_learning_robotics"] = {
                "content": "Applying machine learning techniques to teach robots to learn from data and improve their performance over time.",
                "resources": [
                    "Reinforcement Learning for Robotics",
                    "Neural Networks for Robot Control"
                ]
            }
            
            roadmap['nodeDetails']["computer_vision_robotics"] = {
                "content": "Enabling robots to perceive and understand their environment through visual data processing.",
                "resources": [
                    "OpenCV for Robotics",
                    "ROS Computer Vision Tutorials"
                ]
            }
            
            roadmap['nodeDetails']["robot_control"] = {
                "content": "Systems and algorithms for controlling robot movements, interactions, and tasks.",
                "resources": [
                    "ROS (Robot Operating System)",
                    "Control Systems Engineering"
                ]
            }
    
    # Check for frontend development keywords
    elif any(keyword in message_lower for keyword in ['frontend', 'front end', 'ui', 'interface', 'react', 'vue', 'angular']):
        # Frontend frameworks
        if any(keyword in message_lower for keyword in ['react', 'reactjs']):
            if not any(node['id'] == 'react' for node in roadmap['nodes']):
                roadmap['nodes'].append({
                    "id": "react",
                    "label": "React",
                    "type": "subtopic",
                    "parent": "frontend"
                })
                
                roadmap['nodeDetails']["react"] = {
                    "content": "React is a JavaScript library for building user interfaces, particularly single-page applications.",
                    "resources": [
                        "React Documentation",
                        "React - The Complete Guide (Udemy)",
                        "Scrimba React Course"
                    ]
                }
        
        if any(keyword in message_lower for keyword in ['vue', 'vuejs']):
            if not any(node['id'] == 'vue' for node in roadmap['nodes']):
                roadmap['nodes'].append({
                    "id": "vue",
                    "label": "Vue.js",
                    "type": "subtopic",
                    "parent": "frontend"
                })
                
                roadmap['nodeDetails']["vue"] = {
                    "content": "Vue.js is a progressive JavaScript framework for building user interfaces and single-page applications.",
                    "resources": [
                        "Vue.js Documentation",
                        "Vue Mastery",
                        "Vue School"
                    ]
                }
        
        if any(keyword in message_lower for keyword in ['angular', 'angularjs']):
            if not any(node['id'] == 'angular' for node in roadmap['nodes']):
                roadmap['nodes'].append({
                    "id": "angular",
                    "label": "Angular",
                    "type": "subtopic",
                    "parent": "frontend"
                })
                
                roadmap['nodeDetails']["angular"] = {
                    "content": "Angular is a platform and framework for building single-page client applications using HTML and TypeScript.",
                    "resources": [
                        "Angular Documentation",
                        "Angular University",
                        "Pluralsight Angular Courses"
                    ]
                }
    
    # Check for backend development keywords
    elif any(keyword in message_lower for keyword in ['backend', 'back end', 'server', 'database', 'api', 'node', 'express', 'django', 'flask']):
        # Backend frameworks
        if any(keyword in message_lower for keyword in ['node', 'nodejs', 'express', 'expressjs']):
            if not any(node['id'] == 'node_express' for node in roadmap['nodes']):
                roadmap['nodes'].append({
                    "id": "node_express",
                    "label": "Node.js & Express",
                    "type": "subtopic",
                    "parent": "backend"
                })
                
                roadmap['nodeDetails']["node_express"] = {
                    "content": "Node.js is a JavaScript runtime for server-side programming, and Express is a minimal and flexible Node.js web application framework.",
                    "resources": [
                        "Node.js Documentation",
                        "Express.js Documentation",
                        "The Complete Node.js Developer Course"
                    ]
                }
        
        if any(keyword in message_lower for keyword in ['django', 'python web']):
            if not any(node['id'] == 'django' for node in roadmap['nodes']):
                roadmap['nodes'].append({
                    "id": "django",
                    "label": "Django",
                    "type": "subtopic",
                    "parent": "backend"
                })
                
                roadmap['nodeDetails']["django"] = {
                    "content": "Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design.",
                    "resources": [
                        "Django Documentation",
                        "Django for Beginners",
                        "Django REST Framework"
                    ]
                }
    
    return roadmap

if __name__ == '__main__':
    app.run(debug=True, port=5000)
