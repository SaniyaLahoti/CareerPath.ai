import os
import json
import uuid
from typing import Dict, Any, List, Optional
from roadmap_parser import RoadmapParser

class RoadmapNode:
    """Node class for the roadmap visualization, similar to your existing implementation"""
    def __init__(self, id: str, title: str, node_type: str, content: str = "", resources: List[str] = None, parent_id: Optional[str] = None):
        self.id = id
        self.title = title
        self.node_type = node_type
        self.content = content
        self.resources = resources or []
        self.parent_id = parent_id
        self.children = []
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.node_type,
            'content': self.content,
            'resources': self.resources,
            'children': [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        node = cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            node_type=data.get('type', 'TOPIC'),
            content=data.get('content', ''),
            resources=data.get('resources', [])
        )
        
        for child_data in data.get('children', []):
            child_node = cls.from_dict(child_data)
            node.add_child(child_node)
        
        return node
    
    def add_child(self, child: 'RoadmapNode'):
        child.parent_id = self.id
        self.children.append(child)
    
    def find_node_by_id(self, node_id: str) -> Optional['RoadmapNode']:
        if self.id == node_id:
            return self
        
        for child in self.children:
            found = child.find_node_by_id(node_id)
            if found:
                return found
        
        return None

class RoadmapGenerator:
    """
    Generates personalized roadmaps based on user interests
    by matching them with relevant roadmaps from the repository
    """
    
    def __init__(self, cache_dir: str = 'roadmap_cache'):
        self.parser = RoadmapParser(cache_dir=cache_dir)
        self.roadmap_keywords = {
            'ai': ['ai-agents', 'ai-engineer', 'prompt-engineering'],
            'web development': ['frontend', 'backend', 'javascript', 'react', 'nodejs'],
            'mobile': ['android', 'flutter', 'react-native'],
            'devops': ['devops', 'kubernetes', 'docker'],
            'python': ['python', 'django', 'fastapi'],
            'data science': ['data-science', 'machine-learning'],
            'software architecture': ['software-architect', 'system-design']
        }
    
    def create_initial_roadmap(self) -> RoadmapNode:
        """Create the initial empty roadmap structure"""
        return RoadmapNode(
            id='root',
            title='Your Career Path',
            node_type='ROOT',
            content='Your personalized career path roadmap'
        )
    
    def match_interests_to_roadmaps(self, interests: List[str]) -> List[str]:
        """Match user interests to available roadmaps"""
        matched_roadmaps = []
        
        for interest in interests:
            interest_lower = interest.lower()
            for keyword, roadmap_list in self.roadmap_keywords.items():
                if interest_lower in keyword or keyword in interest_lower:
                    matched_roadmaps.extend(roadmap_list)
        
        # Remove duplicates while preserving order
        unique_roadmaps = []
        for roadmap in matched_roadmaps:
            if roadmap not in unique_roadmaps:
                unique_roadmaps.append(roadmap)
        
        return unique_roadmaps
    
    def generate_roadmap_for_interests(self, interests: List[str]) -> Dict[str, Any]:
        """Generate a comprehensive roadmap based on user interests"""
        # Create the root roadmap node
        root_node = self.create_initial_roadmap()
        
        # Match interests to roadmaps
        matched_roadmaps = self.match_interests_to_roadmaps(interests)
        
        # For each matched roadmap, integrate it into our roadmap
        for roadmap_name in matched_roadmaps[:3]:  # Limit to top 3 to avoid overwhelming
            try:
                # Convert JSON to our node structure
                roadmap_data = self.parser.convert_to_roadmap_nodes(roadmap_name)
                
                # Create a category node for this roadmap
                category_node = RoadmapNode(
                    id=str(uuid.uuid4()),
                    title=self.parser._format_roadmap_title(roadmap_name),
                    node_type="CATEGORY",
                    content=f"Learning path for {self.parser._format_roadmap_title(roadmap_name)}"
                )
                
                # Add the roadmap's root children to our category
                for child in roadmap_data.get('children', []):
                    # Convert dict to RoadmapNode
                    child_node = self._dict_to_node(child)
                    if child_node:
                        category_node.add_child(child_node)
                
                # Add this category to our root
                root_node.add_child(category_node)
            
            except Exception as e:
                print(f"Error processing roadmap {roadmap_name}: {str(e)}")
                # Continue with other roadmaps if one fails
                continue
        
        # Return the roadmap as a dictionary
        return root_node.to_dict()
    
    def _dict_to_node(self, node_dict: Dict[str, Any], max_depth: int = 2, current_depth: int = 0) -> Optional[RoadmapNode]:
        """Convert a dictionary structure to RoadmapNode, with depth limiting"""
        if current_depth > max_depth:
            # Limit depth to prevent overly complex roadmaps
            return None
        
        node = RoadmapNode(
            id=node_dict.get('id', str(uuid.uuid4())),
            title=node_dict.get('title', 'Unknown'),
            node_type=node_dict.get('node_type', 'TOPIC'),
            content=node_dict.get('content', ''),
            resources=node_dict.get('resources', [])
        )
        
        # Process children up to the max depth
        for child_dict in node_dict.get('children', [])[:5]:  # Limit children per node
            child_node = self._dict_to_node(child_dict, max_depth, current_depth + 1)
            if child_node:
                node.add_child(child_node)
        
        return node
