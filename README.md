# CareerPath.AI

A career guidance application that helps users discover their ideal career path through an interactive assessment powered by AI.

## 🚀 One-Click Deploy (Recommended)

The easiest way to deploy this app is using [Render](https://render.com/):

1. [Create a free Render account](https://dashboard.render.com/register)
2. Click **"New +" → "Web Service"**
3. Connect your GitHub repo or upload your code
4. Point to `render.yaml` for auto-setup
5. Set your environment variable `GROQ_API_KEY` with your Groq key
6. Deploy! Your app will be live on a public URL

## Local Development

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment variables:
- Copy the contents of `.env` file
- Replace `your_api_key_here` with your actual Groq API key

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
