import os
from typing import Dict, Any, List, Optional
from groq import Groq
import json
from user_knowledge_assessment import UserKnowledgeAssessment

class LLMChatHandler:
    """
    Handles chat interactions using the Groq API for natural language responses
    """
    
    def __init__(self):
        """Initialize the LLM chat handler with Groq client"""
        try:
            # Make sure we have an API key
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is not set")
                
            # Initialize Groq client
            self.client = Groq(api_key=api_key)  # Pass API key directly to constructor
            # Using a known valid model ID from Groq
            self.model = "llama-3.3-70b-versatile"  # Fallback to known working model
            
            # Print success message
            print(f"✅ Groq API key loaded successfully: {api_key[:5]}...")
            print(f"✅ Using model: {self.model}")
            
            # Never fall back to templates - always use API
            self.force_api_usage = True
            self.api_available = True
            print("✅ LLM Chat Handler initialized with FORCE_API_USAGE=True")
            
            # Test API connection
            self._test_api_connection()
            
        except Exception as e:
            print(f"⚠️ ERROR initializing Groq client: {str(e)}")
            print("⚠️ LLM responses will be limited to fallback templates")
            self.client = None
            self.force_api_usage = False
            self.api_available = False
    
    def _test_api_connection(self):
        """Test connection to Groq API"""
        try:
            # Make a simple API call to test connection
            print("Testing API connection...")
            
            # Print full API key info for debugging (first 5 chars)
            api_key = os.getenv("GROQ_API_KEY")
            print(f"API Key for test: {api_key[:5]}...{api_key[-3:]}")
            print(f"API Key length: {len(api_key) if api_key else 0}")
            
            # Verify the client is properly initialized
            if not self.client:
                print("ERROR: Groq client is None!")
                raise ValueError("Groq client failed to initialize")
                
            print(f"Making test call with model: {self.model}")
            
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "Hello"}],
                model=self.model,
                max_tokens=10,
                temperature=0.5
            )
            
            content = response.choices[0].message.content
            print(f"✅ API connection test successful! Response: {content}")
            
            if not content or content.strip() == "":
                print("WARNING: Empty response from API test call")
                
            self.api_available = True
            return True
        except Exception as e:
            print(f"⚠️ API connection test failed: {str(e)}")
            import traceback
            print(f"Exception traceback: {traceback.format_exc()}")
            self.api_available = False
            return False
            
        # Initialize knowledge assessment system
        self.knowledge_assessor = UserKnowledgeAssessment()
        
        # System prompt that guides the AI's behavior
        self.system_prompt = """
You are CareerPath.AI, a friendly and knowledgeable career guidance expert. Your goal is to help users explore career paths, 
understand different fields, and create personalized roadmaps. The user sees a split-screen interface: chat on the left and an 
interactive graphical roadmap visualization on the right.

Core Behaviors:
1. Be warm, conversational, and empathetic - speak directly to the user as a trusted advisor
2. IMPORTANT: Assess the user's knowledge level in their field of interest through natural conversation
3. Ask specific questions about their experience, skills, and background to gauge expertise level
4. Tailor your roadmap recommendations based on their knowledge level - skip basics for advanced users
5. Directly connect your advice to specific nodes or sections in the roadmap visualization
6. Always reference the visual roadmap that's being built on the right side of the screen
7. Be specific about career paths, required skills, and learning steps - avoid generic advice

Knowledge Assessment:
- For new users interested in a field, ask 2-3 assessment questions to determine their level
- Categories: Beginner (new to the field), Intermediate (some experience), Advanced (significant expertise)
- Customize roadmap content based on their level (e.g., skip basics for advanced users)
- Make your assessment conversational, not like a formal quiz

Agentic AI Focus:
- If users mention interest in AI agents, agentic AI, or autonomous systems, provide detailed guidance
- Reference the GitHub roadmap for AI agents which includes: fundamentals, prompt engineering, reasoning, tool use
- For beginners: focus on fundamentals, basic prompting, understanding of LLMs
- For intermediates: focus on frameworks, tool use patterns, memory systems
- For advanced users: focus on cutting-edge techniques like multi-agent systems

Roadmap Interaction:
- The roadmap displays as a hierarchical tree with clickable nodes
- New interests are added as connected nodes based on the user's expertise level
- Encourage users to explore the roadmap by clicking on nodes for more details

Session Goal: Create a truly personalized learning path that respects the user's existing knowledge.
"""
    
    def generate_response(self, 
                         user_message: str, 
                         conversation_history: List[Dict[str, str]],
                         identified_interests: List[str],
                         roadmap_updated: bool = False,
                         assessment_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a contextual response based on the user's message and conversation history.
        Incorporates knowledge assessment to tailor roadmap content.
        
        Args:
            user_message: The current message from the user
            conversation_history: List of previous messages in the conversation
            identified_interests: List of interests identified so far
            roadmap_updated: Whether the roadmap was just updated
            assessment_state: Current state of knowledge assessment (if any)
            
        Returns:
            A dictionary containing the response and assessment information
        """
        # Initialize or use existing assessment state
        if assessment_state is None:
            assessment_state = self.knowledge_assessor.create_new_assessment_state()
        
        # Handle knowledge assessment if we have identified interests
        is_agentic_ai_interest = any(interest.lower() in ['ai', 'artificial intelligence', 'agentic ai'] 
                                 for interest in identified_interests)
        
        # Check if we should proceed with assessment
        should_assess = is_agentic_ai_interest and self.knowledge_assessor.is_assessment_question_needed(user_message, assessment_state)
        
        # Perform knowledge assessment if needed
        assessment_question = None
        if should_assess:
            # Before completing assessment, analyze the current response
            if len(assessment_state.get('asked_questions', [])) > 0:
                self.knowledge_assessor.analyze_response('agentic ai', user_message, assessment_state)
            
            # Get the next question if assessment is not complete
            if not assessment_state.get('assessment_complete', False):
                assessment_question = self.knowledge_assessor.get_next_question('agentic ai', assessment_state)
        
        # Create messages for the API
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add full conversation history
        messages.extend(conversation_history)  # Include all messages for complete context
        
        # Add information about identified interests, roadmap, and assessment
        context_parts = []
        
        # Add interest information
        interest_context = "Based on our conversation, I've identified these interests: "
        interest_context += ", ".join(identified_interests) if identified_interests else "none yet"
        context_parts.append(interest_context)
        
        # Add roadmap update information
        if roadmap_updated:
            context_parts.append("I've just updated your roadmap visualization with this information.")
        
        # Add knowledge assessment information if available
        if assessment_state.get('knowledge_level'):
            level = assessment_state.get('knowledge_level')
            context_parts.append(f"I've assessed the user's knowledge level as: {level}")
            
            # Add recommendations for roadmap customization if assessment is complete
            if assessment_state.get('assessment_complete') and is_agentic_ai_interest:
                recommendations = self.knowledge_assessor.generate_roadmap_recommendations('agentic ai', assessment_state)
                
                if recommendations.get('skip_basics', False):
                    context_parts.append("The user has prior experience, so skip basic introductory content.")
                    
                if recommendations.get('include_advanced', False):
                    context_parts.append("The user is advanced, so focus on cutting-edge techniques and advanced topics.")
                    
                if recommendations.get('focus_areas'):
                    focus_areas = ', '.join(recommendations.get('focus_areas'))
                    context_parts.append(f"Focus areas for this user: {focus_areas}")
                    
                if recommendations.get('skip_areas'):
                    skip_areas = ', '.join(recommendations.get('skip_areas'))
                    context_parts.append(f"Skip these areas for this user: {skip_areas}")
        
        # Add full context to messages
        messages.append({"role": "system", "content": "\n".join(context_parts)})
        
        # If we have an assessment question, prepare to include it in the response
        if assessment_question:
            messages.append({"role": "system", "content": f"IMPORTANT: Include this assessment question naturally in your response: '{assessment_question}' Ask this to gauge the user's knowledge level in agentic AI."})
        
        # Prepare the response object
        result = {
            'text': '',
            'assessment_state': assessment_state,
            'assessment_in_progress': should_assess,
            'knowledge_level': assessment_state.get('knowledge_level'),
            'assessment_complete': assessment_state.get('assessment_complete', False)
        }
        
        try:
            # FORCE API USAGE: We want to always try to use the API
            # even if previous checks marked it as unavailable
            print("\n🔄 ATTEMPTING LLM API CALL - FORCING API USAGE")
            
            # Re-initialize API client if it's None
            if not self.client:
                print("Re-initializing API client")
                api_key = os.getenv("GROQ_API_KEY")
                if api_key:
                    self.client = Groq(api_key=api_key)
                    print(f"Re-initialized client with API key: {api_key[:5]}...")
                else:
                    print("❌ CRITICAL ERROR: Still no API key available")
                    
            # Always set API to available to force a try
            self.api_available = True
            print(f"API client status: {self.client is not None}")
                
            # Log when we're making an API call
            print(f"Making Groq API call for response, convo length: {len(conversation_history)}")
            
            # Print conversation history for debugging
            print("\nConversation context being sent to API:")
            print(f"Total messages in context: {len(conversation_history)}")
            for i, msg in enumerate(conversation_history[-10:]):  # Show last 10 for brevity in logs
                print(f"[{i}] {msg['role'].upper()}: {msg['content'][:50]}...")
            print()
                
            # Generate response using Groq
            try:
                print(f"Making API call to Groq with model: {self.model}")
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=0.7,
                    max_tokens=500,
                    top_p=1,
                    stream=False
                )
                
                # Extract the content and log it
                content = response.choices[0].message.content
                print(f"Received response from API: {content[:100]}...")
                
                # Make sure we have valid content
                if not content or content.strip() == "":
                    raise ValueError("Empty response received from API")
                    
                result['text'] = content
                print("✅ Successfully generated LLM response")
                return result
                
            except Exception as inner_e:
                print(f"❌ Error during API call: {str(inner_e)}")
                # Provide a default response instead of throwing an error
                result['text'] = f"I'm having trouble connecting to my language model right now. Could you please share what career fields interest you?"
                return result
        
        except Exception as e:
            print(f"Error generating LLM response: {str(e)}")
            
            # Only use fallback if we're not forcing API usage
            if not self.force_api_usage:
                result['text'] = self._get_smart_fallback_response(
                    user_message, 
                    identified_interests, 
                    conversation_history,
                    assessment_state,
                    assessment_question
                )
            else:
                # If we're forcing API usage, return the error message directly
                result['text'] = f"I apologize, but I'm experiencing technical difficulties connecting to my knowledge base (Error: {str(e)}). Please try again in a moment."
                print("WARNING: Returning error message due to FORCE_API_USAGE=True")
                
            return result
    
    def extract_interests_from_message(self, message: str, conversation_history: List[Dict[str, str]]) -> List[str]:
        """
        Use the LLM to extract career interests from the user's message more intelligently
        
        Args:
            message: The current message from the user
            conversation_history: Previous messages for context
            
        Returns:
            List of extracted interests
        """
        # Create a specialized prompt for interest extraction
        system_prompt = """
You are an AI specialized in identifying career interests from conversations.

Your task is to analyze the text and extract specific career fields, technologies, roles, or industries the user expresses interest in.

CONSIDER THESE CAREER DOMAINS:
- Computer Science/Software Engineering (programming, development, coding)
- Data Science & Analytics (data analysis, statistics, big data)
- Artificial Intelligence (AI, ML, deep learning, NLP, neural networks)
- Web Development (frontend, backend, full-stack, HTML/CSS/JS, web frameworks)
- Mobile App Development (iOS, Android, cross-platform, app design)
- Cloud Computing (AWS, Azure, GCP, serverless, DevOps)
- Cybersecurity (network security, ethical hacking, security engineering)
- UI/UX Design (user interface, user experience, design thinking)
- Game Development (game design, game programming, 3D modeling)
- Blockchain/Cryptocurrency (blockchain development, smart contracts, Web3)
- Project Management (agile, scrum, product management)
- Digital Marketing (SEO, content marketing, social media)

MORE SPECIFIC ROLES:
- Machine Learning Engineer, Data Engineer, AI Researcher
- Frontend Developer, Backend Developer, Full-Stack Developer
- DevOps Engineer, Site Reliability Engineer, Cloud Architect
- Cybersecurity Analyst, Penetration Tester, Security Consultant
- UI Designer, UX Researcher, Product Designer
- Game Programmer, Game Artist, 3D Modeler
- Blockchain Developer, Smart Contract Engineer

Extract interests based on EXPLICIT mentions OR STRONG implications. Return ONLY a JSON array of lowercase strings.
Return an empty array if no career interests are detected.
Example outputs: ["machine learning", "artificial intelligence"], ["web development", "javascript"], []
"""
        
        # Add recent conversation context
        messages = [{"role": "system", "content": system_prompt}]
        context = "Here's the recent conversation (analyze all of it for interests):\n\n"
        
        # Add up to 3 previous messages for context
        for msg in conversation_history[-3:]:
            context += f"{msg['role']}: {msg['content']}\n"
        
        # Add current message
        context += f"Current message: {message}"
        messages.append({"role": "user", "content": context})
        
        try:
            # Check if API is available
            if not hasattr(self, 'api_available') or not self.api_available or not self.client:
                print("API not available - using fallback interest extraction")
                return self._basic_interest_extraction(message)
            
            print(f"Making Groq API call for interest extraction")
            # Generate interests using LLM
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.2,  # Lower temperature for more focused extraction
                max_tokens=100,
                top_p=1,
                stream=False
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Raw interest extraction result: {result}")
            
            # Try to parse the response as JSON
            try:
                interests = json.loads(result)
                if isinstance(interests, list):
                    print(f"Extracted interests from API: {interests}")
                    return interests
            except Exception as json_error:
                print(f"Failed to parse JSON from interest extraction: {str(json_error)}")
                # If JSON parsing fails, do basic extraction
                pass
                
            # Fallback to basic keyword extraction
            extracted = self._basic_interest_extraction(message)
            print(f"Falling back to keyword extraction: {extracted}")
            return extracted
            
        except Exception as e:
            print(f"Error extracting interests via API: {str(e)}")
            # Fallback to basic extraction if API fails
            extracted = self._basic_interest_extraction(message)
            print(f"Extraction fallback due to error: {extracted}")
            return extracted
    
    def _get_smart_fallback_response(self, 
                                 user_message: str, 
                                 identified_interests: List[str], 
                                 conversation_history: List[Dict[str, str]],
                                 assessment_state: Optional[Dict[str, Any]] = None,
                                 assessment_question: Optional[str] = None) -> str:
        """Generate a contextual response without using the LLM API, focusing on roadmap integration"""
        message_lower = user_message.lower()
        
        # Create a more personalized response by tracking chat state
        first_time_user = len(conversation_history) <= 2
        has_interests = bool(identified_interests)
        is_question = '?' in user_message
        is_short_greeting = len(user_message) < 10 and any(greeting in message_lower for greeting in ['hi', 'hello', 'hey'])
        is_frustrated = any(term in message_lower for term in ['not working', 'doesn\'t work', 'wrong', 'error', 'problem', 'issue'])
        asks_about_roadmap = any(term in message_lower for term in ['roadmap', 'visualization', 'diagram', 'map', 'graph', 'chart'])
        asks_how_to = 'how' in message_lower and any(term in message_lower for term in ['start', 'begin', 'learn', 'do'])
        
        # Incorporate assessment question if we have one
        if assessment_question:
            if 'agentic ai' in ' '.join(identified_interests).lower():
                return f"Thanks for your interest in Agentic AI! To create a customized roadmap specifically for you, I'd like to understand your current knowledge level. {assessment_question} This will help me tailor the content in your roadmap visualization to your specific needs."
        
        # Check for knowledge level if assessment is complete
        knowledge_level = assessment_state.get('knowledge_level') if assessment_state else None
        
        # Welcome/greeting handling
        if is_short_greeting:
            return "Hi there! Welcome to CareerPath.AI. I'm here to help you explore career paths with our interactive visualization. As we chat, I'll build a personalized roadmap for you on the right side of your screen. What fields or technologies interest you?"
            
        # Discussing the roadmap visualization
        if asks_about_roadmap:
            return "The roadmap visualization on the right side of your screen is interactive! As we identify your interests, I'll add new nodes to the diagram. You can click on any node to see more details about that career path or skill. Would you like me to explain any specific part of your current roadmap?"
            
        # First substantive interaction
        if first_time_user:
            if has_interests:
                interests_str = ", ".join(interest.title() for interest in identified_interests)
                
                # Special handling for agentic AI
                if any(interest.lower() in ['ai', 'artificial intelligence', 'agentic ai'] for interest in identified_interests):
                    if assessment_question:
                        return f"Thanks for sharing your interest in {interests_str}! I've added this to your roadmap visualization on the right. To customize it specifically for you, I'd like to know: {assessment_question} This will help me tailor the content to your experience level."
                    else:
                        return f"Thanks for sharing your interest in {interests_str}! I've added these to your roadmap visualization on the right. You can see the nodes representing these career paths. To create a truly personalized roadmap, could you tell me about your previous experience with {interests_str}?"
                else:
                    return f"Thanks for sharing your interest in {interests_str}! I've added these to your roadmap visualization on the right. You can see the nodes representing these career paths. Click on any node to explore details. What specific aspects of {interests_str} would you like to learn more about?"
            else:
                return "I'm here to help you build a personalized career roadmap. Take a look at the visualization panel on the right - as you share your interests with me, I'll create an interactive roadmap for you. What fields are you interested in exploring? For example: web development, data science, AI, or cybersecurity?"
        
        # Handle questions about how to proceed in a field
        if is_question and asks_how_to and has_interests:
            interest = identified_interests[0].title()
            
            # Tailor response based on knowledge level for AI
            if interest.lower() in ['ai', 'artificial intelligence', 'agentic ai'] and knowledge_level:
                if knowledge_level == 'beginner':
                    return f"Great question about getting started in {interest}! Since you're new to this field, I've highlighted foundational concepts in your roadmap visualization on the right. Start with the basics of AI and machine learning before diving into agentic systems. Would you like me to explain any specific foundational concept first?"
                elif knowledge_level == 'intermediate':
                    return f"Great question about advancing in {interest}! Based on your experience, I've customized the roadmap on the right to focus on intermediate concepts. Look at the highlighted nodes about agent frameworks and tool use patterns. Would you like me to explain any specific implementation technique?"
                elif knowledge_level == 'advanced':
                    return f"Great question about mastering {interest}! Given your advanced experience, I've focused your roadmap visualization on cutting-edge techniques. Check out the highlighted nodes on multi-agent systems and advanced reasoning techniques. Would you like to discuss any particular research direction?"
            else:
                return f"Great question about getting started in {interest}! I've outlined some key steps in your roadmap visualization (on the right). Look for the highlighted nodes that show the recommended learning path. Would you like me to explain specific skills or resources you should focus on first?"
        
        # Handle other questions about fields of interest
        if is_question and has_interests:
            interest = identified_interests[0].title()
            
            # For agentic AI with knowledge assessment complete
            if interest.lower() in ['ai', 'artificial intelligence', 'agentic ai'] and knowledge_level and assessment_state.get('assessment_complete', False):
                if knowledge_level == 'beginner':
                    return f"That's a great question about {interest}! I've customized your roadmap visualization on the right for beginners. I've included fundamental concepts that will help you build a strong foundation. You can click on each node to explore specific details. Which of these foundational concepts interests you most?"
                elif knowledge_level == 'intermediate':
                    return f"That's a great question about {interest}! Based on your experience level, I've customized the roadmap on the right to focus on practical implementation. You can see nodes covering frameworks and design patterns that will help you build effective AI agents. Which specific implementation approach would you like to explore?"
                elif knowledge_level == 'advanced':
                    return f"That's a great question about {interest}! Given your advanced knowledge, I've tailored the roadmap on the right to focus on cutting-edge techniques and research areas. You'll find nodes covering multi-agent systems and advanced reasoning methods. Which frontier topic would you like to discuss in depth?"
            else:
                return f"That's a great question about {interest}! Take a look at your roadmap visualization on the right - I've included relevant information in the nodes. You can click on each node to explore specific details. Is there a particular aspect of {interest} you'd like me to elaborate on?"
            
        # User expresses frustration
        if is_frustrated:
            if has_interests:
                return "I apologize for any confusion. Let's refocus on your interests. I've created a roadmap visualization for you on the right based on what we've discussed so far. You can click on any node to see more details. Would you like me to explain any part of the roadmap, or shall we explore new areas?"
            else:
                return "I apologize for any confusion. Let's start fresh. Tell me about your career interests, and I'll build a personalized roadmap visualization for you on the right side of your screen. What fields or technologies interest you most?"
        
        # Follow-up with existing interests
        if has_interests:
            if len(identified_interests) > 1:
                # Multiple interests - offer to explore connections
                interests_str = ", ".join(interest.title() for interest in identified_interests[:2])
                return f"I've updated your roadmap with your interests in {interests_str}. Take a look at the visualization on the right - you can see how these fields connect. Would you like to explore how these areas overlap, or would you prefer to dive deeper into one specific field?"
            else:
                # Single interest - suggest exploring deeper with knowledge assessment if relevant
                interest = identified_interests[0].title()
                
                # For AI interests with no assessment yet
                if interest.lower() in ['ai', 'artificial intelligence', 'agentic ai'] and not knowledge_level and assessment_question:
                    return f"I've added {interest} to your roadmap visualization. To customize it specifically for your needs, could you tell me: {assessment_question} This will help me tailor the roadmap to your experience level."
                # For AI interests with completed assessment
                elif interest.lower() in ['ai', 'artificial intelligence', 'agentic ai'] and knowledge_level:
                    level_descriptions = {
                        'beginner': "I've customized your roadmap with foundational concepts for beginners in",
                        'intermediate': "I've adjusted your roadmap to focus on implementation techniques for intermediate users in",
                        'advanced': "I've tailored your roadmap to highlight advanced concepts and research areas in"
                    }
                    level_msg = level_descriptions.get(knowledge_level, "I've added")
                    return f"{level_msg} {interest}. Check out the nodes on the right that match your experience level. Would you like to explore specific aspects of the roadmap that I've customized for you?"
                else:
                    return f"I've added {interest} to your roadmap visualization. Check out the nodes on the right showing different roles and skills within this field. Would you like to explore specific career paths, required skills, or learning resources for {interest}?"
        
        # No interests identified yet - encourage sharing
        return "As we chat, I'll build a personalized career roadmap visualization for you on the right side of your screen. To get started, please share what fields, technologies, or roles you're interested in exploring. The more specific you can be, the better I can tailor your roadmap!"
            
    def _basic_interest_extraction(self, message: str) -> List[str]:
        """Enhanced keyword-based interest extraction with special handling for agentic AI and user knowledge assessment"""
        interests = []
        message_lower = message.lower()
        
        # Primary career domains with related keywords
        keywords = {
            'computer science': ['programming', 'code', 'software', 'developer', 'computer science', 'coding', 'development', 'engineer', 'engineering'],
            'artificial intelligence': ['artificial intelligence', 'ai', 'machine learning', 'ml', 'neural networks', 'deep learning', 'nlp', 'computer vision', 'ai engineer', 'ai research'],
            'web development': ['web', 'frontend', 'backend', 'fullstack', 'html', 'css', 'javascript', 'web design', 'web app', 'react', 'angular', 'vue', 'node', 'php'],
            'data science': ['data', 'analytics', 'statistics', 'data science', 'visualization', 'big data', 'data engineering', 'data analysis', 'business intelligence', 'bi', 'database'],
            'cybersecurity': ['security', 'cyber', 'hacking', 'encryption', 'privacy', 'network security', 'infosec', 'security analyst', 'penetration testing', 'pen test', 'ethical hacking'],
            'mobile development': ['mobile', 'app development', 'android', 'ios', 'flutter', 'react native', 'swift', 'kotlin', 'mobile app', 'app design'],
            'game development': ['game', 'gaming', 'unity', 'unreal', '3d', 'game design', 'game programming', 'game developer', 'game engine', 'level design'],
            'cloud computing': ['cloud', 'aws', 'azure', 'gcp', 'devops', 'infrastructure', 'serverless', 'docker', 'kubernetes', 'microservices', 'devsecops'],
            'ui/ux design': ['ui', 'ux', 'user interface', 'user experience', 'design', 'wireframe', 'prototype', 'figma', 'sketch', 'adobe xd', 'visual design'],
            'blockchain': ['blockchain', 'crypto', 'cryptocurrency', 'web3', 'smart contract', 'ethereum', 'nft', 'defi', 'distributed ledger', 'bitcoin'],
            'project management': ['project management', 'agile', 'scrum', 'kanban', 'product management', 'product owner', 'project manager', 'sprint', 'jira', 'pmp'],
            'digital marketing': ['marketing', 'seo', 'content marketing', 'social media', 'analytics', 'digital marketing', 'growth hacking', 'ppc', 'google ads', 'facebook ads']
        }
        
        # Check for job titles or role mentions (more specific)
        specific_roles = {
            'frontend developer': ['frontend developer', 'front-end developer', 'front end developer', 'ui developer'],
            'backend developer': ['backend developer', 'back-end developer', 'back end developer', 'api developer'],
            'full stack developer': ['full stack developer', 'fullstack developer', 'full-stack developer'],
            'data scientist': ['data scientist', 'data science professional', 'data science career'],
            'data engineer': ['data engineer', 'data pipeline', 'etl developer', 'data infrastructure'],
            'machine learning engineer': ['machine learning engineer', 'ml engineer', 'ml specialist'],
            'cybersecurity analyst': ['cybersecurity analyst', 'security analyst', 'infosec analyst', 'security specialist'],
            'devops engineer': ['devops engineer', 'site reliability engineer', 'sre', 'devops specialist', 'infrastructure engineer'],
            'cloud architect': ['cloud architect', 'solutions architect', 'aws architect', 'azure architect'],
            'ui/ux designer': ['ui designer', 'ux designer', 'ui/ux designer', 'product designer', 'interaction designer', 'user experience designer']
        }
        
        # First check for specific roles (higher priority)
        for role, terms in specific_roles.items():
            if any(term in message_lower for term in terms):
                interests.append(role)
        
        # Then check for broader domains
        for field, terms in keywords.items():
            if any(term in message_lower for term in terms) and not any(field in interest for interest in interests):
                interests.append(field)
        
        # Handle some specific combination cases
        if 'data' in message_lower and 'machine learning' in message_lower and 'machine learning engineer' not in interests:
            if 'artificial intelligence' not in interests and 'data science' not in interests:
                interests.append('data science')
                interests.append('artificial intelligence')
        
        return interests
