// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const nodeDetails = document.getElementById('node-details');
const closeDetails = document.getElementById('close-details');
const detailTitle = document.getElementById('detail-title');
const detailContent = document.getElementById('detail-content');
const detailResources = document.getElementById('detail-resources');
const expandCollapseBtn = document.getElementById('expand-collapse');
const roadmapViz = document.getElementById('roadmap-viz');

// Network visualization
let network = null;
let roadmapData = null;

// Empty roadmap data as fallback if server isn't responding
const emptyRoadmap = {
    nodes: [
        { id: "root", label: "Your Career Path", type: "root" }
    ],
    nodeDetails: {
        "root": {
            content: "This is the starting point of your personalized career roadmap. Chat with me about your interests to build your path!",
            resources: ["Let's start by discussing your interests and goals."]
        }
    }
};

// Initialize the application
function init() {
    // Fetch the initial roadmap from the server
    fetchRoadmap();
    
    // Set up event listeners
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', e => {
        if (e.key === 'Enter') sendMessage();
    });
    closeDetails.addEventListener('click', () => {
        nodeDetails.classList.remove('visible');
    });
    expandCollapseBtn.addEventListener('click', toggleRoadmapSize);
}

// Fetch roadmap from the server
async function fetchRoadmap() {
    try {
        const response = await fetch('/api/roadmap');
        roadmapData = await response.json();
        renderRoadmap();
    } catch (error) {
        console.error('Error fetching roadmap:', error);
        // Use an empty roadmap as fallback
        roadmapData = {
            nodes: [
                { id: "root", label: "Your Career Path", type: "root" }
            ],
            nodeDetails: {
                "root": {
                    content: "This is the starting point of your personalized career roadmap. Chat with me about your interests to build your path!",
                    resources: ["Let's start by discussing your interests and goals."]
                }
            }
        };
        renderRoadmap();
    }
}

// Render the roadmap using vis.js
function renderRoadmap(highlightNodes = []) {
    // Create nodes array for vis.js
    const nodes = roadmapData.nodes.map(node => {
        // Set up visual properties based on node type
        const visNode = {
            id: node.id,
            label: node.label,
            group: node.type,
            font: { color: '#fff', face: 'Inter', size: 14 }
        };
        
        // Add shape and styling based on node type
        switch (node.type) {
            case 'category':
                visNode.shape = 'diamond';
                visNode.color = {
                    background: '#2c5282',
                    border: highlightNodes.includes(node.id) ? '#38b2ac' : '#90cdf4',
                    highlight: { background: '#3182ce', border: '#90cdf4' }
                };
                visNode.font.bold = true;
                break;
                
            case 'topic':
                visNode.shape = 'box';
                visNode.color = {
                    background: '#2b6cb0',
                    border: highlightNodes.includes(node.id) ? '#38b2ac' : '#63b3ed',
                    highlight: { background: '#3182ce', border: '#63b3ed' }
                };
                break;
                
            case 'subtopic':
                visNode.shape = 'box';
                visNode.color = {
                    background: '#2c5282',
                    border: highlightNodes.includes(node.id) ? '#38b2ac' : '#4299e1',
                    highlight: { background: '#3182ce', border: '#4299e1' }
                };
                break;
                
            case 'resource':
                visNode.shape = 'box';
                visNode.color = {
                    background: '#4a5568',
                    border: highlightNodes.includes(node.id) ? '#38b2ac' : '#a0aec0',
                    highlight: { background: '#718096', border: '#a0aec0' }
                };
                visNode.font.italic = true;
                break;
                
            default:
                visNode.shape = 'box';
                visNode.color = {
                    background: '#2b6cb0',
                    border: highlightNodes.includes(node.id) ? '#38b2ac' : '#63b3ed',
                    highlight: { background: '#3182ce', border: '#63b3ed' }
                };
        }
        
        // Add a shadow effect for highlighted nodes
        if (highlightNodes.includes(node.id)) {
            visNode.shadow = {
                enabled: true,
                color: '#38b2ac',
                size: 10,
                x: 0,
                y: 0
            };
        }
        
        return visNode;
    });
    
    // Create edges based on parent-child relationships
    const edges = [];
    roadmapData.nodes.forEach(node => {
        if (node.parent) {
            edges.push({
                from: node.parent,
                to: node.id,
                arrows: 'to',
                color: { color: '#4a5568', highlight: '#a0aec0' },
                width: 2,
                smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }
            });
        } else if (node.id !== 'root') {
            // Connect top-level categories to root
            edges.push({
                from: 'root',
                to: node.id,
                arrows: 'to',
                color: { color: '#4a5568', highlight: '#a0aec0' },
                width: 2,
                smooth: { type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }
            });
        }
    });
    
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
                nodeSpacing: 150,
                levelSeparation: 150,
                blockShifting: true,
                edgeMinimization: true,
                parentCentralization: true
            }
        },
        physics: {
            enabled: false
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
                minimum: 100,
                maximum: 200
            },
            heightConstraint: {
                minimum: 30
            }
        },
        edges: {
            smooth: {
                type: 'cubicBezier',
                forceDirection: 'vertical',
                roundness: 0.4
            }
        }
    };
    
    // Destroy any existing network
    if (network) {
        // Get current view position
        const currentView = network.getViewPosition();
        const currentScale = network.getScale();
        
        // Destroy old network
        network.destroy();
        
        // Create new network
        network = new vis.Network(roadmapViz, data, options);
        
        // Restore view position
        network.moveTo({
            position: currentView,
            scale: currentScale
        });
    } else {
        // First time creating the network
        network = new vis.Network(roadmapViz, data, options);
        
        // Fit to view
        setTimeout(() => {
            network.fit({
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
        }, 500);
    }
    
    // Add click event listener
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            showNodeDetails(nodeId);
        } else {
            // Hide details if clicking on empty space
            nodeDetails.classList.remove('visible');
        }
    });
    
    // If there are highlighted nodes, focus on the first one
    if (highlightNodes.length > 0) {
        setTimeout(() => {
            network.selectNodes(highlightNodes);
            network.focus(highlightNodes[0], {
                scale: 1.2,
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
            
            // Flash a message indicating new nodes
            const flashMsg = document.createElement('div');
            flashMsg.textContent = `${highlightNodes.length} new topics added to your roadmap!`;
            flashMsg.style.position = 'absolute';
            flashMsg.style.top = '60px';
            flashMsg.style.right = '20px';
            flashMsg.style.backgroundColor = 'rgba(56, 178, 172, 0.9)';
            flashMsg.style.color = 'white';
            flashMsg.style.padding = '8px 12px';
            flashMsg.style.borderRadius = '4px';
            flashMsg.style.zIndex = '1000';
            flashMsg.style.fontWeight = '500';
            flashMsg.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
            flashMsg.style.animation = 'fadeIn 0.3s ease-out, fadeOut 0.3s 3s ease-out forwards';
            document.getElementById('roadmap-container').appendChild(flashMsg);
            
            // Add fadeOut animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes fadeOut {
                    from { opacity: 1; transform: translateY(0); }
                    to { opacity: 0; transform: translateY(-10px); }
                }
            `;
            document.head.appendChild(style);
            
            // Remove the flash message after 3.3 seconds
            setTimeout(() => {
                if (flashMsg.parentNode) {
                    flashMsg.parentNode.removeChild(flashMsg);
                }
            }, 3300);
        }, 500);
    }
}

// Show node details in the panel
function showNodeDetails(nodeId) {
    const node = roadmapData.nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    const details = roadmapData.nodeDetails[nodeId];
    
    // Set title
    detailTitle.textContent = node.label;
    
    // Clear the details container
    detailContent.innerHTML = '';
    detailResources.innerHTML = '';
    
    // Add content if available with formatting
    if (details && details.content) {
        const contentParagraph = document.createElement('p');
        contentParagraph.innerHTML = formatTextWithMarkdown(details.content);
        detailContent.appendChild(contentParagraph);
    } else {
        const contentParagraph = document.createElement('p');
        contentParagraph.textContent = 'No detailed information available for this topic.';
        detailContent.appendChild(contentParagraph);
    }
    
    // Add skills section if available
    if (details && details.skills) {
        const skillsSection = createDetailSection('Required Skills', details.skills);
        detailContent.appendChild(skillsSection);
    }
    
    // Add career progression if available
    if (details && details.career_progression) {
        const careerSection = createDetailSection('Career Progression', details.career_progression);
        detailContent.appendChild(careerSection);
    }
    
    // Add salary information if available
    if (details && details.salary) {
        const salarySection = createDetailSection('Salary Expectations', details.salary);
        detailContent.appendChild(salarySection);
    }
    
    // Add courses and learning resources
    if (details && details.resources && details.resources.length > 0) {
        const resourcesTitle = document.createElement('h3');
        resourcesTitle.textContent = 'Learning Resources & Courses';
        resourcesTitle.style.borderBottom = '1px solid #4a5568';
        resourcesTitle.style.paddingBottom = '8px';
        resourcesTitle.style.marginTop = '20px';
        detailResources.appendChild(resourcesTitle);
        
        const resourcesList = document.createElement('ul');
        resourcesList.style.listStyleType = 'none';
        resourcesList.style.padding = '0';
        resourcesList.style.marginTop = '12px';
        
        details.resources.forEach(resource => {
            const li = document.createElement('li');
            li.style.marginBottom = '12px';
            li.style.padding = '8px';
            li.style.borderRadius = '4px';
            li.style.backgroundColor = 'rgba(45, 55, 72, 0.3)';
            
            // Determine if resource is a URL or just text
            if (typeof resource === 'string') {
                if (resource.startsWith('http')) {
                    // It's a URL
                    const a = document.createElement('a');
                    a.href = resource;
                    a.target = '_blank';
                    a.textContent = getDisplayNameFromUrl(resource);
                    a.style.color = '#63b3ed';
                    a.style.textDecoration = 'none';
                    a.style.display = 'block';
                    li.appendChild(a);
                } else {
                    // It's just text
                    li.textContent = resource;
                }
            } else if (typeof resource === 'object') {
                // If it's an object with name and url properties
                if (resource.name && resource.url) {
                    const a = document.createElement('a');
                    a.href = resource.url;
                    a.target = '_blank';
                    a.textContent = resource.name;
                    a.style.color = '#63b3ed';
                    a.style.textDecoration = 'none';
                    a.style.display = 'block';
                    li.appendChild(a);
                    
                    // Add description if available
                    if (resource.description) {
                        const desc = document.createElement('div');
                        desc.textContent = resource.description;
                        desc.style.fontSize = '0.85em';
                        desc.style.color = '#a0aec0';
                        desc.style.marginTop = '4px';
                        li.appendChild(desc);
                    }
                } else {
                    li.textContent = JSON.stringify(resource);
                }
            }
            
            resourcesList.appendChild(li);
        });
        detailResources.appendChild(resourcesList);
    }
    
    // Add sample projects section if available
    if (details && details.projects) {
        const projectsTitle = document.createElement('h3');
        projectsTitle.textContent = 'Sample Projects to Practice';
        projectsTitle.style.borderBottom = '1px solid #4a5568';
        projectsTitle.style.paddingBottom = '8px';
        projectsTitle.style.marginTop = '20px';
        detailResources.appendChild(projectsTitle);
        
        const projectsList = document.createElement('ul');
        projectsList.style.paddingLeft = '20px';
        projectsList.style.marginTop = '12px';
        
        if (Array.isArray(details.projects)) {
            details.projects.forEach(project => {
                const li = document.createElement('li');
                li.style.marginBottom = '8px';
                
                if (typeof project === 'string') {
                    li.innerHTML = formatTextWithMarkdown(project);
                } else if (typeof project === 'object' && project.name) {
                    const projectName = document.createElement('strong');
                    projectName.textContent = project.name;
                    li.appendChild(projectName);
                    
                    if (project.description) {
                        const desc = document.createElement('div');
                        desc.innerHTML = formatTextWithMarkdown(project.description);
                        li.appendChild(desc);
                    }
                }
                
                projectsList.appendChild(li);
            });
        } else if (typeof details.projects === 'string') {
            const li = document.createElement('li');
            li.innerHTML = formatTextWithMarkdown(details.projects);
            projectsList.appendChild(li);
        }
        
        detailResources.appendChild(projectsList);
    }
    
    // Add books section if available
    if (details && details.books) {
        const booksTitle = document.createElement('h3');
        booksTitle.textContent = 'Recommended Books';
        booksTitle.style.borderBottom = '1px solid #4a5568';
        booksTitle.style.paddingBottom = '8px';
        booksTitle.style.marginTop = '20px';
        detailResources.appendChild(booksTitle);
        
        const booksList = document.createElement('ul');
        booksList.style.paddingLeft = '20px';
        booksList.style.marginTop = '12px';
        
        if (Array.isArray(details.books)) {
            details.books.forEach(book => {
                const li = document.createElement('li');
                li.style.marginBottom = '8px';
                
                if (typeof book === 'string') {
                    li.textContent = book;
                } else if (typeof book === 'object' && book.title) {
                    li.innerHTML = `<strong>${book.title}</strong>`;
                    if (book.author) {
                        li.innerHTML += ` by ${book.author}`;
                    }
                }
                
                booksList.appendChild(li);
            });
        } else if (typeof details.books === 'string') {
            const li = document.createElement('li');
            li.textContent = details.books;
            booksList.appendChild(li);
        }
        
        detailResources.appendChild(booksList);
    }
    
    // Show the details panel
    nodeDetails.classList.add('visible');
}

// Helper function to create detail sections
function createDetailSection(title, content) {
    const section = document.createElement('div');
    section.style.marginTop = '16px';
    
    const sectionTitle = document.createElement('h4');
    sectionTitle.textContent = title;
    sectionTitle.style.color = '#e2e8f0';
    sectionTitle.style.marginBottom = '8px';
    section.appendChild(sectionTitle);
    
    const sectionContent = document.createElement('p');
    
    if (Array.isArray(content)) {
        const list = document.createElement('ul');
        list.style.paddingLeft = '20px';
        content.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = formatTextWithMarkdown(item);
            list.appendChild(li);
        });
        section.appendChild(list);
    } else {
        sectionContent.innerHTML = formatTextWithMarkdown(content);
        section.appendChild(sectionContent);
    }
    
    return section;
}

// Helper function to format text with markdown-like syntax
function formatTextWithMarkdown(text) {
    if (!text) return '';
    
    // Replace bold syntax
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Replace italic syntax
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Replace links [text](url)
    text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color:#63b3ed;text-decoration:none;">$1</a>');
    
    // Replace line breaks
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Helper function to get a display name from a URL
function getDisplayNameFromUrl(url) {
    try {
        const urlObj = new URL(url);
        const domain = urlObj.hostname.replace('www.', '');
        
        // Common learning platforms
        if (domain.includes('coursera')) return 'Coursera Course';
        if (domain.includes('udemy')) return 'Udemy Course';
        if (domain.includes('edx')) return 'edX Course';
        if (domain.includes('pluralsight')) return 'Pluralsight Course';
        if (domain.includes('linkedin.com/learning')) return 'LinkedIn Learning';
        if (domain.includes('freecodecamp')) return 'freeCodeCamp Resource';
        if (domain.includes('youtube')) return 'YouTube Tutorial';
        if (domain.includes('github')) return 'GitHub Repository';
        
        // Default to domain name
        return domain.charAt(0).toUpperCase() + domain.slice(1) + ' Resource';
    } catch (e) {
        return url;
    }
}

// Toggle roadmap size
function toggleRoadmapSize() {
    const chatContainer = document.getElementById('chat-container');
    const roadmapContainer = document.getElementById('roadmap-container');
    
    if (chatContainer.style.width === '25%') {
        chatContainer.style.width = '40%';
        roadmapContainer.style.width = '60%';
        expandCollapseBtn.textContent = '⟷';
    } else if (chatContainer.style.width === '40%' || chatContainer.style.width === '') {
        chatContainer.style.width = '25%';
        roadmapContainer.style.width = '75%';
        expandCollapseBtn.textContent = '⟷';
    }
    
    // Wait for transition to complete, then redraw the network
    setTimeout(() => {
        if (network) {
            network.redraw();
            network.fit();
        }
    }, 300);
}

// Send message to the server
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Disable input and button during processing
    chatInput.disabled = true;
    sendButton.disabled = true;
    
    // Add user message to chat
    addMessage(text, 'user');
    chatInput.value = '';
    
    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message';
    const loadingIndicator = document.createElement('span');
    loadingIndicator.id = 'loading-spinner';
    loadingDiv.appendChild(loadingIndicator);
    loadingDiv.appendChild(document.createTextNode(' Thinking...'));
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        // Process the message through the server API
        await sendChatMessage(text);
        
        // Remove loading indicator
        chatMessages.removeChild(loadingDiv);
    } catch (error) {
        // Remove loading indicator
        chatMessages.removeChild(loadingDiv);
        
        // Show error message
        addMessage('Sorry, I encountered an error while processing your message. Please try again.', 'bot');
        console.error('Error sending message:', error);
    } finally {
        // Re-enable input and button
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
}

// Process chat through the server API
async function sendChatMessage(message) {
    try {
        // Send message to API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Server response:', data);
        
        // Add bot response to chat
        if (data.response) {
            addMessage(data.response, 'bot');
        }
        
        // Update roadmap if new nodes were added
        if (data.roadmap) {
            roadmapData = data.roadmap;
            const newNodes = data.newNodes || [];
            
            // Show system message if new nodes were added
            if (newNodes.length > 0) {
                // Get the labels of new nodes
                const newNodeLabels = newNodes.map(nodeId => {
                    const node = roadmapData.nodes.find(n => n.id === nodeId);
                    return node ? node.label : nodeId;
                }).join(', ');
                
                const systemMsg = document.createElement('div');
                systemMsg.className = 'message system-message';
                systemMsg.textContent = `✨ Added ${newNodes.length} new topics to your roadmap: ${newNodeLabels}`;
                chatMessages.appendChild(systemMsg);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
            
            // Update the roadmap visualization
            renderRoadmap(newNodes);
        }
        
        return true;
    } catch (error) {
        console.error('Error sending chat message:', error);
        addMessage('Sorry, I encountered an error while processing your message. Please try again.', 'bot');
        return false;
    }
}

// Add a message to the chat
function addMessage(text, sender) {
    const message = document.createElement('div');
    message.className = `message ${sender}-message`;
    
    // Convert markdown-style formatting to HTML
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic
    text = text.replace(/\n\n/g, '<br><br>'); // Line breaks
    text = text.replace(/\n/g, '<br>'); // Line breaks
    
    // Handle lists
    const listRegex = /^\d+\.\s+(.*?)$/gm;
    text = text.replace(listRegex, '<li>$1</li>');
    text = text.replace(/<li>(.*?)<\/li>/g, function(match) {
        return '<ol>' + match + '</ol>';
    });
    
    // Handle bullet lists
    const bulletRegex = /^-\s+(.*?)$/gm;
    text = text.replace(bulletRegex, '<li>$1</li>');
    text = text.replace(/<li>(.*?)<\/li>/g, function(match) {
        return '<ul>' + match + '</ul>';
    });
    
    // Set the HTML content
    message.innerHTML = text;
    
    // Add the message to the chat
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Initialize the application when the document is loaded
document.addEventListener('DOMContentLoaded', init);
