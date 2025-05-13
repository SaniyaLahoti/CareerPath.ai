import chainlit as cl
import os
import json
from dotenv import load_dotenv
import groq
from chainlit.element import Element
import uuid

# Load environment variables
load_dotenv()

# Initialize Groq client
client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

# Initialize session settings
@cl.on_chat_start
async def on_chat_start():
    # Create an agent for roadmap generation
    cl.user_session.set(
        "system_prompt",
        """You are a career advisor specializing in technology pathways and roadmaps.
        Analyze the user's interests and generate detailed career roadmaps.
        Focus on being detailed, accurate, and helpful.
        """
    )
    
    # Initialize chat history
    cl.user_session.set("history", [])
    
    # Initialize user roadmap
    cl.user_session.set("roadmap", create_default_roadmap())
    
    # Display welcome message
    await cl.Message(
        content="Hi there! I'm your CareerPath.AI advisor. I can help personalize your learning roadmap based on your interests. Let me know what field you're interested in!"
    ).send()
    
    # Display the roadmap
    await update_roadmap_display()

def create_default_roadmap():
    """Create a default roadmap to start with"""
    return {
        "nodes": [
            {"id": "root", "label": "Technology Careers", "type": "category"},
            {"id": "ai", "label": "AI & Machine Learning", "type": "category"},
            {"id": "web", "label": "Web Development", "type": "category"},
            {"id": "data", "label": "Data Science", "type": "category"},
            {"id": "cloud", "label": "Cloud Computing", "type": "category"}
        ],
        "edges": [
            {"from": "root", "to": "ai"},
            {"from": "root", "to": "web"},
            {"from": "root", "to": "data"},
            {"from": "root", "to": "cloud"}
        ],
        "nodeDetails": {
            "ai": {
                "content": "AI and Machine Learning focus on creating intelligent systems that can learn from data.",
                "resources": ["Coursera Machine Learning", "Fast.ai", "DeepLearning.AI"]
            },
            "web": {
                "content": "Web development involves building websites and web applications.",
                "resources": ["MDN Web Docs", "freeCodeCamp", "The Odin Project"]
            },
            "data": {
                "content": "Data Science focuses on extracting insights and knowledge from data.",
                "resources": ["Kaggle", "DataCamp", "Python Data Science Handbook"]
            },
            "cloud": {
                "content": "Cloud Computing involves delivering computing services over the internet.",
                "resources": ["AWS Training", "Google Cloud Training", "Microsoft Azure Learn"]
            }
        }
    }

def generate_roadmap_html(roadmap):
    """Generate HTML for the roadmap visualization"""
    
    # Create a content object to embed the roadmap visualization
    vis_network_script = """
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
      #roadmap-container {
        width: 100%;
        height: 500px;
        border: 1px solid #ccc;
        background-color: #1E1E1E;
        border-radius: 8px;
        overflow: hidden;
      }
      #node-details {
        margin-top: 20px;
        padding: 15px;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        background-color: #2a2a2a;
        display: none;
      }
      #node-details.visible {
        display: block;
      }
      #node-details h3 {
        margin-top: 0;
        color: #ccc;
      }
      #resources-list {
        list-style-type: none;
        padding-left: 0;
      }
      #resources-list li {
        margin-bottom: 5px;
      }
      .resource-link {
        color: #66b2ff;
        text-decoration: none;
      }
      .resource-link:hover {
        text-decoration: underline;
      }
      .node-category {
        background-color: #39424E !important;
        border: 2px solid #fff !important;
      }
      .node-topic {
        background-color: #1E3A8A !important;
        border: 2px solid #fff !important;
      }
      .node-subtopic {
        background-color: #1E4A8A !important;
        border: 2px solid #fff !important;
      }
      .node-resource {
        background-color: #2C5282 !important;
        border: 2px solid #fff !important;
      }
      .new-node {
        border: 3px solid #2ECC71 !important;
        animation: pulse 1.5s infinite;
      }
      @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }
        100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
      }
    </style>
    
    <div id="roadmap-container"></div>
    <div id="node-details">
      <h3 id="detail-title">Node Details</h3>
      <p id="detail-content">Click on a node to see more information.</p>
      <div id="detail-resources">
        <h4>Resources:</h4>
        <ul id="resources-list"></ul>
      </div>
    </div>
    
    <script>
      // Initialize the network visualization
      function initNetwork() {
        const container = document.getElementById('roadmap-container');
        const nodeDetails = document.getElementById('node-details');
        const detailTitle = document.getElementById('detail-title');
        const detailContent = document.getElementById('detail-content');
        const resourcesList = document.getElementById('resources-list');
        
        // Parse the roadmap data
        const roadmapData = JSON.parse('ROADMAP_DATA_PLACEHOLDER');
        
        // Track new nodes for highlighting
        const newNodes = JSON.parse('NEW_NODES_PLACEHOLDER');
        
        // Create nodes array for vis.js
        const nodes = roadmapData.nodes.map(node => {
          const visNode = {
            id: node.id,
            label: node.label,
            shape: getNodeShape(node.type),
            color: getNodeColor(node.type),
            font: { color: '#fff', face: 'Inter', size: 14 },
            className: newNodes.includes(node.id) ? 'new-node' : ''
          };
          
          if (node.type === 'category') {
            visNode.font.bold = true;
            visNode.size = 25;
          }
          
          return visNode;
        });
        
        // Create edges array for vis.js
        const edges = roadmapData.edges.map(edge => ({
          from: edge.from,
          to: edge.to,
          arrows: { to: { enabled: true, scaleFactor: 0.5 } },
          color: { color: '#aaa', highlight: '#fff' },
          width: 2,
          smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.5 }
        }));
        
        // Create the network
        const data = {
          nodes: new vis.DataSet(nodes),
          edges: new vis.DataSet(edges)
        };
        
        const options = {
          layout: {
            hierarchical: {
              direction: 'UD',
              sortMethod: 'directed',
              nodeSpacing: 120,
              levelSeparation: 150,
              blockShifting: true,
              edgeMinimization: true,
              parentCentralization: true
            }
          },
          physics: {
            hierarchicalRepulsion: {
              nodeDistance: 150
            },
            stabilization: true
          },
          interaction: {
            dragNodes: true,
            dragView: true,
            zoomView: true,
            hover: true
          },
          nodes: {
            shape: 'box',
            margin: 10,
            widthConstraint: {
              minimum: 120,
              maximum: 180
            },
            heightConstraint: {
              minimum: 40
            }
          }
        };
        
        // Create the network
        const network = new vis.Network(container, data, options);
        
        // Add click event listener
        network.on('click', function(params) {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = roadmapData.nodes.find(n => n.id === nodeId);
            
            if (node) {
              const details = roadmapData.nodeDetails[nodeId] || {
                content: 'No detailed information available for this node.',
                resources: []
              };
              
              // Update node details panel
              detailTitle.textContent = node.label;
              detailContent.textContent = details.content || 'No details available.';
              
              // Clear previous resources
              resourcesList.innerHTML = '';
              
              // Add resources if available
              if (details.resources && details.resources.length > 0) {
                details.resources.forEach(resource => {
                  const li = document.createElement('li');
                  if (resource.startsWith('http')) {
                    const a = document.createElement('a');
                    a.href = resource;
                    a.target = '_blank';
                    a.textContent = resource;
                    a.className = 'resource-link';
                    li.appendChild(a);
                  } else {
                    li.textContent = resource;
                  }
                  resourcesList.appendChild(li);
                });
              } else {
                const li = document.createElement('li');
                li.textContent = 'No resources available.';
                resourcesList.appendChild(li);
              }
              
              // Show the details panel
              nodeDetails.classList.add('visible');
            }
          } else {
            // Hide the details panel if clicking outside nodes
            nodeDetails.classList.remove('visible');
          }
        });
        
        // If there are new nodes, highlight them
        if (newNodes.length > 0) {
          network.selectNodes(newNodes);
          
          // Focus on the first new node
          if (newNodes.length > 0) {
            network.focus(newNodes[0], {
              scale: 1.2,
              animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
              }
            });
          }
        }
        
        // Fit the network to view after a short delay
        setTimeout(() => {
          network.fit({
            animation: {
              duration: 1000,
              easingFunction: 'easeInOutQuad'
            }
          });
        }, 500);
      }
      
      // Get shape based on node type
      function getNodeShape(type) {
        switch (type) {
          case 'category':
            return 'diamond';
          case 'resource':
            return 'box';
          case 'decision':
            return 'circle';
          default:
            return 'box';
        }
      }
      
      // Get color based on node type
      function getNodeColor(type) {
        switch (type) {
          case 'category':
            return { background: '#39424E', border: '#fff' };
          case 'topic':
            return { background: '#1E3A8A', border: '#fff' };
          case 'subtopic':
            return { background: '#1E4A8A', border: '#fff' };
          case 'resource':
            return { background: '#2C5282', border: '#fff' };
          case 'decision':
            return { background: '#333', border: '#fff' };
          default:
            return { background: '#1E3A8A', border: '#fff' };
        }
      }
      
      // Initialize the network when the document is loaded
      document.addEventListener('DOMContentLoaded', initNetwork);
      
      // Also initialize now in case we're already loaded
      initNetwork();
    </script>
    """
    
    # Replace the placeholder with the actual roadmap data
    vis_network_script = vis_network_script.replace(
        "ROADMAP_DATA_PLACEHOLDER", 
        json.dumps(roadmap)
    )
    
    # Add placeholder for new nodes (empty array for now)
    vis_network_script = vis_network_script.replace(
        "NEW_NODES_PLACEHOLDER", 
        "[]"
    )
    
    return vis_network_script

async def update_roadmap_with_new_nodes(roadmap, new_nodes=None):
    """Generate HTML with highlighted new nodes"""
    
    # Create a content object to embed the roadmap visualization
    vis_network_script = """
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
      #roadmap-container {
        width: 100%;
        height: 500px;
        border: 1px solid #ccc;
        background-color: #1E1E1E;
        border-radius: 8px;
        overflow: hidden;
      }
      #node-details {
        margin-top: 20px;
        padding: 15px;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        background-color: #2a2a2a;
        display: none;
      }
      #node-details.visible {
        display: block;
      }
      #node-details h3 {
        margin-top: 0;
        color: #ccc;
      }
      #resources-list {
        list-style-type: none;
        padding-left: 0;
      }
      #resources-list li {
        margin-bottom: 5px;
      }
      .resource-link {
        color: #66b2ff;
        text-decoration: none;
      }
      .resource-link:hover {
        text-decoration: underline;
      }
      .node-category {
        background-color: #39424E !important;
        border: 2px solid #fff !important;
      }
      .node-topic {
        background-color: #1E3A8A !important;
        border: 2px solid #fff !important;
      }
      .node-subtopic {
        background-color: #1E4A8A !important;
        border: 2px solid #fff !important;
      }
      .node-resource {
        background-color: #2C5282 !important;
        border: 2px solid #fff !important;
      }
      .new-node {
        border: 3px solid #2ECC71 !important;
        animation: pulse 1.5s infinite;
      }
      @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }
        100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
      }
    </style>
    
    <div id="roadmap-container"></div>
    <div id="node-details">
      <h3 id="detail-title">Node Details</h3>
      <p id="detail-content">Click on a node to see more information.</p>
      <div id="detail-resources">
        <h4>Resources:</h4>
        <ul id="resources-list"></ul>
      </div>
    </div>
    
    <script>
      // Initialize the network visualization
      function initNetwork() {
        const container = document.getElementById('roadmap-container');
        const nodeDetails = document.getElementById('node-details');
        const detailTitle = document.getElementById('detail-title');
        const detailContent = document.getElementById('detail-content');
        const resourcesList = document.getElementById('resources-list');
        
        // Parse the roadmap data
        const roadmapData = JSON.parse('ROADMAP_DATA_PLACEHOLDER');
        
        // Track new nodes for highlighting
        const newNodes = JSON.parse('NEW_NODES_PLACEHOLDER');
        
        // Create nodes array for vis.js
        const nodes = roadmapData.nodes.map(node => {
          const visNode = {
            id: node.id,
            label: node.label,
            shape: getNodeShape(node.type),
            color: getNodeColor(node.type),
            font: { color: '#fff', face: 'Inter', size: 14 },
            className: newNodes.includes(node.id) ? 'new-node' : ''
          };
          
          if (node.type === 'category') {
            visNode.font.bold = true;
            visNode.size = 25;
          }
          
          return visNode;
        });
        
        // Create edges array for vis.js
        const edges = roadmapData.edges.map(edge => ({
          from: edge.from,
          to: edge.to,
          arrows: { to: { enabled: true, scaleFactor: 0.5 } },
          color: { color: '#aaa', highlight: '#fff' },
          width: 2,
          smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.5 }
        }));
        
        // Create the network
        const data = {
          nodes: new vis.DataSet(nodes),
          edges: new vis.DataSet(edges)
        };
        
        const options = {
          layout: {
            hierarchical: {
              direction: 'UD',
              sortMethod: 'directed',
              nodeSpacing: 120,
              levelSeparation: 150,
              blockShifting: true,
              edgeMinimization: true,
              parentCentralization: true
            }
          },
          physics: {
            hierarchicalRepulsion: {
              nodeDistance: 150
            },
            stabilization: true
          },
          interaction: {
            dragNodes: true,
            dragView: true,
            zoomView: true,
            hover: true
          },
          nodes: {
            shape: 'box',
            margin: 10,
            widthConstraint: {
              minimum: 120,
              maximum: 180
            },
            heightConstraint: {
              minimum: 40
            }
          }
        };
        
        // Create the network
        const network = new vis.Network(container, data, options);
        
        // Add click event listener
        network.on('click', function(params) {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = roadmapData.nodes.find(n => n.id === nodeId);
            
            if (node) {
              const details = roadmapData.nodeDetails[nodeId] || {
                content: 'No detailed information available for this node.',
                resources: []
              };
              
              // Update node details panel
              detailTitle.textContent = node.label;
              detailContent.textContent = details.content || 'No details available.';
              
              // Clear previous resources
              resourcesList.innerHTML = '';
              
              // Add resources if available
              if (details.resources && details.resources.length > 0) {
                details.resources.forEach(resource => {
                  const li = document.createElement('li');
                  if (resource.startsWith('http')) {
                    const a = document.createElement('a');
                    a.href = resource;
                    a.target = '_blank';
                    a.textContent = resource;
                    a.className = 'resource-link';
                    li.appendChild(a);
                  } else {
                    li.textContent = resource;
                  }
                  resourcesList.appendChild(li);
                });
              } else {
                const li = document.createElement('li');
                li.textContent = 'No resources available.';
                resourcesList.appendChild(li);
              }
              
              // Show the details panel
              nodeDetails.classList.add('visible');
            }
          } else {
            // Hide the details panel if clicking outside nodes
            nodeDetails.classList.remove('visible');
          }
        });
        
        // If there are new nodes, highlight them
        if (newNodes.length > 0) {
          network.selectNodes(newNodes);
          
          // Focus on the first new node
          if (newNodes.length > 0) {
            network.focus(newNodes[0], {
              scale: 1.2,
              animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
              }
            });
          }
        }
        
        // Fit the network to view after a short delay
        setTimeout(() => {
          network.fit({
            animation: {
              duration: 1000,
              easingFunction: 'easeInOutQuad'
            }
          });
        }, 500);
      }
      
      // Get shape based on node type
      function getNodeShape(type) {
        switch (type) {
          case 'category':
            return 'diamond';
          case 'resource':
            return 'box';
          case 'decision':
            return 'circle';
          default:
            return 'box';
        }
      }
      
      // Get color based on node type
      function getNodeColor(type) {
        switch (type) {
          case 'category':
            return { background: '#39424E', border: '#fff' };
          case 'topic':
            return { background: '#1E3A8A', border: '#fff' };
          case 'subtopic':
            return { background: '#1E4A8A', border: '#fff' };
          case 'resource':
            return { background: '#2C5282', border: '#fff' };
          case 'decision':
            return { background: '#333', border: '#fff' };
          default:
            return { background: '#1E3A8A', border: '#fff' };
        }
      }
      
      // Initialize the network when the document is loaded
      document.addEventListener('DOMContentLoaded', initNetwork);
      
      // Also initialize now in case we're already loaded
      initNetwork();
    </script>
    """
    
    # Replace the placeholder with the actual roadmap data
    vis_network_script = vis_network_script.replace(
        "ROADMAP_DATA_PLACEHOLDER", 
        json.dumps(roadmap)
    )
    
    # Add the new nodes for highlighting
    vis_network_script = vis_network_script.replace(
        "NEW_NODES_PLACEHOLDER", 
        json.dumps(new_nodes if new_nodes else [])
    )
    
    return vis_network_script

async def update_roadmap_display(new_nodes=None):
    """Update the roadmap display"""
    roadmap = cl.user_session.get("roadmap")
    
    # Generate HTML for the roadmap visualization
    if new_nodes:
        roadmap_html = await update_roadmap_with_new_nodes(roadmap, new_nodes)
    else:
        roadmap_html = generate_roadmap_html(roadmap)
    
    # Check if there's already a roadmap element
    elements = cl.user_session.get("elements", [])
    roadmap_element = None
    
    for element in elements:
        if element.name == "roadmap":
            roadmap_element = element
            break
    
    # Create or update the roadmap element
    if roadmap_element:
        roadmap_element.content = roadmap_html
        await roadmap_element.update()
    else:
        roadmap_element = Element(
            name="roadmap",
            type="html",
            content=roadmap_html
        )
        cl.user_session.set("elements", elements + [roadmap_element])
        await roadmap_element.send()

async def update_roadmap_from_message(message_text, roadmap):
    """
    Agent-based roadmap generation from user message
    This is where the magic happens - we'll use LLM to analyze user input
    and add relevant nodes to the roadmap
    """
    # Get current nodes to check which ones are new later
    current_nodes = [node["id"] for node in roadmap["nodes"]]
    
    # Create the agentic prompt for roadmap generation
    system_prompt = """You are a career path advisor specializing in technology roadmaps. 
    Based on the user's message, analyze what career topics they're interested in and update their roadmap.
    The existing roadmap is provided in JSON format. You will add relevant nodes, edges, and details.
    For each new node, be sure to provide:
    1. A unique ID (use format like 'category_name' or 'topic_name')
    2. A descriptive label
    3. A type (category, topic, subtopic, resource)
    4. Connect it to existing nodes with appropriate edges
    5. Include detailed content and resources
    
    ONLY ADD RELEVANT INFORMATION based on the user's interests.
    """
    
    user_prompt = f"""User message: "{message_text}"
    
    Current roadmap:
    {json.dumps(roadmap, indent=2)}
    
    Update the roadmap by adding relevant nodes, edges, and node details based on the user's interests.
    Return ONLY the JSON of the updated roadmap, properly formatted.
    """
    
    # Call the LLM to generate the updated roadmap
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract the response
        llm_response = response.choices[0].message.content
        
        # Try to parse the JSON from the response
        updated_roadmap = None
        try:
            # Find JSON in the response (it might be wrapped in markdown code blocks)
            json_match = llm_response
            if "```json" in llm_response:
                json_match = llm_response.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_response:
                json_match = llm_response.split("```")[1].split("```")[0].strip()
                
            updated_roadmap = json.loads(json_match)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            # If parsing fails, just return the original roadmap
            return roadmap, []
        
        # Get the IDs of new nodes
        new_node_ids = [node["id"] for node in updated_roadmap["nodes"] if node["id"] not in current_nodes]
        
        return updated_roadmap, new_node_ids
    
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return roadmap, []

@cl.on_message
async def on_message(message: cl.Message):
    # Get message content
    message_text = message.content
    
    # Get history
    history = cl.user_session.get("history", [])
    history.append({"role": "user", "content": message_text})
    
    # Get current roadmap
    roadmap = cl.user_session.get("roadmap", create_default_roadmap())
    
    # Update the roadmap based on user message
    updated_roadmap, new_nodes = await update_roadmap_from_message(message_text, roadmap)
    
    # Update the session roadmap
    cl.user_session.set("roadmap", updated_roadmap)
    
    # Prepare system message
    system_prompt = cl.user_session.get("system_prompt")
    
    # Create the context for the LLM
    messages = [
        {"role": "system", "content": system_prompt},
    ] + history
    
    try:
        # Send typing indicator
        await cl.Message(content="").send()
        
        # Get response from Groq
        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract the response
        ai_response = response.choices[0].message.content
        
        # Update history
        history.append({"role": "assistant", "content": ai_response})
        cl.user_session.set("history", history)
        
        # Send the assistant's response
        await cl.Message(content=ai_response).send()
        
        # Update the roadmap display with highlighted new nodes
        await update_roadmap_display(new_nodes)
        
        # If new nodes were added, send a message about them
        if new_nodes:
            node_names = [
                node["label"] 
                for node in updated_roadmap["nodes"] 
                if node["id"] in new_nodes
            ]
            await cl.Message(
                content=f"✨ I've updated your roadmap with {len(new_nodes)} new topics: {', '.join(node_names)}. Click on them to see details!",
                author="System"
            ).send()
            
    except Exception as e:
        await cl.Message(
            content=f"I encountered an error: {str(e)}. Please try again.",
            author="System"
        ).send()

if __name__ == "__main__":
    cl.run()
