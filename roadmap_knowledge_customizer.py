"""
Customizes roadmaps based on user knowledge assessment
to provide a personalized learning experience.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional

def update_roadmap_with_knowledge_level(
    current_roadmap: Dict[str, Any], 
    interests: List[str],
    knowledge_level: str
) -> Dict[str, Any]:
    """
    Customize a roadmap based on the user's assessed knowledge level.
    Different content will be shown or highlighted based on beginner,
    intermediate, or advanced levels.
    
    Args:
        current_roadmap: The current roadmap structure
        interests: List of user interests
        knowledge_level: The user's knowledge level (beginner, intermediate, advanced)
        
    Returns:
        Updated roadmap structure with customized content
    """
    # Check if we have a valid knowledge level
    if knowledge_level not in ['beginner', 'intermediate', 'advanced']:
        # Default to beginner if not specified
        knowledge_level = 'beginner'
    
    # Special case: For agentic AI, generate a complete custom roadmap
    has_agentic_ai_interest = any(
        interest.lower() in ['agentic-ai', 'agentic ai']
        for interest in interests
    )
    
    if has_agentic_ai_interest:
        print(f"Generating dedicated agentic AI roadmap for knowledge level: {knowledge_level}")
        # Generate a completely new roadmap specifically for agentic AI
        return generate_agentic_ai_roadmap(knowledge_level)
    
    # For other interests, use the standard customization approach
    # Create a deep copy of the roadmap to avoid modifying the original
    updated_roadmap = json.loads(json.dumps(current_roadmap))
    
    # Check for general AI interests
    has_ai_interest = any(
        interest.lower() in ['ai', 'artificial intelligence', 'machine learning'] 
        for interest in interests
    )
    
    if has_ai_interest:
        # Customize AI roadmap based on knowledge level
        customize_ai_roadmap_for_level(updated_roadmap, knowledge_level)
    
    # Add a note about the customization
    if 'content' in updated_roadmap:
        level_notes = {
            'beginner': "Customized for beginners with foundation-building content",
            'intermediate': "Customized for intermediate users with practical implementation focus",
            'advanced': "Customized for advanced users with cutting-edge techniques"
        }
        updated_roadmap['content'] += f" - {level_notes.get(knowledge_level, '')}"
    
    return updated_roadmap

def customize_ai_roadmap_for_level(roadmap_node: Dict[str, Any], knowledge_level: str) -> None:
    """
    Recursively customize AI roadmap nodes based on knowledge level
    
    Args:
        roadmap_node: A node in the roadmap (possibly with children)
        knowledge_level: User's knowledge level
    """
    # Process current node based on title/type
    node_title = roadmap_node.get('title', '').lower()
    
    # Check for AI-related node
    is_ai_node = any(term in node_title for term in 
                     ['ai', 'artificial intelligence', 'machine learning', 'agent'])
    
    if is_ai_node:
        # Add indicators based on knowledge level
        if knowledge_level == 'beginner':
            if 'introduction' in node_title or 'fundamental' in node_title or 'basic' in node_title:
                roadmap_node['highlight'] = True
                roadmap_node['priority'] = 'high'
                
        elif knowledge_level == 'intermediate':
            if any(term in node_title for term in ['framework', 'implement', 'develop', 'tool']):
                roadmap_node['highlight'] = True
                roadmap_node['priority'] = 'high'
                
            if 'introduction' in node_title or 'basic' in node_title:
                roadmap_node['priority'] = 'low'
                
        elif knowledge_level == 'advanced':
            if any(term in node_title for term in ['advanced', 'research', 'cutting-edge', 'system']):
                roadmap_node['highlight'] = True
                roadmap_node['priority'] = 'high'
                
            if any(term in node_title for term in ['introduction', 'basic', 'fundamental']):
                roadmap_node['collapsed'] = True
                roadmap_node['priority'] = 'low'
    
    # Add agentic AI specific nodes for the right knowledge level
    if 'agent' in node_title:
        agentic_ai_nodes = create_agentic_ai_nodes_for_level(knowledge_level)
        
        # Only add if we have new nodes and this node has children
        if agentic_ai_nodes and 'children' in roadmap_node:
            # Check if we already have similar nodes to avoid duplication
            existing_titles = [child.get('title', '').lower() for child in roadmap_node.get('children', [])]
            
            for new_node in agentic_ai_nodes:
                if not any(new_node['title'].lower() in title for title in existing_titles):
                    # Mark as newly added
                    new_node['highlight'] = True
                    new_node['new'] = True
                    roadmap_node['children'].append(new_node)
    
    # Recursively process children
    for child in roadmap_node.get('children', []):
        customize_ai_roadmap_for_level(child, knowledge_level)

def generate_agentic_ai_roadmap(knowledge_level: str = 'beginner') -> Dict[str, Any]:
    """
    Generate a complete roadmap for agentic AI based on the user's knowledge level.
    This creates a fully customized roadmap rather than simply adding nodes to an existing one.
    
    Args:
        knowledge_level: User's knowledge level ('beginner', 'intermediate', or 'advanced')
        
    Returns:
        A complete roadmap structure focused on agentic AI
    """
    # Create the root node
    root_id = f"agentic_ai_roadmap_{uuid.uuid4().hex[:8]}"
    roadmap = {
        'id': root_id,
        'title': 'My Career Roadmap',
        'type': 'ROOT',
        'content': 'Your personalized agentic AI learning journey',
        'children': []
    }
    
    # Create the main category node
    ai_category = {
        'id': f"ai_engineering_{uuid.uuid4().hex[:8]}",
        'title': 'AI Engineering',
        'type': 'CATEGORY',
        'content': 'Artificial Intelligence and ML engineering paths',
        'children': []
    }
    
    # Create the agentic AI node
    agentic_ai_node = {
        'id': f"agentic_ai_{uuid.uuid4().hex[:8]}",
        'title': 'Agentic AI',
        'type': 'TOPIC',
        'content': 'The cutting-edge field of developing autonomous AI agents',
        'highlight': True,
        'children': []
    }
    
    # Add level-specific content based on the user's knowledge
    if knowledge_level == 'beginner':
        # For beginners: focus on fundamentals and concepts
        agentic_ai_node['children'] = [
            {
                'id': f"ai_agent_basics_{uuid.uuid4().hex[:8]}",
                'title': 'What is an AI Agent?',
                'type': 'TOPIC',
                'content': 'AI agents are autonomous systems that can perceive their environment, make decisions, and take actions to achieve specific goals.',
                'resources': ['https://www.anthropic.com/index/claude-instant-1-2'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"llm_basics_{uuid.uuid4().hex[:8]}",
                'title': 'LLM Foundations',
                'type': 'TOPIC',
                'content': 'Learn how Large Language Models function as the core of modern AI agents.',
                'resources': ['https://huggingface.co/learn/nlp-course/chapter1/1'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"prompt_engineering_{uuid.uuid4().hex[:8]}",
                'title': 'Prompt Engineering',
                'type': 'TOPIC',
                'content': 'Master the art of crafting effective prompts to guide agent behavior.',
                'resources': ['https://www.promptingguide.ai/'],
                'children': []
            },
            {
                'id': f"tools_basics_{uuid.uuid4().hex[:8]}",
                'title': 'Tools and Functions',
                'type': 'TOPIC',
                'content': 'Introduction to how agents can use tools and call functions.',
                'resources': ['https://platform.openai.com/docs/guides/function-calling'],
                'children': []
            }
        ]
        
    elif knowledge_level == 'intermediate':
        # For intermediate: focus on frameworks and implementation
        agentic_ai_node['children'] = [
            {
                'id': f"agent_frameworks_{uuid.uuid4().hex[:8]}",
                'title': 'Agent Frameworks',
                'type': 'TOPIC',
                'content': 'Explore LangChain, AutoGPT, and other frameworks for building AI agents.',
                'resources': ['https://python.langchain.com/docs/get_started/introduction'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"tool_integration_{uuid.uuid4().hex[:8]}",
                'title': 'Tool Integration',
                'type': 'TOPIC',
                'content': 'Connect your agents to external tools, APIs, and data sources.',
                'resources': ['https://python.langchain.com/docs/modules/agents/tools/'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"agent_memory_{uuid.uuid4().hex[:8]}",
                'title': 'Agent Memory Systems',
                'type': 'TOPIC',
                'content': 'Implement different memory architectures for persistent agent knowledge.',
                'resources': ['https://python.langchain.com/docs/modules/memory/'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"rag_systems_{uuid.uuid4().hex[:8]}",
                'title': 'Retrieval-Augmented Generation',
                'type': 'TOPIC',
                'content': 'Learn to enhance your agents with external knowledge using RAG techniques.',
                'resources': ['https://www.pinecone.io/learn/retrieval-augmented-generation/'],
                'children': []
            },
            {
                'id': f"vector_embeddings_{uuid.uuid4().hex[:8]}",
                'title': 'Vector Embeddings',
                'type': 'TOPIC',
                'content': 'Understanding vector embeddings for semantic search and retrieval.',
                'resources': ['https://www.sbert.net/'],
                'children': []
            }
        ]
        
    elif knowledge_level == 'advanced':
        # For advanced: focus on cutting-edge techniques and systems
        agentic_ai_node['children'] = [
            {
                'id': f"multi_agent_systems_{uuid.uuid4().hex[:8]}",
                'title': 'Multi-Agent Systems',
                'type': 'TOPIC',
                'content': 'Design and implement systems with multiple collaborating AI agents.',
                'resources': ['https://arxiv.org/abs/2304.03442'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"reasoning_techniques_{uuid.uuid4().hex[:8]}",
                'title': 'Advanced Reasoning',
                'type': 'TOPIC',
                'content': 'Implement chain-of-thought, tree-of-thought, and other advanced reasoning methods.',
                'resources': ['https://arxiv.org/abs/2305.10601'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"agent_alignment_{uuid.uuid4().hex[:8]}",
                'title': 'Agent Alignment & Safety',
                'type': 'TOPIC',
                'content': 'Techniques for ensuring agents are aligned with human values and goals.',
                'resources': ['https://www.anthropic.com/research'],
                'highlight': True,
                'children': []
            },
            {
                'id': f"advanced_rag_{uuid.uuid4().hex[:8]}",
                'title': 'Advanced RAG Architectures',
                'type': 'TOPIC',
                'content': 'Cutting-edge retrieval systems like HyDE and multi-vector retrieval.',
                'resources': ['https://arxiv.org/abs/2212.10496'],
                'children': []
            },
            {
                'id': f"research_frontiers_{uuid.uuid4().hex[:8]}",
                'title': 'Research Frontiers',
                'type': 'TOPIC',
                'content': 'Stay current with the latest research and emerging techniques in agentic AI.',
                'resources': ['https://arxiv.org/list/cs.AI/recent'],
                'children': []
            }
        ]
    
    # Build the complete roadmap structure
    ai_category['children'].append(agentic_ai_node)
    roadmap['children'].append(ai_category)
    
    return roadmap


def create_agentic_ai_nodes_for_level(knowledge_level: str) -> List[Dict[str, Any]]:
    """
    Create agentic AI-specific nodes based on knowledge level
    This is used to add nodes to an existing roadmap, rather than creating a complete one.
    
    Args:
        knowledge_level: User's knowledge level
        
    Returns:
        List of nodes to add to the roadmap
    """
    nodes = []
    
    # Common node structure
    def create_node(title, content, node_type='TOPIC'):
        return {
            'id': f"agentic_{title.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}",
            'title': title,
            'type': node_type,
            'content': content,
            'children': []
        }
    
    # Add level-specific nodes
    if knowledge_level == 'beginner':
        nodes.append(create_node(
            "Understanding AI Agents",
            "Learn the fundamentals of AI agents, what they are, and how they work."
        ))
        nodes.append(create_node(
            "Prompt Engineering Basics",
            "Master the basics of crafting effective prompts for AI models."
        ))
        nodes.append(create_node(
            "LLM Foundations",
            "Understand how Large Language Models work and their capabilities."
        ))
        
    elif knowledge_level == 'intermediate':
        nodes.append(create_node(
            "Agent Frameworks",
            "Explore frameworks like LangChain and AutoGPT for building AI agents."
        ))
        nodes.append(create_node(
            "Tool Use Integration",
            "Learn how to integrate tools and APIs with your AI agents."
        ))
        nodes.append(create_node(
            "Agent Memory Systems",
            "Implement different memory architectures for persistent agent knowledge."
        ))
        
    elif knowledge_level == 'advanced':
        nodes.append(create_node(
            "Multi-Agent Systems",
            "Design and implement systems with multiple collaborating AI agents."
        ))
        nodes.append(create_node(
            "Advanced Reasoning Techniques",
            "Explore cutting-edge reasoning methods like chain-of-thought and tree of thought."
        ))
        nodes.append(create_node(
            "Research Frontiers",
            "Stay current with the latest research in agentic AI systems."
        ))
    
    return nodes
