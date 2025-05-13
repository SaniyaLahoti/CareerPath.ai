import os
import json
import uuid
import chainlit as cl
from groq import Groq
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

# Set page configuration
cl.config.ui.name = "CareerPath.AI"
cl.config.ui.description = "Your personalized career roadmap assistant"

# Add custom CSS for split-screen layout
cl.config.ui.custom_css = """
/* Custom CSS for split-screen layout */
.split-view {
    display: flex;
    height: calc(100vh - 160px);
    margin-top: 20px;
    margin-bottom: 20px;
}

.chat-side {
    width: 50%;
    padding-right: 20px;
}

.roadmap-side {
    width: 50%;
    background: #121212;
    border-radius: 8px;
    overflow: hidden;
    padding: 10px;
    position: relative;
}

.roadmap-title {
    color: white;
    margin-bottom: 10px;
    font-size: 18px;
    font-weight: bold;
}

@media (max-width: 768px) {
    .split-view {
        flex-direction: column;
    }
    
    .chat-side, .roadmap-side {
        width: 100%;
    }
    
    .chat-side {
        margin-bottom: 20px;
    }
}

/* Styling for roadmap visualization */
.node rect, .node circle, .node polygon {
    stroke: #fff;
    fill-opacity: 0.9;
    stroke-width: 1.5px;
}

.node:hover rect, .node:hover circle, .node:hover polygon {
    stroke: #00a2ff;
    stroke-width: 2.5px;
    cursor: pointer;
}

.node text {
    font-weight: bold;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    fill: white;
}

.node-details {
    background: rgba(30, 58, 138, 0.95);
    border-radius: 8px;
    padding: 15px;
    margin-top: 15px;
    color: white;
}

.node-resources {
    margin-top: 10px;
}

.node-resources a {
    color: #66b2ff;
}

.link {
    fill: none;
    stroke: #ccc;
    stroke-width: 1.5px;
}
"""

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq()
client.api_key = os.getenv("GROQ_API_KEY")

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

# Set up Chainlit page configuration
cl.ChatSettings(
    features={
        "latex": True,
        "markdown": True,
    }
)

# Chainlit event handlers
@cl.on_chat_start
async def on_chat_start():
    # Get user ID and initialize roadmap
    user_id = get_user_id(cl.user_session)
    roadmap = get_or_create_roadmap(user_id)
    
    # Create the HTML for the interactive roadmap
    roadmap_html = generate_interactive_roadmap_html(roadmap)
    
    # Create the welcome message with split-screen layout
    html_content = f"""
    <div class="split-view">
        <div class="chat-side">
            <div>
                <h3>Hi there! I'm your CareerPath.AI advisor.</h3>
                <p>I can help personalize your learning roadmap based on your interests. Let me know what field you're interested in!</p>
                <p>I've prepared an interactive roadmap for you. As we chat, I'll help you explore different career paths and options.</p>
                <p>Click on any node in the roadmap to learn more about that career path.</p>
            </div>
        </div>
        <div class="roadmap-side">
            <div class="roadmap-title">My Career Roadmap</div>
            <div id="roadmap-container">
                {roadmap_html}
            </div>
        </div>
    </div>
    """
    
    # Add D3.js library
    d3_script = """
    <script src="https://d3js.org/d3.v7.min.js"></script>
    """
    
    # Send the welcome message with split-screen layout
    welcome_msg = cl.Message(content="")
    welcome_msg.html = d3_script + html_content
    await welcome_msg.send()
    
    # Initialize the session
    cl.user_session.set("history", [
        {"role": "system", "content": INITIAL_PROMPT}
    ])
    cl.user_session.set("roadmap_initialized", True)

# Function to generate formatted content for a roadmap node
def format_node_content(node):
    content = f"## {node.title}\n\n{node.content}"
    
    if node.resources and len(node.resources) > 0:
        content += "\n\n### Resources\n"
        for res in node.resources:
            if res.startswith("http"):
                content += f"- [{res}]({res})\n"
            else:
                content += f"- {res}\n"
    
    return content

@cl.on_message
async def on_message(message: cl.Message):
    try:
        # Get conversation history
        history = cl.user_session.get("history")
        
        if history is None:
            history = [{"role": "system", "content": INITIAL_PROMPT}]
        
        # Add user's message to history
        history.append({"role": "user", "content": message.content})
        
        # Process user message to update roadmap
        user_id = get_user_id(cl.user_session)
        roadmap = get_or_create_roadmap(user_id)
        
        # Create a new message with streaming
        msg = cl.Message(content="")
        await msg.send()
        
        # Variables to collect the streamed response
        full_response = ""
        
        # Stream the response from Groq
        for chunk in client.chat.completions.create(
            messages=history,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        ):
            content = chunk.choices[0].delta.content
            if content is not None:
                full_response += content
                await msg.stream_token(content)
        
        # Finalize the message
        await msg.update()
        
        # Add assistant's response to history
        history.append({"role": "assistant", "content": full_response})
        cl.user_session.set("history", history)
        
        # Update roadmap based on user input
        lowertext = message.content.lower()
        
        # Check for career interests in the message
        new_nodes_added = False
        
        # Handling AI and Machine Learning queries
        if any(term in lowertext for term in ["ai", "machine learning", "artificial intelligence", "data science", "ml"]):
            ai_node = None
            # Find AI node if it exists
            for child in roadmap.children:
                if child.title == "Machine Learning" or child.title == "AI Engineer":
                    ai_node = child
                    break
                for subchild in child.children:
                    if subchild.title == "AI Engineer":
                        ai_node = subchild
                        break
            
            # Create new AI related nodes
            if ai_node:
                # Add specific interest as a new node
                interest_title = "AI Specialization"
                if "computer vision" in lowertext:
                    interest_title = "Computer Vision"
                elif "nlp" in lowertext or "language" in lowertext:
                    interest_title = "Natural Language Processing"
                elif "reinforcement" in lowertext:
                    interest_title = "Reinforcement Learning"
                
                new_node = RoadmapNode(
                    id=str(uuid.uuid4()),
                    title=interest_title,
                    node_type="TOPIC",
                    content=f"Specialized AI path focusing on {interest_title}.",
                    resources=["Online courses", "Research papers", "Practice projects"]
                )
                ai_node.add_child(new_node)
                new_nodes_added = True
        
        # Handling Web Development queries
        elif any(term in lowertext for term in ["web", "frontend", "backend", "full stack", "javascript", "html", "css"]):
            # Find or create Web Dev node
            web_node = None
            cs_node = None
            
            # Find Computer Science node
            for child in roadmap.children:
                if child.title == "Computer Science":
                    cs_node = child
                    # Look for Web Dev within CS
                    for subchild in child.children:
                        if "Full Stack" in subchild.title or "Web" in subchild.title:
                            web_node = subchild
                            break
                    break
            
            if not web_node and cs_node:
                # Create Web Dev node if it doesn't exist
                web_node = RoadmapNode(
                    id=str(uuid.uuid4()),
                    title="Full Stack Development",
                    node_type="CATEGORY",
                    content="Web development career path covering frontend, backend, and full stack skills."
                )
                cs_node.add_child(web_node)
            
            if web_node:
                # Add specialized web node based on interest
                if "frontend" in lowertext or "html" in lowertext or "css" in lowertext:
                    new_node = RoadmapNode(
                        id=str(uuid.uuid4()),
                        title="Frontend Development",
                        node_type="TOPIC",
                        content="Frontend development focuses on creating user interfaces and experiences using HTML, CSS, and JavaScript.",
                        resources=["MDN Web Docs", "Frontend Masters", "freeCodeCamp"]
                    )
                    web_node.add_child(new_node)
                elif "backend" in lowertext or "server" in lowertext or "database" in lowertext:
                    new_node = RoadmapNode(
                        id=str(uuid.uuid4()),
                        title="Backend Development",
                        node_type="TOPIC",
                        content="Backend development involves creating server-side logic, databases, and APIs.",
                        resources=["Node.js docs", "PostgreSQL tutorials", "RESTful API guides"]
                    )
                    web_node.add_child(new_node)
                else:
                    new_node = RoadmapNode(
                        id=str(uuid.uuid4()),
                        title="Full Stack Skills",
                        node_type="TOPIC",
                        content="Full stack development covers both frontend and backend technologies.",
                        resources=["The Odin Project", "Full Stack Open"]
                    )
                    web_node.add_child(new_node)
                
                new_nodes_added = True
        
        # Create new interactive roadmap HTML if nodes were added
        if new_nodes_added:
            roadmap_html = generate_interactive_roadmap_html(roadmap)
            
            # Create a split-screen response with updated roadmap
            html_content = f"""
            <div class="split-view">
                <div class="chat-side">
                    <div>
                        <p>{full_response}</p>
                    </div>
                </div>
                <div class="roadmap-side">
                    <div class="roadmap-title">My Career Roadmap</div>
                    <div id="roadmap-container">
                        {roadmap_html}
                    </div>
                </div>
            </div>
            """
            
            # Add D3.js library
            d3_script = """
            <script src="https://d3js.org/d3.v7.min.js"></script>
            """
            
            # Send the split-screen update
            update_msg = cl.Message(content="I've updated your career roadmap based on our conversation:")
            update_msg.html = d3_script + html_content
            await update_msg.send()
        
        # Perform web search for relevant resources
        if any(word in lowertext for word in ['career', 'job', 'industry', 'trends', 'skills', 'learn', 'education']):
            # Send a message that we're gathering resources
            resources_msg = cl.Message(content="Finding relevant resources for you...")
            await resources_msg.send()
            
            try:
                # Use DuckDuckGo for web search
                search_query = message.content.replace(' ', '+') + "+career+path+guide"
                url = f'https://duckduckgo.com/html/?q={search_query}'
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get top 3 results
                results = soup.find_all('div', class_='result')[:3]
                search_results = []
                for i, result in enumerate(results):
                    try:
                        title_elem = result.find('h2')
                        link_elem = result.find('a')
                        if title_elem and link_elem:
                            title = title_elem.text
                            link = link_elem.get('href')
                            if title and link:
                                search_results.append(f"{i+1}. [{title}]({link})")
                    except Exception as e:
                        print(f"Error parsing search result: {e}")
                
                if search_results:
                    web_info = "### Relevant resources:\n\n" + "\n".join(search_results)
                    await resources_msg.update(content=web_info)
                else:
                    await resources_msg.update(content="I couldn't find specific resources for this topic. Try asking about a more specific career area.")
            except Exception as e:
                await resources_msg.update(content=f"I encountered an issue while searching for resources: {str(e)}")
    
    except Exception as e:
        await cl.Message(content=f"An error occurred: {str(e)}").send()