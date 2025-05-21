from roadmap_generator import RoadmapGenerator
from typing import Dict, Any, List
import json
import os

# Initialize the roadmap generator
roadmap_gen = RoadmapGenerator(cache_dir='roadmap_cache')

def update_roadmap_with_dynamic_content(current_roadmap, interests):
    """
    Update the user's roadmap with dynamically generated content from the developer roadmaps
    
    This function integrates with the app.py update_roadmap_based_on_interests function
    """
    if not interests:
        return current_roadmap
    
    try:
        # Generate a dynamic roadmap based on user interests
        dynamic_roadmap = roadmap_gen.generate_roadmap_for_interests(interests)
        
        # If we don't have a current roadmap, return the dynamic one
        if not current_roadmap or 'children' not in current_roadmap:
            return dynamic_roadmap
        
        # Merge the dynamic roadmap with the current one
        # Here we're preserving the root but adding new children
        existing_ids = [child.get('id') for child in current_roadmap.get('children', [])]
        
        # Add new categories from the dynamic roadmap if they don't exist
        for child in dynamic_roadmap.get('children', []):
            if child.get('id') not in existing_ids:
                current_roadmap['children'].append(child)
                existing_ids.append(child.get('id'))
        
        return current_roadmap
        
    except Exception as e:
        print(f"Error updating roadmap with dynamic content: {str(e)}")
        # Return the original roadmap if something goes wrong
        return current_roadmap

def get_available_roadmaps():
    """
    Get a list of all available roadmaps for reference
    """
    return roadmap_gen.parser.fetch_all_available_roadmaps()

def initialize_roadmap_cache():
    """
    Pre-cache some commonly used roadmaps to improve performance
    """
    try:
        common_roadmaps = ['ai-agents', 'frontend', 'backend', 'python']
        for roadmap_name in common_roadmaps:
            print(f"Pre-caching roadmap: {roadmap_name}")
            roadmap_gen.parser.fetch_roadmap_json(roadmap_name)
        print("Roadmap cache initialization complete")
    except Exception as e:
        print(f"Error initializing roadmap cache: {str(e)}")

# Create a simple test function to verify the integration works
def test_roadmap_generation():
    """Test function to verify roadmap generation works correctly"""
    test_interests = ['AI', 'Web Development']
    roadmap = roadmap_gen.generate_roadmap_for_interests(test_interests)
    
    # Save output to a test file
    with open('test_roadmap.json', 'w') as f:
        json.dump(roadmap, f, indent=2)
    
    print(f"Test roadmap generated with {len(roadmap.get('children', []))} top-level nodes")
    return roadmap

# Initialize the cache if this file is run directly
if __name__ == "__main__":
    initialize_roadmap_cache()
    test_roadmap = test_roadmap_generation()
    print(f"Test complete. Check test_roadmap.json for results")
