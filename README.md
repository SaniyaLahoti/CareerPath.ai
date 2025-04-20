# CareerPath.AI

A career guidance application that helps users discover their ideal career path through an interactive assessment powered by AI.

## 🚀 Deploy to Railway (Recommended)

Railway is the simplest way to deploy Chainlit apps:

1. [Sign up for Railway](https://railway.app/) (free tier available)
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Connect to your GitHub repository
4. Under **"Variables"**, add your environment variable:
   - `GROQ_API_KEY`: Your Groq API key
5. Deploy! Railway will automatically detect and deploy your app

## Local Development

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
- Copy the contents of `.env` file
- Replace with your actual Groq API key

3. Start the application:
```bash
chainlit run app.py
```

The application will be available at http://localhost:8000 (or your chosen port)

## Features

- Interactive, emotionally intelligent career assessment quiz
- AI-powered career path recommendations
- User-friendly chat interface
- Personalized guidance based on interests, skills, and personality

---

**Note:** Netlify and Vercel are not suitable for Python backend apps like Chainlit. Use Render, Railway, or Fly.io for easiest deployment.
