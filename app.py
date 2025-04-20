import os
import chainlit as cl
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq()
client.api_key = os.getenv("GROQ_API_KEY")

INITIAL_PROMPT = """You are a friendly, empathetic career guidance expert at CareerPath.AI. Your style is concise, warm, and supportive.

Follow these guidelines strictly:
1. Keep your responses brief and to the point - use 1-3 short paragraphs maximum
2. Ask only one clear, focused question at a time
3. Be emotionally intelligent - recognize signs of frustration, uncertainty, or demotivation and respond with empathy
4. Provide actionable, practical steps for each career path you suggest
5. Tailor your advice to the user's specific circumstances, skills, and interests
6. When suggesting resources, be specific (books, courses, websites)

When the user expresses negative emotions or doubts:
- Acknowledge their feelings first
- Offer reassurance and perspective
- Share a practical next step they can take

Maintain a conversational, friendly tone while being professional and direct."""

@cl.on_chat_start
async def start():
    # Create and send initial message
    await cl.Message(content="Hi there! I'm your CareerPath.AI advisor. How can I help with your career journey today?").send()
    
    # Initialize the session with the system prompt
    cl.user_session.set("history", [
        {"role": "system", "content": INITIAL_PROMPT}
    ])

@cl.on_message
async def main(message: cl.Message):
    try:
        # Get conversation history
        history = cl.user_session.get("history")
        
        if history is None:
            history = [{"role": "system", "content": INITIAL_PROMPT}]
        
        # Add user's message to history
        history.append({"role": "user", "content": message.content})
        
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
        
        # Finalize the message stream
        await msg.update()
        
        # Add assistant's response to history
        history.append({"role": "assistant", "content": full_response})
        
        # Update the session history
        cl.user_session.set("history", history)
        
    except Exception as e:
        await cl.Message(content=f"An error occurred: {str(e)}").send()
