import chainlit as cl
import os
from dotenv import load_dotenv
import groq
import json
import uuid

# Load environment variables
load_dotenv()

# Initialize Groq client
client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

@cl.on_chat_start
async def on_chat_start():
    # Set system prompt for the LLM
    cl.user_session.set(
        "system_prompt",
        """You are a career advisor specializing in technology pathways and roadmaps.
        Analyze the user's interests and provide detailed career guidance.
        Be detailed, accurate, and helpful."""
    )
    
    # Initialize chat history
    cl.user_session.set("history", [])
    
    # Initialize roadmap data
    default_roadmap = {
        "nodes": [
            {"id": "root", "label": "Technology Careers", "level": 0, "type": "root"},
            {"id": "ai", "label": "AI & ML", "level": 1, "type": "category", "parentId": "root"},
            {"id": "web", "label": "Web Development", "level": 1, "type": "category", "parentId": "root"},
            {"id": "data", "label": "Data Science", "level": 1, "type": "category", "parentId": "root"},
            {"id": "cloud", "label": "Cloud Computing", "level": 1, "type": "category", "parentId": "root"}
        ],
        "nodeDetails": {
            "ai": {
                "description": "AI and Machine Learning involve teaching computers to learn from data and make decisions.",
                "resources": ["Coursera Machine Learning", "Fast.ai", "DeepLearning.AI"]
            },
            "web": {
                "description": "Web development focuses on creating websites and web applications.",
                "resources": ["MDN Web Docs", "freeCodeCamp", "The Odin Project"]
            },
            "data": {
                "description": "Data Science uses statistical methods to extract insights from data.",
                "resources": ["Kaggle", "DataCamp", "Python Data Science Handbook"]
            },
            "cloud": {
                "description": "Cloud Computing delivers computing services over the internet.",
                "resources": ["AWS Training", "Google Cloud", "Microsoft Azure Learn"]
            }
        }
    }
    
    cl.user_session.set("roadmap", default_roadmap)
    
    # Display welcome message
    await cl.Message(
        content="Hi there! I'm your CareerPath.AI advisor. I can help personalize your learning roadmap based on your interests. Let me know what field you're interested in!"
    ).send()
    
    # Display the initial roadmap
    await display_roadmap()

async def display_roadmap(highlight_nodes=None):
    """Display the roadmap visualization"""
    roadmap = cl.user_session.get("roadmap")
    
    # Create HTML for the roadmap
    html_content = f"""
    <div id="roadmap-container" style="height:500px; background: #161B22; border-radius:8px; overflow:hidden; position:relative;">
        <svg id="roadmap-svg" width="100%" height="100%"></svg>
        <div id="node-details" style="position:absolute; bottom:0; left:0; right:0; background:rgba(22,27,34,0.9); padding:20px; border-top:1px solid #30363d; transform:translateY(100%); transition:transform 0.3s ease; max-height:50%; overflow-y:auto;">
            <h3 id="node-title" style="margin-top:0; color:#e6edf3;"></h3>
            <p id="node-description" style="color:#c9d1d9;"></p>
            <div id="node-resources"></div>
            <button id="close-details" style="position:absolute; top:10px; right:10px; background:none; border:none; color:#8b949e; font-size:16px; cursor:pointer;">×</button>
        </div>
    </div>
    
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script>
    (function() {
        // Parse the roadmap data
        const roadmapData = {JSON_DATA};
        const highlightNodes = {HIGHLIGHT_NODES};
        
        // Set up dimensions
        const container = document.getElementById('roadmap-svg');
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        // Clear any existing SVG content
        d3.select('#roadmap-svg').selectAll('*').remove();
        
        // Create the SVG
        const svg = d3.select('#roadmap-svg')
            .attr('width', width)
            .attr('height', height);
            
        // Create a group for the entire visualization
        const g = svg.append('g');
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });
            
        svg.call(zoom);
        
        // Organize nodes by level
        const nodesByLevel = {};
        roadmapData.nodes.forEach(node => {
            if (!nodesByLevel[node.level]) {
                nodesByLevel[node.level] = [];
            }
            nodesByLevel[node.level].push(node);
        });
        
        // Calculate level heights
        const levels = Object.keys(nodesByLevel).sort((a, b) => a - b);
        const levelHeight = height * 0.7 / levels.length;
        
        // Organize horizontal positions
        levels.forEach((level, i) => {
            const nodesInLevel = nodesByLevel[level];
            const nodeWidth = width * 0.8 / Math.max(nodesInLevel.length, 1);
            
            nodesInLevel.forEach((node, j) => {
                node.x = (j + 0.5) * nodeWidth + width * 0.1;
                node.y = (i + 0.5) * levelHeight + height * 0.15;
            });
        });
        
        // Draw lines between parent and child nodes
        roadmapData.nodes.forEach(node => {
            if (node.parentId) {
                const parent = roadmapData.nodes.find(n => n.id === node.parentId);
                if (parent) {
                    g.append('line')
                        .attr('x1', parent.x)
                        .attr('y1', parent.y + 20)
                        .attr('x2', node.x)
                        .attr('y2', node.y - 20)
                        .attr('stroke', '#30363d')
                        .attr('stroke-width', 2);
                }
            }
        });
        
        // Draw nodes
        const nodeGroups = g.selectAll('.node')
            .data(roadmapData.nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x}, ${d.y})`)
            .style('cursor', 'pointer');
            
        // Add appropriate shape based on node type
        nodeGroups.each(function(d) {
            const group = d3.select(this);
            
            if (d.type === 'root') {
                group.append('circle')
                    .attr('r', 25)
                    .attr('fill', '#4f5d75')
                    .attr('stroke', highlightNodes.includes(d.id) ? '#2ECC71' : '#8b949e')
                    .attr('stroke-width', highlightNodes.includes(d.id) ? 3 : 1);
            } else if (d.type === 'category') {
                group.append('rect')
                    .attr('x', -60)
                    .attr('y', -20)
                    .attr('width', 120)
                    .attr('height', 40)
                    .attr('rx', 5)
                    .attr('fill', '#1a3d82')
                    .attr('stroke', highlightNodes.includes(d.id) ? '#2ECC71' : '#8b949e')
                    .attr('stroke-width', highlightNodes.includes(d.id) ? 3 : 1);
            } else if (d.type === 'topic') {
                group.append('rect')
                    .attr('x', -50)
                    .attr('y', -15)
                    .attr('width', 100)
                    .attr('height', 30)
                    .attr('rx', 5)
                    .attr('fill', '#1E4D8A')
                    .attr('stroke', highlightNodes.includes(d.id) ? '#2ECC71' : '#8b949e')
                    .attr('stroke-width', highlightNodes.includes(d.id) ? 3 : 1);
            } else if (d.type === 'resource') {
                group.append('rect')
                    .attr('x', -40)
                    .attr('y', -12)
                    .attr('width', 80)
                    .attr('height', 24)
                    .attr('rx', 5)
                    .attr('fill', '#2C5282')
                    .attr('stroke', highlightNodes.includes(d.id) ? '#2ECC71' : '#8b949e')
                    .attr('stroke-width', highlightNodes.includes(d.id) ? 3 : 1);
            } else {
                group.append('rect')
                    .attr('x', -50)
                    .attr('y', -15)
                    .attr('width', 100)
                    .attr('height', 30)
                    .attr('rx', 5)
                    .attr('fill', '#2D3748')
                    .attr('stroke', highlightNodes.includes(d.id) ? '#2ECC71' : '#8b949e')
                    .attr('stroke-width', highlightNodes.includes(d.id) ? 3 : 1);
            }
            
            // Add pulsing effect to highlighted nodes
            if (highlightNodes.includes(d.id)) {
                const pulseCircle = group.append('circle')
                    .attr('r', 30)
                    .attr('fill', 'none')
                    .attr('stroke', '#2ECC71')
                    .attr('stroke-width', 2)
                    .attr('opacity', 0.7)
                    .style('pointer-events', 'none');
                    
                // Animation
                function pulse() {
                    pulseCircle
                        .attr('r', 30)
                        .attr('opacity', 0.7)
                        .transition()
                        .duration(1500)
                        .attr('r', 50)
                        .attr('opacity', 0)
                        .on('end', pulse);
                }
                
                pulse();
            }
        });
        
        // Add text labels
        nodeGroups.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('fill', '#e6edf3')
            .style('font-size', d => d.type === 'root' ? '12px' : d.type === 'category' ? '13px' : '11px')
            .style('font-weight', d => d.type === 'category' ? 'bold' : 'normal')
            .style('pointer-events', 'none')
            .text(d => d.label);
            
        // Click handler for nodes
        nodeGroups.on('click', (event, d) => {
            const details = roadmapData.nodeDetails[d.id];
            const detailsPanel = document.getElementById('node-details');
            const title = document.getElementById('node-title');
            const description = document.getElementById('node-description');
            const resources = document.getElementById('node-resources');
            
            title.textContent = d.label;
            
            if (details) {
                description.textContent = details.description || 'No description available.';
                
                // Clear and populate resources
                resources.innerHTML = '';
                if (details.resources && details.resources.length > 0) {
                    const header = document.createElement('h4');
                    header.textContent = 'Resources:';
                    header.style.color = '#e6edf3';
                    header.style.marginBottom = '5px';
                    resources.appendChild(header);
                    
                    const list = document.createElement('ul');
                    list.style.color = '#c9d1d9';
                    list.style.paddingLeft = '20px';
                    
                    details.resources.forEach(resource => {
                        const item = document.createElement('li');
                        if (resource.startsWith('http')) {
                            const link = document.createElement('a');
                            link.href = resource;
                            link.target = '_blank';
                            link.textContent = resource;
                            link.style.color = '#58a6ff';
                            item.appendChild(link);
                        } else {
                            item.textContent = resource;
                        }
                        list.appendChild(item);
                    });
                    
                    resources.appendChild(list);
                }
            } else {
                description.textContent = 'No details available for this node.';
                resources.innerHTML = '';
            }
            
            // Show the details panel
            detailsPanel.style.transform = 'translateY(0)';
        });
        
        // Close details panel button
        document.getElementById('close-details').addEventListener('click', () => {
            document.getElementById('node-details').style.transform = 'translateY(100%)';
        });
        
        // Center the visualization
        const initialScale = 0.9;
        const initialTransform = d3.zoomIdentity
            .translate(width/2, height/2)
            .scale(initialScale)
            .translate(-width/2, -height/2);
            
        svg.call(zoom.transform, initialTransform);
        
        // If there are highlighted nodes, focus on the first one
        if (highlightNodes.length > 0) {
            const highlightNode = roadmapData.nodes.find(n => n.id === highlightNodes[0]);
            if (highlightNode) {
                setTimeout(() => {
                    const focusTransform = d3.zoomIdentity
                        .translate(width/2, height/2)
                        .scale(1.5)
                        .translate(-highlightNode.x, -highlightNode.y);
                        
                    svg.transition()
                        .duration(750)
                        .call(zoom.transform, focusTransform);
                }, 1000);
            }
        }
    })();
    </script>
    """
    
    # Replace placeholders with actual data
    highlight_nodes = highlight_nodes if highlight_nodes else []
    html_content = html_content.replace("{JSON_DATA}", json.dumps(roadmap))
    html_content = html_content.replace("{HIGHLIGHT_NODES}", json.dumps(highlight_nodes))
    
    # Check if roadmap element already exists
    existing_elements = cl.user_session.get("elements", [])
    roadmap_element = None
    
    for element in existing_elements:
        if element.name == "roadmap-viz":
            roadmap_element = element
            break
    
    # Create or update the roadmap element
    if roadmap_element:
        roadmap_element.content = html_content
        await roadmap_element.update()
    else:
        roadmap_element = cl.Html(name="roadmap-viz", content=html_content)
        await roadmap_element.send()

async def analyze_user_message(message_text, current_roadmap):
    """Use LLM to analyze user message and update roadmap"""
    
    # Track current node IDs to identify new ones
    current_node_ids = [node["id"] for node in current_roadmap["nodes"]]
    
    # Create the system prompt for roadmap analysis
    system_prompt = """You are an AI career advisor that updates a career roadmap based on user interests.
    
    TASK: Analyze the user message and update the provided roadmap data structure with new relevant nodes.
    
    RULES:
    1. Add relevant nodes based on the user's expressed interests
    2. Connect nodes properly using parent-child relationships
    3. Each node must have: id, label, level, type, and parentId (except root)
    4. Node types: root, category, topic, subtopic, resource
    5. For each new node, add detailed descriptions and resources in the nodeDetails object
    6. DO NOT modify existing nodes, only add new ones
    7. Assign correct level values (0 for root, 1 for main categories, 2 for topics, etc.)
    8. Use specific, relevant labels for nodes
    9. RESPOND WITH VALID JSON ONLY - just the updated roadmap object
    """
    
    user_prompt = f"""User message: "{message_text}"
    
    Current roadmap:
    {json.dumps(current_roadmap, indent=2)}
    
    Add relevant nodes based on the user's interests and return the complete updated roadmap JSON.
    """
    
    try:
        # Call the LLM to analyze and update the roadmap
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=2500
        )
        
        # Parse the response
        llm_response = response.choices[0].message.content
        
        # Extract JSON (it might be in a code block)
        json_text = llm_response
        
        if "```json" in llm_response:
            json_text = llm_response.split("```json")[1].split("```")[0].strip()
        elif "```" in llm_response:
            json_text = llm_response.split("```")[1].split("```")[0].strip()
            
        updated_roadmap = json.loads(json_text)
        
        # Identify new nodes
        new_node_ids = [node["id"] for node in updated_roadmap["nodes"] if node["id"] not in current_node_ids]
        
        return updated_roadmap, new_node_ids
        
    except Exception as e:
        print(f"Error updating roadmap: {str(e)}")
        # Return original roadmap if there's an error
        return current_roadmap, []

@cl.on_message
async def on_message(message: cl.Message):
    # Get message text
    message_text = message.content
    
    # Get current session data
    history = cl.user_session.get("history", [])
    system_prompt = cl.user_session.get("system_prompt", "You are a helpful career advisor.")
    roadmap = cl.user_session.get("roadmap", {})
    
    # Add user message to history
    history.append({"role": "user", "content": message_text})
    
    # Update the roadmap based on user message
    updated_roadmap, new_nodes = await analyze_user_message(message_text, roadmap)
    
    # Update the session roadmap
    cl.user_session.set("roadmap", updated_roadmap)
    
    # Send LLM response to user
    try:
        # Show typing indicator
        await cl.Message(content="").send()
        
        # Prepare messages for LLM
        llm_messages = [
            {"role": "system", "content": system_prompt}
        ] + history
        
        # Add roadmap context if there are new nodes
        if new_nodes:
            new_node_labels = [
                node["label"] for node in updated_roadmap["nodes"] 
                if node["id"] in new_nodes
            ]
            roadmap_context = f"I've updated your career roadmap with the following topics: {', '.join(new_node_labels)}. You can click on them for more details."
            llm_messages.append({"role": "system", "content": f"Context: {roadmap_context}"})
        
        # Get response from LLM
        response = client.chat.completions.create(
            messages=llm_messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=800
        )
        
        # Extract the response
        ai_response = response.choices[0].message.content
        
        # Add assistant message to history
        history.append({"role": "assistant", "content": ai_response})
        cl.user_session.set("history", history)
        
        # Send the response to the user
        await cl.Message(content=ai_response).send()
        
        # Update the roadmap visualization with highlighted new nodes
        await display_roadmap(new_nodes)
        
        # If there are new nodes, send a notification
        if new_nodes:
            node_labels = [
                node["label"] for node in updated_roadmap["nodes"] 
                if node["id"] in new_nodes
            ]
            await cl.Message(
                content=f"✨ I've updated your roadmap with {len(new_nodes)} new topics: {', '.join(node_labels)}. Click on them to see details!",
                author="System"
            ).send()
            
    except Exception as e:
        await cl.Message(
            content=f"I encountered an error: {str(e)}. Please try again.",
            author="System"
        ).send()

if __name__ == "__main__":
    cl.run()
