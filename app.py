import os
import json
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

# Force load environment variables at the very beginning
load_dotenv()

# Debug environment variables
groq_api_key = os.getenv("GROQ_API_KEY")
print(f"\n======== FLASK APP STARTUP - ENVIRONMENT CHECK ========")
print(f"GROQ_API_KEY found! Key starts with: {groq_api_key[:5]}...") if groq_api_key else print("\nCRITICAL ERROR: GROQ_API_KEY NOT FOUND!\n")
print(f"Current working directory: {os.getcwd()}")
print(f"ENV file exists: {os.path.exists('.env')}")
print(f"ENV variables loaded: {bool(load_dotenv())}")
print("====================================================\n")

# Import roadmap generator
from roadmap_generator import RoadmapGenerator
from roadmap_integration import update_roadmap_with_dynamic_content, initialize_roadmap_cache
from roadmap_knowledge_customizer import update_roadmap_with_knowledge_level

# Import LLM chat handler
from llm_chat import LLMChatHandler

# Import roadmap knowledge customizer
from roadmap_knowledge_customizer import update_roadmap_with_knowledge_level

# Sample roadmap data
sample_roadmap = {
    'id': 'root',
    'title': 'Career Path',
    'type': 'ROOT',
    'content': 'Your personalized career path roadmap',
    'children': [
        {
            'id': 'cs',
            'title': 'Computer Science',
            'type': 'CATEGORY',
            'content': 'Computer Science career paths and specializations',
            'children': [
                {
                    'id': 'ai',
                    'title': 'AI Engineer',
                    'type': 'CATEGORY',
                    'content': 'Career path: AI Engineer',
                    'children': [
                        {
                            'id': 'what_is_ai',
                            'title': 'What is AI Engineer',
                            'type': 'TOPIC',
                            'content': 'AI Engineers develop and implement AI and machine learning solutions.',
                            'resources': ['https://www.coursera.org/articles/ai-engineer'],
                            'children': []
                        }
                    ]
                }
            ]
        }
    ]
}

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-for-careerpath-ai')

# Initialize roadmap cache on startup
initialize_roadmap_cache()

# Serve index.html as the main route
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Test endpoint to directly call the Groq API
@app.route('/test-api')
def test_api():
    try:
        print("\n============ API TEST ENDPOINT CALLED ============")
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key not found'
            })
            
        # Initialize client
        client = Groq(api_key=api_key)
        
        # Make a simple API call
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello and introduce yourself briefly."}
            ],
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=100
        )
        
        # Return the response
        return jsonify({
            'success': True,
            'response': response.choices[0].message.content
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })

# Session data to track conversation state
user_sessions = {}

# Check if API key is loaded
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("WARNING: GROQ_API_KEY not found in environment variables!")
    print("Please make sure your .env file contains: GROQ_API_KEY=your_key_here")
else:
    print(f"Groq API key found! Key starts with: {groq_api_key[:5]}...")

# Initialize the LLM chat handler
llm_chat_handler = LLMChatHandler()

# Chat endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        print("\n============ CHAT ENDPOINT CALLED ============")
        print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get the user message
        data = request.get_json()
        user_message = data.get('message', '').strip()
        print(f"Received message: {user_message}")
        
        if not user_message:
            return jsonify({
                'response': 'I did not receive a message. Please try again.',
                'roadmap': empty_roadmap
            })
        
        # Get session ID or create a new one if needed
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            
        # Initialize conversation history if needed
        if 'conversation' not in session:
            session['conversation'] = []
            
        # Initialize interests if needed
        if 'interests' not in session:
            session['interests'] = []
            
        # Initialize roadmap if needed
        if 'roadmap' not in session:
            session['roadmap'] = empty_roadmap
            
        # Add the user message to conversation history
        session['conversation'].append({"role": "user", "content": user_message})
        print(f"Added message to conversation. Total messages: {len(session['conversation'])}")
        
        # Get the API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("ERROR: No API key available")
            return jsonify({
                'response': 'I cannot connect to my AI capabilities. Please check the API key.',
                'roadmap': session['roadmap']
            })
            
        # Create a direct Groq client with the API key
        print("Creating Groq client with API key")
        client = Groq(api_key=api_key)
        
        # Prepare the messages for the API call with clear instructions for conciseness
        messages = [
            {"role": "system", "content": "You are CareerPath.AI, a helpful career advisor who specializes in creating personalized learning roadmaps for agentic AI. Your goal is to understand the user's interests and skill level, then provide EXTREMELY CONCISE guidance and next steps. IMPORTANT: Keep all responses under 150 words total."}, 
            {"role": "system", "content": "RESPONSE FORMAT RULES:\n1) Use bullet points for lists\n2) Maximum 2-3 sentences per paragraph\n3) Only list 1-2 resources per topic\n4) Use markdown for formatting\n5) Focus on next actions, not explanations\n6) Be direct and specific"}
        ]
        
        # Add conversation history (limited to prevent context overflow)
        if len(session['conversation']) > 15:
            # Include the first message and the latest messages
            messages.append(session['conversation'][0])
            messages.extend(session['conversation'][-14:])
        else:
            messages.extend(session['conversation'])
            
        print(f"Sending {len(messages)} messages to Groq API")
        for i, msg in enumerate(messages):
            print(f"[{i}] {msg['role'].upper()}: {msg['content'][:50]}...")
            
        try:
            # Make the API call
            print("Making API call with model: llama3-70b-8192")
            response = client.chat.completions.create(
                messages=messages,
                model="llama3-70b-8192",  # Use a known working model
                temperature=0.7,
                max_tokens=800,
                top_p=1
            )
            
            # Extract response
            bot_response = response.choices[0].message.content
            print(f"API response received: {bot_response[:100]}...")
            
            # Add bot response to conversation history
            session['conversation'].append({"role": "assistant", "content": bot_response})
            
            # Extract interests and knowledge level from the user message (more sophisticated)
            interests = []
            knowledge_level = 'beginner'  # Default level
            
            # Check for agentic AI specific interest
            if 'agentic ai' in user_message.lower() or ('agentic' in user_message.lower() and 'ai' in user_message.lower()):
                interests.append('agentic-ai')
                
                # Determine knowledge level for agentic AI based on mentioned concepts
                advanced_concepts = ['rag', 'vector embeddings', 'multi-agent systems', 'tree of thought', 'reasoning', 'llm agents']
                intermediate_concepts = ['frameworks', 'langchain', 'tools', 'agent memory', 'workflows']
                beginner_concepts = ['what is', 'how to', 'basics', 'fundamentals', 'introduction']
                
                # Check for knowledge indicators in the message
                user_msg_lower = user_message.lower()
                
                # Check if user explicitly mentions their knowledge level
                if 'advanced' in user_msg_lower or 'expert' in user_msg_lower or any(concept in user_msg_lower for concept in advanced_concepts):
                    knowledge_level = 'advanced'
                    print(f"Detected ADVANCED knowledge level for agentic AI")
                elif 'intermediate' in user_msg_lower or any(concept in user_msg_lower for concept in intermediate_concepts):
                    knowledge_level = 'intermediate'
                    print(f"Detected INTERMEDIATE knowledge level for agentic AI")
                elif any(concept in user_msg_lower for concept in beginner_concepts):
                    knowledge_level = 'beginner'
                    print(f"Detected BEGINNER knowledge level for agentic AI")
                
                print(f"Knowledge level set to: {knowledge_level} for agentic AI")
            
            # General AI interest detection
            elif 'ai' in user_message.lower() or 'artificial intelligence' in user_message.lower() or 'machine learning' in user_message.lower():
                interests.append('ai')
            
            # Other domains (for future expansion)
            if 'computer science' in user_message.lower() or 'programming' in user_message.lower():
                interests.append('computer science')
            if 'web development' in user_message.lower() or 'web' in user_message.lower():
                interests.append('web development')
            if 'data science' in user_message.lower() or 'data' in user_message.lower():
                interests.append('data science')
                
            # Store knowledge level in session
            if 'knowledge_levels' not in session:
                session['knowledge_levels'] = {}
            
            # Update knowledge level for detected interests
            if interests and interests[0] == 'agentic-ai':
                session['knowledge_levels']['agentic-ai'] = knowledge_level
                
            # Update the interests in the session
            for interest in interests:
                if interest not in session['interests']:
                    session['interests'].append(interest)
                    
            # ALWAYS update the roadmap with every message to ensure it persists
            try:
                # First, check for keywords that might indicate knowledge level changes
                user_msg_lower = user_message.lower()
                roadmap_keywords = {
                    'beginner': ['beginner', 'basics', 'start', 'new to', 'introduction', 'fundamentals'],
                    'intermediate': ['intermediate', 'already know', 'familiar with', 'experience with', 'worked with', 'prompt engineering', 'frameworks'],
                    'advanced': ['advanced', 'expert', 'rag', 'vector embeddings', 'multi-agent systems', 'tree of thought']
                }
                
                # Initialize with previous interests or empty list
                if 'interests' not in session:
                    session['interests'] = []
                
                # Add new detected interests
                for interest in interests:
                    if interest not in session['interests']:
                        session['interests'].append(interest)
                
                # Initialize knowledge levels dictionary if needed
                if 'knowledge_levels' not in session:
                    session['knowledge_levels'] = {}
                
                # Parse this specific message for knowledge level indicators
                detected_level = None
                # Check for specific requests for roadmap changes
                is_roadmap_request = 'roadmap' in user_msg_lower or 'next steps' in user_msg_lower
                
                # Detect knowledge level from current message
                for level, keywords in roadmap_keywords.items():
                    if any(keyword in user_msg_lower for keyword in keywords):
                        detected_level = level
                        print(f"Detected {level} knowledge level from message")
                        break
                
                # If we found a new knowledge level, update it
                if detected_level:
                    if 'agentic-ai' in session['interests'] or 'ai' in session['interests']:
                        session['knowledge_levels']['agentic-ai'] = detected_level
                
                # ALWAYS create a roadmap even if we don't have explicit interests yet
                # This ensures the roadmap is always shown
                current_interests = session.get('interests', [])
                
                # Default to AI interest if nothing specified yet but they requested a roadmap
                if (not current_interests) and is_roadmap_request:
                    current_interests = ['agentic-ai']
                    session['interests'] = current_interests
                
                # If we have interests, create/update the roadmap
                if current_interests:
                    # Get current knowledge level (default to beginner if not set)
                    current_knowledge_level = 'beginner'
                    if 'knowledge_levels' in session:
                        current_knowledge_level = session['knowledge_levels'].get('agentic-ai', 'beginner')
                    
                    print(f"Generating roadmap with interests: {current_interests}, level: {current_knowledge_level}")
                    
                    # Generate a fresh tailored roadmap
                    updated_roadmap = update_roadmap_with_knowledge_level(
                        empty_roadmap,  # Start fresh each time 
                        current_interests,
                        current_knowledge_level
                    )
                    
                    # ALWAYS save the updated roadmap to session
                    session['roadmap'] = updated_roadmap
                    print(f"Roadmap updated successfully with {len(updated_roadmap.get('children', []))} top-level nodes")
                else:
                    # If no interests detected yet, use empty roadmap
                    session['roadmap'] = empty_roadmap
            except Exception as roadmap_error:
                print(f"Error updating roadmap: {str(roadmap_error)}")
                import traceback
                print(traceback.format_exc())
            
            # Return the response to the frontend
            return jsonify({
                'response': bot_response,
                'roadmap': session['roadmap'],
                'session_id': session['session_id']
            })
            
        except Exception as api_error:
            print(f"Error making API call: {str(api_error)}")
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'response': "I'm sorry, I encountered an error connecting to my AI capabilities. Please try again.",
                'roadmap': session['roadmap'],
                'session_id': session['session_id']
            })
                
    except Exception as outer_e:
        import traceback
        print(f"\n❌ CRITICAL ERROR in chat endpoint: {str(outer_e)}")
        print(traceback.format_exc())
        
        # Return a friendly error message
        return jsonify({
            'response': "I'm sorry, I encountered an error processing your request. Please try again.",
            'roadmap': empty_roadmap
        })

# Legacy keyword-based interest extraction (now used as fallback in LLMChatHandler)
# This is kept for reference but no longer directly used
def extract_interests_legacy(message):
    interests = []
    keywords = {
        'computer science': ['programming', 'code', 'software', 'developer', 'computer science', 'coding'],
        'ai': ['artificial intelligence', 'ai', 'machine learning', 'ml', 'data science', 'neural networks'],
        'web development': ['web', 'frontend', 'backend', 'fullstack', 'html', 'css', 'javascript'],
        'data science': ['data', 'analytics', 'statistics', 'visualization', 'big data'],
        'cybersecurity': ['security', 'cyber', 'hacking', 'encryption', 'privacy', 'network security'],
        'mobile development': ['mobile', 'app', 'android', 'ios', 'flutter', 'react native'],
        'game development': ['game', 'gaming', 'unity', 'unreal', '3d', 'game design'],
        'cloud computing': ['cloud', 'aws', 'azure', 'devops', 'infrastructure', 'serverless']
    }
    
    message_lower = message.lower()
    for field, terms in keywords.items():
        if any(term in message_lower for term in terms):
            interests.append(field)
    
    return interests

# Update or create roadmap based on identified interests
def update_roadmap_based_on_interests(current_roadmap, interests):
    # If no interests yet, return current roadmap
    if not interests:
        return current_roadmap
    
    # Start with root node if roadmap is empty
    if not current_roadmap or 'children' not in current_roadmap:
        current_roadmap = {
            'id': 'root',
            'title': 'Your Career Path',
            'type': 'ROOT',
            'content': 'Your personalized career path roadmap',
            'children': []
        }
    
    # First, update with dynamic content from developer roadmaps
    current_roadmap = update_roadmap_with_dynamic_content(current_roadmap, interests)
    
    # Then add our predefined career path information for topics not covered in roadmaps
    # Career path definitions with detailed information
    career_paths = {
        'computer science': {
            'id': 'cs',
            'title': 'Computer Science',
            'type': 'CATEGORY',
            'content': 'Computer Science is the study of computers and computational systems, including their theory, design, development, and application. It encompasses theoretical studies, engineering design, and development of computational approaches.',
            'resources': [
                'https://www.coursera.org/browse/computer-science',
                'https://www.edx.org/learn/computer-science'
            ],
            'children': [
                {
                    'id': 'software_engineering',
                    'title': 'Software Engineering',
                    'type': 'TOPIC',
                    'content': 'Software engineering is the application of engineering principles to the design, development, and maintenance of software. Software engineers create applications used on computers, tech devices, and networks.',
                    'resources': [
                        'https://www.coursera.org/professional-certificates/meta-back-end-developer',
                        'https://www.codecademy.com/learn/paths/computer-science'
                    ],
                    'children': []
                },
                {
                    'id': 'algorithms',
                    'title': 'Algorithms & Data Structures',
                    'type': 'TOPIC',
                    'content': 'Algorithms are step-by-step procedures for solving problems, while data structures organize and store data. Together, they form the foundation of computer science and efficient programming.',
                    'resources': [
                        'https://www.coursera.org/learn/algorithms-part1',
                        'https://leetcode.com/'
                    ],
                    'children': []
                },
                {
                    'id': 'databases',
                    'title': 'Databases',
                    'type': 'TOPIC',
                    'content': 'Database systems organize, store, and retrieve data efficiently. Skills in this area include SQL, database design, normalization, and working with both relational and NoSQL databases.',
                    'resources': [
                        'https://www.postgresql.org/docs/current/tutorial.html',
                        'https://university.mongodb.com/'
                    ],
                    'children': []
                }
            ]
        },
        'ai': {
            'id': 'ai',
            'title': 'Artificial Intelligence',
            'type': 'CATEGORY',
            'content': 'Artificial Intelligence (AI) involves creating systems capable of performing tasks that typically require human intelligence. This includes learning, reasoning, problem-solving, perception, and language understanding.',
            'resources': [
                'https://www.coursera.org/learn/ai-for-everyone',
                'https://www.edx.org/search?q=artificial+intelligence'
            ],
            'children': [
                {
                    'id': 'machine_learning',
                    'title': 'Machine Learning',
                    'type': 'TOPIC',
                    'content': 'Machine Learning is a subset of AI that focuses on building systems that learn from data. It includes supervised learning, unsupervised learning, and reinforcement learning techniques.',
                    'resources': [
                        'https://www.coursera.org/learn/machine-learning',
                        'https://www.kaggle.com/learn/intro-to-machine-learning'
                    ],
                    'children': [
                        {
                            'id': 'deep_learning',
                            'title': 'Deep Learning',
                            'type': 'SUBTOPIC',
                            'content': "Deep Learning uses neural networks with many layers (deep neural networks) to analyze various factors of data. It's particularly powerful for image and speech recognition, natural language processing, and more.",
                            'resources': [
                                'https://www.deeplearning.ai/',
                                'https://www.tensorflow.org/tutorials'
                            ],
                            'children': []
                        }
                    ]
                },
                {
                    'id': 'nlp',
                    'title': 'Natural Language Processing',
                    'type': 'TOPIC',
                    'content': 'Natural Language Processing (NLP) focuses on the interaction between computers and human language. It involves enabling computers to understand, interpret, and generate human language in a valuable way.',
                    'resources': [
                        'https://www.coursera.org/specializations/natural-language-processing',
                        'https://huggingface.co/course/chapter1/1'
                    ],
                    'children': []
                },
                {
                    'id': 'computer_vision',
                    'title': 'Computer Vision',
                    'type': 'TOPIC',
                    'content': 'Computer Vision enables computers to derive meaningful information from digital images, videos, and other visual inputs. Applications include image recognition, object detection, and scene reconstruction.',
                    'resources': [
                        'https://www.coursera.org/specializations/deep-learning',
                        'https://opencv.org/'
                    ],
                    'children': []
                }
            ]
        },
        'web development': {
            'id': 'web_dev',
            'title': 'Web Development',
            'type': 'CATEGORY',
            'content': 'Web development involves creating and maintaining websites and web applications. It encompasses everything from simple static webpages to complex web applications, e-commerce sites, and social network services.',
            'resources': [
                'https://developer.mozilla.org/en-US/docs/Learn',
                'https://www.theodinproject.com/'
            ],
            'children': [
                {
                    'id': 'frontend',
                    'title': 'Frontend Development',
                    'type': 'TOPIC',
                    'content': 'Frontend development focuses on what users see and interact with in a browser. It involves HTML for structure, CSS for presentation, and JavaScript for functionality, along with various frameworks and libraries.',
                    'resources': [
                        'https://www.freecodecamp.org/learn/responsive-web-design/',
                        'https://reactjs.org/tutorial/tutorial.html'
                    ],
                    'children': []
                },
                {
                    'id': 'backend',
                    'title': 'Backend Development',
                    'type': 'TOPIC',
                    'content': 'Backend development involves server-side logic, database interactions, APIs, architecture, and server configuration. It powers the frontend and manages data processing and storage.',
                    'resources': [
                        'https://nodejs.org/en/learn',
                        'https://www.djangoproject.com/start/'
                    ],
                    'children': []
                }
            ]
        },
        'data science': {
            'id': 'data_science',
            'title': 'Data Science',
            'type': 'CATEGORY',
            'content': 'Data Science combines domain expertise, programming skills, and knowledge of math and statistics to extract meaningful insights from data. It involves analyzing complex data to help organizations make informed decisions.',
            'resources': [
                'https://www.coursera.org/professional-certificates/ibm-data-science',
                'https://www.datacamp.com/tracks/data-scientist-with-python'
            ],
            'children': [
                {
                    'id': 'data_analysis',
                    'title': 'Data Analysis',
                    'type': 'TOPIC',
                    'content': 'Data Analysis involves inspecting, cleansing, transforming, and modeling data to discover useful information, inform conclusions, and support decision-making. Tools include Python, R, SQL, and Excel.',
                    'resources': [
                        'https://www.kaggle.com/learn/pandas',
                        'https://www.datacamp.com/courses/introduction-to-data-science-in-python'
                    ],
                    'children': []
                },
                {
                    'id': 'data_visualization',
                    'title': 'Data Visualization',
                    'type': 'TOPIC',
                    'content': 'Data Visualization is the graphical representation of information and data. It uses visual elements like charts, graphs, and maps to provide an accessible way to understand trends, outliers, and patterns in data.',
                    'resources': [
                        'https://www.tableau.com/learn/training',
                        'https://d3js.org/'
                    ],
                    'children': []
                }
            ]
        },
        'cybersecurity': {
            'id': 'cybersecurity',
            'title': 'Cybersecurity',
            'type': 'CATEGORY',
            'content': 'Cybersecurity involves protecting systems, networks, and programs from digital attacks. These attacks often aim to access, change, or destroy sensitive information; extort money; or interrupt normal business processes.',
            'resources': [
                'https://www.coursera.org/professional-certificates/google-cybersecurity',
                'https://www.sans.org/cyberaces/'
            ],
            'children': [
                {
                    'id': 'network_security',
                    'title': 'Network Security',
                    'type': 'TOPIC',
                    'content': 'Network Security focuses on protecting the usability and integrity of your network and data. It includes both hardware and software technologies, and effective network security manages access to the network.',
                    'resources': [
                        'https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html',
                        'https://www.comptia.org/certifications/security'
                    ],
                    'children': []
                },
                {
                    'id': 'ethical_hacking',
                    'title': 'Ethical Hacking',
                    'type': 'TOPIC',
                    'content': 'Ethical Hacking involves identifying weaknesses in computer systems and networks to prevent malicious attacks. Ethical hackers use their skills to improve security by finding and fixing vulnerabilities.',
                    'resources': [
                        'https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/',
                        'https://www.hackthebox.com/'
                    ],
                    'children': []
                }
            ]
        }
    }

    # Add each interest as a separate node if it doesn't exist yet
    existing_ids = [child['id'] for child in current_roadmap['children']]
    
    for interest in interests:
        if interest in career_paths:
            career_info = career_paths[interest]
            
            # Check if this career path is already in the roadmap
            if career_info['id'] not in existing_ids:
                current_roadmap['children'].append(career_info)
                existing_ids.append(career_info['id'])
    
    return current_roadmap

def generate_initial_roadmap():
    return {
        'id': 'root',
        'title': 'Your Career Path',
        'type': 'ROOT',
        'content': 'Your personalized career path roadmap',
        'children': []
    }

# Legacy response generation functions - kept for reference but no longer directly used

# These functions have been replaced by the LLMChatHandler which provides
# more personalized, context-aware responses using the Groq API

# Initialize Groq client
client = Groq()
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("ERROR: GROQ_API_KEY not set for global client!")
else:
    client.api_key = groq_api_key

# In-memory storage for user sessions (MVP)
user_sessions: Dict[str, Dict[str, Any]] = {}

# Node types for the roadmap visualization
NODE_TYPES = {
    "ROOT": "rectangle",
    "CATEGORY": "diamond",
    "TOPIC": "rectangle",
    "SUBTOPIC": "rectangle",
    "DECISION": "circle",
}

# Define a roadmap node structure
class RoadmapNode:
    def __init__(self, id: str, title: str, node_type: str, content: str = "", resources: List[str] = None, parent_id: Optional[str] = None):
        self.id = id
        self.title = title
        self.node_type = node_type
        self.content = content
        self.resources = resources or []
        self.parent_id = parent_id
        self.children = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.node_type,
            "content": self.content,
            "resources": self.resources,
            "parent_id": self.parent_id,
            "children": [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoadmapNode':
        node = cls(
            id=data["id"],
            title=data["title"],
            node_type=data["type"],
            content=data.get("content", ""),
            resources=data.get("resources", []),
            parent_id=data.get("parent_id")
        )
        
        for child_data in data.get("children", []):
            child = cls.from_dict(child_data)
            node.children.append(child)
            
        return node
    
    def add_child(self, child: 'RoadmapNode') -> None:
        child.parent_id = self.id
        self.children.append(child)
        
    def find_node_by_id(self, node_id: str) -> Optional['RoadmapNode']:
        if self.id == node_id:
            return self
        
        for child in self.children:
            result = child.find_node_by_id(node_id)
            if result:
                return result
                
        return None

# Initial prompt for the AI assistant
INITIAL_PROMPT = """You are a friendly, empathetic career guidance expert at CareerPath.AI. Your style is concise, warm, and supportive.

Follow these guidelines strictly:
1. Keep your responses brief and to the point - use 1-3 short paragraphs maximum
2. Ask only one clear, focused question at a time
3. Be emotionally intelligent - recognize signs of frustration, uncertainty, or demotivation and respond with empathy
4. Provide actionable, practical steps for each career path you suggest
5. Tailor your advice to the user's specific circumstances, skills, and interests
6. When suggesting resources, be specific (books, courses, websites)
7. Use web search results to provide up-to-date information and relevant resources

When the user expresses negative emotions or doubts:
- Acknowledge their feelings first
- Offer reassurance and perspective
- Share a practical next step they can take

Maintain a conversational, friendly tone while being professional and direct."""

# Helper functions for the personalized roadmap feature
def get_user_id(session):
    # For MVP: use session id or fallback to a dummy id
    return str(session.id) if hasattr(session, "id") else "test_user"

def get_default_roadmap():
    """Create a default roadmap for new users based on image examples"""
    # Root node for the roadmap
    root = RoadmapNode(
        id=str(uuid.uuid4()),
        title="My Roadmap",
        node_type="ROOT",
        content="Your personalized career path roadmap"
    )
    
    # Add sample paths from the images
    cs_node = RoadmapNode(
        id=str(uuid.uuid4()),
        title="Computer Science",
        node_type="CATEGORY",
        content="Computer Science career paths and specializations"
    )
    root.add_child(cs_node)
    
    # Add career path options
    for path in ["Full Stack Developer", "AI Engineer", "Blockchain", "DevOps"]:
        path_node = RoadmapNode(
            id=str(uuid.uuid4()),
            title=path,
            node_type="CATEGORY",
            content=f"Career path: {path}"
        )
        cs_node.add_child(path_node)
        
        # Add special AI engineering path from the example
        if path == "AI Engineer":
            what_is_node = RoadmapNode(
                id=str(uuid.uuid4()),
                title="What is AI Engineer",
                node_type="TOPIC",
                content="AI Engineers develop and implement AI and machine learning solutions. They bridge the gap between data science and production systems.",
                resources=["https://www.coursera.org/articles/ai-engineer"]
            )
            path_node.add_child(what_is_node)
            
            decision_node = RoadmapNode(
                id=str(uuid.uuid4()),
                title="OR",
                node_type="DECISION",
                content="Choose a specialization"
            )
            what_is_node.add_child(decision_node)
            
            for option in ["AI", "ML"]:
                option_node = RoadmapNode(
                    id=str(uuid.uuid4()),
                    title=option,
                    node_type="TOPIC",
                    content=f"Focus on {option} specialization"
                )
                decision_node.add_child(option_node)
            
            tasks_node = RoadmapNode(
                id=str(uuid.uuid4()),
                title="Tasks of an AI Engineer",
                node_type="TOPIC",
                content="Key responsibilities and day-to-day tasks of an AI Engineer"
            )
            path_node.add_child(tasks_node)
            
            # Add subtopics for AI Engineer tasks
            for subtopic in ["Prompt Engineering", "Building Agents", "RAG", "Generative AI"]:
                subtopic_node = RoadmapNode(
                    id=str(uuid.uuid4()),
                    title=subtopic,
                    node_type="SUBTOPIC",
                    content=f"Learn about {subtopic} and its applications"
                )
                tasks_node.add_child(subtopic_node)
    
    # Add Machine Learning path from first image
    ml_node = RoadmapNode(
        id=str(uuid.uuid4()),
        title="Machine Learning",
        node_type="CATEGORY",
        content="Machine Learning learning path"
    )
    root.add_child(ml_node)
    
    foundation_node = RoadmapNode(
        id=str(uuid.uuid4()),
        title="Build a foundation in Python and statistics",
        node_type="TOPIC",
        content="Learn the fundamentals of Python programming and statistics for ML",
        resources=["Coursera"]
    )
    ml_node.add_child(foundation_node)
    
    applications_node = RoadmapNode(
        id=str(uuid.uuid4()),
        title="Explore real-world AI applications",
        node_type="TOPIC",
        content="Practical applications of AI in different domains",
        resources=["skin cancer classification", "neural networks", "fuzzy logic"]
    )
    foundation_node.add_child(applications_node)
    
    nn_node = RoadmapNode(
        id=str(uuid.uuid4()),
        title="Experiment with neural networks and CNNs",
        node_type="TOPIC",
        content="Hands-on practice with neural networks and convolutional neural networks",
        resources=["edX"]
    )
    applications_node.add_child(nn_node)
    
    return root

def get_or_create_roadmap(user_id):
    if user_id not in user_sessions:
        # Initialize with a default roadmap
        root_node = get_default_roadmap()
        user_sessions[user_id] = {
            "roadmap": root_node
        }
    return user_sessions[user_id]["roadmap"]

def update_roadmap(user_id, node_id, content, user_input=""):
    """Update an existing node in the roadmap or add a new one"""
    roadmap = get_or_create_roadmap(user_id)
    
    if node_id:
        # Find and update an existing node
        node = roadmap.find_node_by_id(node_id)
        if node:
            node.content = content
            return roadmap
    
    # If we didn't find the node or no node_id was provided,
    # add a new node to the root based on user input
    if user_input:
        new_id = str(uuid.uuid4())
        new_node = RoadmapNode(
            id=new_id,
            title=f"Explore: {user_input[:20]}...",
            node_type="TOPIC",
            content=content
        )
        roadmap.add_child(new_node)
    
    return roadmap

def add_child_node(user_id, parent_id, title, content, node_type="TOPIC", resources=None):
    """Add a child node to a specific parent node"""
    roadmap = get_or_create_roadmap(user_id)
    parent = roadmap.find_node_by_id(parent_id)
    
    if parent:
        new_id = str(uuid.uuid4())
        child = RoadmapNode(
            id=new_id,
            title=title,
            node_type=node_type,
            content=content,
            resources=resources or []
        )
        parent.add_child(child)
        return new_id
    return None

def generate_interactive_roadmap_html(roadmap_node):
    """Generate HTML/JavaScript for the interactive roadmap visualization"""
    # Convert the roadmap to a JSON structure for D3.js
    roadmap_data = roadmap_node.to_dict()
    json_data = json.dumps(roadmap_data)
    
    # Create the HTML with embedded D3.js visualization
    html = f"""
    <div id="roadmap-viz" style="width:100%; height:500px; overflow:hidden;"></div>
    
    <div id="node-details" class="node-details" style="display:none;">
        <h3 id="detail-title"></h3>
        <p id="detail-content"></p>
        <div id="detail-resources" class="node-resources"></div>
    </div>
    
    <script>
    // Roadmap data
    const roadmapData = {json_data};
    
    // Function to show node details
    function showNodeDetails(node) {{
        const detailsDiv = document.getElementById('node-details');
        const titleEl = document.getElementById('detail-title');
        const contentEl = document.getElementById('detail-content');
        const resourcesEl = document.getElementById('detail-resources');
        
        // Set content
        titleEl.textContent = node.title;
        contentEl.textContent = node.content || 'No detailed information available';
        
        // Clear previous resources
        resourcesEl.innerHTML = '';
        
        // Add resources if available
        if (node.resources && node.resources.length > 0) {{
            const resourcesTitle = document.createElement('h4');
            resourcesTitle.textContent = 'Resources';
            resourcesEl.appendChild(resourcesTitle);
            
            const resourcesList = document.createElement('ul');
            node.resources.forEach(resource => {{
                const li = document.createElement('li');
                if (resource.startsWith('http')) {{
                    const a = document.createElement('a');
                    a.href = resource;
                    a.target = '_blank';
                    a.textContent = resource;
                    li.appendChild(a);
                }} else {{
                    li.textContent = resource;
                }}
                resourcesList.appendChild(li);
            }});
            resourcesEl.appendChild(resourcesList);
        }}
        
        // Show the details
        detailsDiv.style.display = 'block';
    }}
    
    // When the DOM is loaded, render the roadmap
    document.addEventListener('DOMContentLoaded', function() {{
        renderRoadmap();
    }});
    
    // Just in case the script runs after DOM is loaded
    if (document.readyState === 'complete' || document.readyState === 'interactive') {{
        setTimeout(renderRoadmap, 1);
    }}
    
    function renderRoadmap() {{
        // Get container dimensions
        const container = document.getElementById('roadmap-viz');
        if (!container) return;
        
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        // Clear any existing content
        container.innerHTML = '';
        
        // Create SVG container
        const svg = d3.select('#roadmap-viz')
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', 'translate(40,40)');
        
        // Create hierarchical layout
        const root = d3.hierarchy(roadmapData);
        
        // Create a tree layout
        const treeLayout = d3.tree()
            .size([width - 80, height - 80]);
        
        // Apply the layout
        const treeData = treeLayout(root);
        
        // Create links between nodes
        svg.selectAll('.link')
            .data(treeData.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d => {{
                return `M${{d.source.x}},${{d.source.y}} C${{d.source.x}},${{(d.source.y + d.target.y) / 2}} ${{d.target.x}},${{(d.source.y + d.target.y) / 2}} ${{d.target.x}},${{d.target.y}}`;
            }});
        
        // Create node groups
        const nodes = svg.selectAll('.node')
            .data(treeData.descendants())
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${{d.x}},${{d.y}})`);
        
        // Add node shapes based on type
        nodes.each(function(d) {{
            const node = d3.select(this);
            const type = d.data.type || 'TOPIC';
            
            if (type === 'DECISION') {{
                // Circle for decision nodes
                node.append('circle')
                    .attr('r', 25)
                    .attr('fill', '#333');
            }} else if (type === 'CATEGORY') {{
                // Diamond for categories
                node.append('polygon')
                    .attr('points', '0,-30 30,0 0,30 -30,0')
                    .attr('fill', '#39424E');
            }} else {{
                // Rectangle for other nodes
                node.append('rect')
                    .attr('x', -60)
                    .attr('y', -20)
                    .attr('width', 120)
                    .attr('height', 40)
                    .attr('rx', 5)
                    .attr('ry', 5)
                    .attr('fill', '#1E3A8A');
            }}
            
            // Add title text
            node.append('text')
                .attr('dy', 5)
                .attr('text-anchor', 'middle')
                .attr('fill', 'white')
                .text(d => d.data.title.length > 15 ? d.data.title.substring(0, 15) + '...' : d.data.title);
            
            // Make nodes interactive
            node.on('click', function() {{
                showNodeDetails(d.data);
            }});
        }});
    }}
    </script>
    """
    
    return html

def format_roadmap_text(node, level=0):
    """Format a text representation of the roadmap for text-based clients"""
    lines = []
    indent = "  " * level
    
    # Format current node
    lines.append(f"{indent}● {node.title}")
    
    # Add resources if available
    if node.resources:
        for res in node.resources:
            lines.append(f"{indent}  - {res}")
    
    # Recursively format children
    for child in node.children:
        child_text = format_roadmap_text(child, level + 1)
        lines.append(child_text)
    
    return "\n".join(lines)

# Empty roadmap structure (will be filled with dynamic data)
empty_roadmap = {
    'id': 'root',
    'title': 'My Career Roadmap',
    'type': 'ROOT',
    'content': 'Your personalized learning journey',
    'children': []  # Initially empty - will be populated based on user interests
}

# Set up Flask routes
# Remove this duplicate route - it's already defined above


if __name__ == "__main__":
    # Use port 5008 since 5001, 5005, 5006, and 5007 might be in use
    app.run(debug=True, port=5008)