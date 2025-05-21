import requests
import json
import os
from typing import Dict, Any, List, Optional

class RoadmapParser:
    """
    Parser for developer roadmaps from kamranahmedse/developer-roadmap
    """
    
    def __init__(self, cache_dir: str = 'roadmap_cache'):
        """Initialize the roadmap parser with optional caching"""
        self.base_url = 'https://raw.githubusercontent.com/kamranahmedse/developer-roadmap/master/src/data/roadmaps/'
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def fetch_roadmap_json(self, roadmap_name: str) -> Dict[str, Any]:
        """Fetch the JSON data for a roadmap"""
        cache_path = os.path.join(self.cache_dir, f"{roadmap_name}.json")
        
        # Check if we have a cached version
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
        
        # Fetch from GitHub
        url = f"{self.base_url}{roadmap_name}/{roadmap_name}.json"
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse and cache the data
        data = response.json()
        with open(cache_path, 'w') as f:
            json.dump(data, f)
        
        return data
    
    def fetch_content_file(self, roadmap_name: str, file_id: str) -> str:
        """Fetch a specific content file from the roadmap"""
        cache_path = os.path.join(self.cache_dir, f"{roadmap_name}_{file_id}.md")
        
        # Check cache first
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return f.read()
        
        # Extract the actual filename from ID (format is usually filename@id)
        parts = file_id.split('@')
        if len(parts) > 1:
            filename = f"{parts[0]}@{parts[1]}.md"
        else:
            filename = f"{file_id}.md"
        
        # Fetch from GitHub
        url = f"{self.base_url}{roadmap_name}/content/{filename}"
        response = requests.get(url)
        response.raise_for_status()
        
        content = response.text
        
        # Cache the content
        with open(cache_path, 'w') as f:
            f.write(content)
        
        return content
    
    def convert_to_roadmap_nodes(self, roadmap_name: str) -> Dict[str, Any]:
        """
        Convert the JSON roadmap data into a structured format
        suitable for CareerPath.AI visualization
        """
        json_data = self.fetch_roadmap_json(roadmap_name)
        
        # Extract nodes and edges from the JSON data
        nodes = json_data.get('nodes', [])
        
        # Create node lookup for quick access
        node_map = {}
        for node in nodes:
            if node.get('type') == 'text':
                node_id = node.get('id', '')
                node_map[node_id] = {
                    'id': node_id,
                    'title': node.get('data', {}).get('text', 'Unknown'),
                    'content': self._extract_content_from_node(node),
                    'node_type': self._determine_node_type(node),
                    'resources': [],
                    'children': []
                }
        
        # Build the tree structure by processing connections
        root_nodes = []
        connections = json_data.get('edges', [])
        
        # Build parent-child relationships
        for connection in connections:
            source = connection.get('source', '')
            target = connection.get('target', '')
            
            if source in node_map and target in node_map:
                parent = node_map[source]
                child = node_map[target]
                parent['children'].append(child)
            
        # Find root nodes (those without parents)
        for node_id, node in node_map.items():
            is_child = False
            for potential_parent in node_map.values():
                if any(child['id'] == node_id for child in potential_parent['children']):
                    is_child = True
                    break
            
            if not is_child:
                root_nodes.append(node)
        
        # Create the structured roadmap
        roadmap = {
            'id': f"{roadmap_name}_root",
            'title': self._format_roadmap_title(roadmap_name),
            'type': 'ROOT',
            'content': f"Your personalized {self._format_roadmap_title(roadmap_name)} roadmap",
            'children': root_nodes
        }
        
        return roadmap
    
    def _extract_content_from_node(self, node: Dict[str, Any]) -> str:
        """Extract content from a node, could be extended to fetch from content files"""
        content = node.get('data', {}).get('text', '')
        return content
    
    def _determine_node_type(self, node: Dict[str, Any]) -> str:
        """Determine the type of node (CATEGORY, TOPIC, etc.)"""
        # This is a simplistic approach - you might want to refine based on node properties
        style = node.get('data', {}).get('style', {})
        if style.get('backgroundColor') == '#2ecc71':
            return 'CATEGORY'
        elif style.get('backgroundColor') == '#3498db':
            return 'TOPIC'
        return 'TOPIC'
    
    def _format_roadmap_title(self, roadmap_name: str) -> str:
        """Format the roadmap name as a title"""
        # Convert something like 'ai-agents' to 'AI Agents'
        return ' '.join(word.capitalize() for word in roadmap_name.replace('-', ' ').split())

    def fetch_all_available_roadmaps(self) -> List[str]:
        """
        Fetch a list of all available roadmaps
        """
        # This would ideally query the GitHub API to get the list,
        # but for now we'll hardcode some common ones
        return [
            'ai-agents',
            'ai-engineer', 
            'frontend',
            'backend',
            'devops',
            'python',
            'javascript',
            'react',
            'android',
            'software-architect'
        ]
