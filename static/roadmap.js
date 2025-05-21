// Load Markdown parser
const markdownParser = window.markdownit ? window.markdownit() : null;

// Function to format bot responses with markdown
function formatBotResponse(text) {
    // If markdown-it library is loaded, use it to parse markdown
    if (markdownParser) {
        return markdownParser.render(text);
    }
    
    // Fallback to basic formatting if library isn't available
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

// Function to truncate very long messages and make them expandable
function createExpandableMessage(content, isBot = true) {
    const maxLength = 300; // Characters before truncation
    
    // For user messages or short content, just format and return
    if (!isBot || content.length <= maxLength) {
        return isBot ? formatBotResponse(content) : content;
    }
    
    // For longer bot messages, create a unique ID for this message
    const messageId = 'msg_' + Math.random().toString(36).substring(2, 10);
    
    // Generate HTML with the unique ID for targeting
    const truncated = content.substring(0, maxLength);
    return `
        <div class="expandable-message" id="${messageId}">
            <div class="message-content truncated">
                ${formatBotResponse(truncated)}...
                <a href="javascript:void(0)" onclick="expandMessage('${messageId}')" class="show-more">Read more</a>
            </div>
            <div class="message-content full" style="display: none">
                ${formatBotResponse(content)}
                <a href="javascript:void(0)" onclick="collapseMessage('${messageId}')" class="show-less">Show less</a>
            </div>
        </div>
    `;
}

// Global functions for expanding/collapsing messages
function expandMessage(messageId) {
    const container = document.getElementById(messageId);
    if (container) {
        container.querySelector('.truncated').style.display = 'none';
        container.querySelector('.full').style.display = 'block';
        // Scroll to ensure the expanded content is visible
        container.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
}

function collapseMessage(messageId) {
    const container = document.getElementById(messageId);
    if (container) {
        container.querySelector('.full').style.display = 'none';
        container.querySelector('.truncated').style.display = 'block';
    }
}

// Chat logic
function sendMessage() {
    const input = document.getElementById('chat-input');
    const chatBox = document.getElementById('chat-box');
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message with clean formatting
    chatBox.innerHTML += `<div class="message user-message"><b>You:</b> ${message}</div>`;
    input.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;
    
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => {
        // Add bot's response with markdown support and expandable content
        chatBox.innerHTML += `<div class="message bot-message"><b>Bot:</b> ${createExpandableMessage(data.response)}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
        
        // Check if roadmap data exists and has the required structure
        if (data.roadmap) {
            console.log('Received roadmap data:', JSON.stringify(data.roadmap));
            
            try {
                // Only try to render if the roadmap has some content
                if (data.roadmap.children && data.roadmap.children.length > 0) {
                    renderRoadmap(data.roadmap);
                    chatBox.innerHTML += `<div class="message system-message">✨ Added ${countNewNodes(data.roadmap)} new topics to your roadmap</div>`;
                } else if (!data.roadmap.children) {
                    console.error('Roadmap missing children array');
                    // Initialize an empty roadmap if none exists
                    renderEmptyRoadmap();
                } else if (data.roadmap.children.length === 0) {
                    // If we have an empty roadmap (waiting for user interests)
                    console.log('Empty roadmap received - waiting for specific interests');
                    renderEmptyRoadmap();
                }
            } catch (renderError) {
                console.error('Error rendering roadmap:', renderError);
                // If we can't render the roadmap, show an empty one
                renderEmptyRoadmap();
            }
            
            chatBox.scrollTop = chatBox.scrollHeight;
        } else {
            console.warn('No roadmap data received from server');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        chatBox.innerHTML += `<div class="message system-message">Sorry, I encountered an error while processing your message. Please try again.</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}

document.getElementById('chat-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') sendMessage();
});

// Track previously seen nodes to detect new ones
let previousNodes = new Set();

// Count new nodes added to the roadmap
function countNewNodes(roadmap) {
    let newCount = 0;
    const currentNodes = new Set();
    
    function traverse(node) {
        currentNodes.add(node.id);
        if (!previousNodes.has(node.id)) {
            newCount++;
        }
        if (node.children && node.children.length > 0) {
            node.children.forEach(traverse);
        }
    }
    
    traverse(roadmap);
    previousNodes = currentNodes;
    return newCount;
}

// Convert hierarchical data to vis.js format
function convertToVisFormat(roadmapData) {
    const nodes = [];
    const edges = [];
    const highlightNodes = [];
    
    function traverse(node, parent = null, level = 0) {
        // Create node
        const nodeColor = getNodeColor(node.type);
        const nodeShape = getNodeShape(node.type);
        
        nodes.push({
            id: node.id,
            label: node.title,
            level: level,
            color: nodeColor,
            shape: nodeShape,
            font: { color: '#ffffff', size: 14 },
            margin: 10,
            data: node // Store the original data for details
        });
        
        // If this is a new node, highlight it
        if (!previousNodes.has(node.id)) {
            highlightNodes.push(node.id);
        }
        
        // Create edge if parent exists
        if (parent) {
            edges.push({
                from: parent.id,
                to: node.id,
                arrows: 'to',
                color: { color: '#4a5568' },
                smooth: { type: 'cubicBezier', roundness: 0.2 }
            });
        }
        
        // Process children recursively
        if (node.children && node.children.length > 0) {
            node.children.forEach(child => traverse(child, node, level + 1));
        }
    }
    
    traverse(roadmapData);
    return { nodes, edges, highlightNodes };
}

// Get node color based on type
function getNodeColor(type) {
    switch(type) {
        case 'ROOT': return { background: '#3182ce', border: '#2c5282' };
        case 'CATEGORY': return { background: '#805ad5', border: '#553c9a' };
        case 'TOPIC': return { background: '#38a169', border: '#276749' };
        case 'SUBTOPIC': return { background: '#dd6b20', border: '#9c4221' };
        case 'DECISION': return { background: '#e53e3e', border: '#9b2c2c' };
        default: return { background: '#3182ce', border: '#2c5282' };
    }
}

// Get node shape based on type
function getNodeShape(type) {
    switch(type) {
        case 'ROOT': return 'box';
        case 'CATEGORY': return 'diamond';
        case 'TOPIC': return 'box';
        case 'SUBTOPIC': return 'box';
        case 'DECISION': return 'circle';
        default: return 'box';
    }
}

// Function to render an empty roadmap with guidance for agentic AI
function renderEmptyRoadmap() {
    const container = document.getElementById('roadmap-viz');
    if (!container) return;
    
    // Clear the container
    container.innerHTML = '';
    
    // Create a more descriptive placeholder for agentic AI
    const placeholder = document.createElement('div');
    placeholder.className = 'roadmap-placeholder';
    placeholder.innerHTML = `
        <div class="roadmap-placeholder-content">
            <h3>Your Agentic AI Roadmap</h3>
            <p>Tell me specifically about your interests and knowledge in agentic AI:</p>
            <ul>
                <li>"I'm interested in agentic AI and I'm a beginner"</li>
                <li>"I know about agentic AI frameworks and RAG"</li>
                <li>"I'm advanced in agentic AI and want to learn about multi-agent systems"</li>
            </ul>
        </div>
    `;
    container.appendChild(placeholder);
    
    // Add some extra styling for the agentic AI recommendations
    const style = document.createElement('style');
    style.textContent = `
        .roadmap-placeholder-content ul {
            text-align: left;
            margin-top: 15px;
            padding-left: 20px;
        }
        .roadmap-placeholder-content li {
            margin-bottom: 8px;
            color: #4a90e2;
        }
    `;
    document.head.appendChild(style);
}

// Render the roadmap using vis.js
function renderRoadmap(roadmapData = null) {
    const container = document.getElementById('roadmap-viz');
    if (!container) return;
    
    // Clear the container
    container.innerHTML = '';
    
    // Create placeholder if no roadmap data yet
    if (!roadmapData) {
        renderEmptyRoadmap();
        return;
    }
    
    // If roadmap data is empty (no children), also show the empty state
    if (!roadmapData.children || roadmapData.children.length === 0) {
        renderEmptyRoadmap();
        return;
    }
    
    // Convert the hierarchical data to vis.js format
    const { nodes, edges, highlightNodes } = convertToVisFormat(roadmapData);
    
    // Create the data object
    const data = {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges)
    };
    
    // Set up the network options
    const options = {
        layout: {
            hierarchical: {
                direction: 'UD',
                sortMethod: 'directed',
                nodeSpacing: 100,
                levelSeparation: 150
            }
        },
        physics: {
            enabled: false
        },
        interaction: {
            navigationButtons: true,
            keyboard: true,
            zoomView: true
        },
        nodes: {
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 2,
            shadow: true
        }
    };
    
    // Create the network
    const network = new vis.Network(container, data, options);
    
    // Handle node clicks
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const nodeData = nodes.find(n => n.id === nodeId);
            if (nodeData && nodeData.data) {
                showNodeDetails(nodeData.data);
            }
        } else {
            // Hide details panel when clicking away
            hideNodeDetails();
        }
    });
    
    // Highlight new nodes
    if (highlightNodes.length > 0) {
        network.selectNodes(highlightNodes);
        
        // Pulse animation for highlighted nodes
        let pulseCount = 0;
        const pulseInterval = setInterval(() => {
            const scale = 1 + Math.sin(pulseCount * 0.2) * 0.2;
            network.moveTo({
                scale: scale,
                animation: {
                    duration: 500,
                    easingFunction: 'easeInOutQuad'
                }
            });
            pulseCount++;
            if (pulseCount > 10) clearInterval(pulseInterval);
        }, 500);
    }
}

// Show node details in the panel
function showNodeDetails(node) {
    const detailsDiv = document.getElementById('node-details');
    if (!detailsDiv) return;
    
    // Set content
    const title = document.createElement('h3');
    title.textContent = node.title;
    
    const content = document.createElement('p');
    content.textContent = node.content || 'No detailed information available';
    
    // Clear previous content
    detailsDiv.innerHTML = '';
    detailsDiv.appendChild(title);
    detailsDiv.appendChild(content);
    
    // Add resources if available
    if (node.resources && node.resources.length > 0) {
        const resourcesTitle = document.createElement('h4');
        resourcesTitle.textContent = 'Resources';
        detailsDiv.appendChild(resourcesTitle);
        
        const resourcesList = document.createElement('ul');
        node.resources.forEach(resource => {
            const li = document.createElement('li');
            if (resource.startsWith('http')) {
                const a = document.createElement('a');
                a.href = resource;
                a.target = '_blank';
                a.textContent = resource;
                li.appendChild(a);
            } else {
                li.textContent = resource;
            }
            resourcesList.appendChild(li);
        });
        detailsDiv.appendChild(resourcesList);
    }
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'close-btn';
    closeBtn.textContent = '×';
    closeBtn.onclick = hideNodeDetails;
    detailsDiv.appendChild(closeBtn);
    
    // Show the panel with animation
    detailsDiv.classList.add('visible');
}

// Hide the node details panel
function hideNodeDetails() {
    const detailsDiv = document.getElementById('node-details');
    if (detailsDiv) {
        detailsDiv.classList.remove('visible');
    }
}

// Initial render with welcome message
window.onload = () => {
    // Initialize the chat box
    const chatBox = document.getElementById('chat-box');
    if (!chatBox.innerHTML.trim()) {
        chatBox.innerHTML = "<div class='message bot-message'><b>Bot:</b> Hi there! I'm your CareerPath.AI advisor. I can help personalize your learning roadmap based on your interests. Let me know what field you're interested in!</div>";
    }
    
    // Render initial empty roadmap
    renderRoadmap();

    // Add event listener for the send button
    const sendButton = document.getElementById('send-btn');
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Also add event listener for the alternative button id
    const altSendButton = document.getElementById('send-button');
    if (altSendButton) {
        altSendButton.addEventListener('click', sendMessage);
    }
}; 