from flask import Flask, send_from_directory, request, jsonify
import os
import json
import uuid
from dotenv import load_dotenv
import groq
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')

# Initialize Groq client if API key is available
groq_client = None
groq_api_key = os.getenv("GROQ_API_KEY")
if groq_api_key:
    groq_client = groq.Client(api_key=groq_api_key)
    print("Groq API client initialized successfully")
else:
    print("Warning: GROQ_API_KEY not found in environment variables")

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
    
    # If user doesn't have a roadmap yet, create empty one
    if user_id not in roadmaps:
        roadmaps[user_id] = create_empty_roadmap()
    
    return jsonify(roadmaps[user_id])

@app.route('/api/chat', methods=['POST'])
def process_chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    user_message = data['message']
    user_id = request.cookies.get('user_id', str(uuid.uuid4()))
    
    print(f"Processing message from user {user_id}: {user_message}")
    
    # Initialize chat history if needed
    if user_id not in chat_history:
        chat_history[user_id] = [
            {"role": "system", "content": "You are a friendly, empathetic career guidance expert at CareerPath.AI. Your style is concise, warm, and supportive. You specialize in technology career pathways."}
        ]
    
    # Add user message to history
    chat_history[user_id].append({"role": "user", "content": user_message})
    
    # Get or create roadmap
    if user_id not in roadmaps:
        roadmaps[user_id] = create_empty_roadmap()
    
    # Store current node IDs to identify new ones later
    current_node_ids = [node["id"] for node in roadmaps[user_id]["nodes"]]
    
    # Process the message and update the roadmap
    try:
        # If Groq client is available, use LLM to generate response and update roadmap
        if groq_client:
            print("Using Groq API for response generation")
            # First, generate the AI response
            chat_response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=chat_history[user_id],
                temperature=0.7,
                max_tokens=800
            )
            
            ai_response = chat_response.choices[0].message.content
            chat_history[user_id].append({"role": "assistant", "content": ai_response})
            print(f"Generated AI response: {ai_response[:100]}...")
            
            # Now, ask the LLM to update the roadmap based on the user message
            roadmap_update_prompt = f"""
            As a career advisor AI, analyze this user message and UPDATE the existing career roadmap by ADDING new nodes.
            
            User message: "{user_message}"
            
            Current roadmap: {json.dumps(roadmaps[user_id])}
            
            CRITICAL INSTRUCTIONS:
            1. NEVER replace or remove existing nodes, ONLY ADD NEW ONES
            2. Make sure new nodes connect to the EXISTING structure
            3. Each node must have: id, label, type, and parent fields
            4. Node types: root, category, topic, subtopic, resource
            5. Add EXTREMELY DETAILED content for each new node in nodeDetails including:
               - Detailed description (150+ words)
               - Required skills
               - Career progression paths
               - Salary expectations
               - Real course links (Coursera, edX, Udemy, etc.)
               - Sample projects to practice
               - Books or resources to read
            6. Focus on depth rather than breadth
            7. Ensure proper parent-child connections to make a coherent tree
            8. Use highly specific node IDs to avoid collisions (e.g., 'web_dev_frontend_react')
            
            Return ONLY the complete updated roadmap JSON without any explanation.
            """
            
            print("Generating roadmap update...")
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
                print(f"Received roadmap update: {roadmap_text[:100]}...")
                
                # Extract JSON from possible markdown formatting
                if "```json" in roadmap_text:
                    roadmap_text = roadmap_text.split("```json")[1].split("```")[0].strip()
                elif "```" in roadmap_text:
                    roadmap_text = roadmap_text.split("```")[1].split("```")[0].strip()
                
                # Parse the updated roadmap
                updated_roadmap = json.loads(roadmap_text)
                
                # Ensure we're not losing existing nodes
                # Get existing node IDs for comparison
                existing_node_ids = {node["id"] for node in roadmaps[user_id]["nodes"]}
                updated_node_ids = {node["id"] for node in updated_roadmap["nodes"]}
                
                # If any existing nodes are missing, something went wrong
                if not existing_node_ids.issubset(updated_node_ids):
                    print("Warning: Some existing nodes are missing in the update!")
                    print(f"Missing nodes: {existing_node_ids - updated_node_ids}")
                    
                    # Fallback: manually merge the roadmaps rather than replacing
                    merged_nodes = roadmaps[user_id]["nodes"].copy()
                    merged_node_details = roadmaps[user_id]["nodeDetails"].copy()
                    
                    # Add only new nodes from the update
                    new_nodes = [node for node in updated_roadmap["nodes"] if node["id"] not in existing_node_ids]
                    merged_nodes.extend(new_nodes)
                    
                    # Add new node details
                    for node_id, details in updated_roadmap["nodeDetails"].items():
                        if node_id not in merged_node_details:
                            merged_node_details[node_id] = details
                    
                    # Create properly merged roadmap
                    roadmaps[user_id] = {
                        "nodes": merged_nodes,
                        "nodeDetails": merged_node_details
                    }
                    print(f"Manually merged {len(new_nodes)} new nodes into the roadmap")
                else:
                    # The update looks good, use it
                    roadmaps[user_id] = updated_roadmap
                    print("Roadmap updated successfully")
            except Exception as e:
                print(f"Error updating roadmap from LLM response: {e}")
                print(f"LLM response: {roadmap_text}")
                # If parsing fails, use fallback update
                roadmaps[user_id] = update_roadmap_heuristic(roadmaps[user_id], user_message)
        else:
            print("No Groq API key found, using fallback response generation")
            # Fallback for when Groq API is not available
            ai_response = "I'm analyzing your career interests. Let me update your roadmap with some relevant paths."
            chat_history[user_id].append({"role": "assistant", "content": ai_response})
            roadmaps[user_id] = update_roadmap_heuristic(roadmaps[user_id], user_message)
        
        # Identify new nodes
        new_node_ids = [node["id"] for node in roadmaps[user_id]["nodes"] if node["id"] not in current_node_ids]
        print(f"Added {len(new_node_ids)} new nodes to the roadmap")
        
        return jsonify({
            "response": ai_response,
            "roadmap": roadmaps[user_id],
            "newNodes": new_node_ids
        })
    
    except Exception as e:
        print(f"Error processing chat: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "response": "I'm sorry, I encountered an error. Please try again."}), 500

def create_empty_roadmap():
    """Create an empty roadmap with just a root node"""
    return {
        "nodes": [
            {"id": "root", "label": "Your Career Path", "type": "root", "parent": None}
        ],
        "nodeDetails": {
            "root": {
                "content": "This is the starting point of your personalized career roadmap. Chat with me about your interests to build your path!",
                "resources": ["Let's start by discussing your interests and goals."]
            }
        }
    }

def update_roadmap_heuristic(roadmap, message):
    """
    Fallback method to update roadmap based on simple keyword matching
    Used when LLM is not available or fails
    """
    message_lower = message.lower()
    
    # Check for technology fields
    if any(tech in message_lower for tech in ['programming', 'coding', 'developer', 'software']):
        # Add Software Development if not present
        if not any(node['id'] == 'software_dev' for node in roadmap['nodes']):
            roadmap['nodes'].append({
                "id": "software_dev",
                "label": "Software Development",
                "type": "category",
                "parent": "root"
            })
            
            roadmap['nodeDetails']["software_dev"] = {
                "content": "Software development is the process of conceiving, specifying, designing, programming, documenting, testing, and bug fixing involved in creating and maintaining applications, frameworks, or other software components.",
                "resources": [
                    "freeCodeCamp",
                    "The Odin Project",
                    "MIT OpenCourseWare"
                ]
            }
            
            # Add some common programming paths
            roadmap['nodes'].append({
                "id": "frontend_dev",
                "label": "Frontend Development",
                "type": "topic",
                "parent": "software_dev"
            })
            
            roadmap['nodeDetails']["frontend_dev"] = {
                "content": "Frontend development focuses on creating the user interface and experience of a website or application.",
                "resources": [
                    "MDN Web Docs",
                    "Frontend Masters",
                    "CSS-Tricks"
                ]
            }
            
            roadmap['nodes'].append({
                "id": "backend_dev",
                "label": "Backend Development",
                "type": "topic",
                "parent": "software_dev"
            })
            
            roadmap['nodeDetails']["backend_dev"] = {
                "content": "Backend development focuses on server-side logic, databases, and application architecture.",
                "resources": [
                    "Node.js Documentation",
                    "Django Documentation",
                    "SQL Tutorial"
                ]
            }
    
    # Check for AI/ML interest
    if any(ai_term in message_lower for ai_term in ['ai', 'artificial intelligence', 'machine learning', 'ml']):
        # Add AI/ML if not present
        if not any(node['id'] == 'ai_ml' for node in roadmap['nodes']):
            roadmap['nodes'].append({
                "id": "ai_ml",
                "label": "AI & Machine Learning",
                "type": "category",
                "parent": "root"
            })
            
            roadmap['nodeDetails']["ai_ml"] = {
                "content": "Artificial Intelligence and Machine Learning focus on creating systems that can learn from data, identify patterns, and make decisions with minimal human intervention.",
                "resources": [
                    "Coursera Machine Learning",
                    "Fast.ai",
                    "DeepLearning.AI"
                ]
            }
            
            # Add common AI/ML paths
            roadmap['nodes'].append({
                "id": "ml_fundamentals",
                "label": "ML Fundamentals",
                "type": "topic",
                "parent": "ai_ml"
            })
            
            roadmap['nodeDetails']["ml_fundamentals"] = {
                "content": "Learn the basics of machine learning algorithms, techniques, and applications.",
                "resources": [
                    "Andrew Ng's Coursera Course",
                    "Elements of Statistical Learning",
                    "Kaggle Learn"
                ]
            }
    
    # Check for data science interest
    if any(data_term in message_lower for data_term in ['data', 'analytics', 'statistics', 'visualization']):
        # Add Data Science if not present
        if not any(node['id'] == 'data_science' for node in roadmap['nodes']):
            roadmap['nodes'].append({
                "id": "data_science",
                "label": "Data Science",
                "type": "category",
                "parent": "root"
            })
            
            roadmap['nodeDetails']["data_science"] = {
                "content": "Data Science combines domain expertise, programming skills, and math/statistics knowledge to extract meaningful insights from data.",
                "resources": [
                    "DataCamp",
                    "Kaggle",
                    "R for Data Science"
                ]
            }
            
            # Add common data science paths
            roadmap['nodes'].append({
                "id": "data_analysis",
                "label": "Data Analysis",
                "type": "topic",
                "parent": "data_science"
            })
            
            roadmap['nodeDetails']["data_analysis"] = {
                "content": "Data Analysis involves inspecting, cleaning, transforming, and modeling data to discover useful information and support decision-making.",
                "resources": [
                    "Python for Data Analysis",
                    "SQL for Data Analysis",
                    "Tableau Public"
                ]
            }
    
    return roadmap

if __name__ == '__main__':
    print("Starting CareerPath.AI server...")
    app.run(debug=True, port=9090)
