import os
import subprocess
import threading
from flask import Flask

app = Flask(__name__)

# Start Chainlit in a separate thread
def run_chainlit():
    subprocess.run(["chainlit", "run", "app.py", "--host", "localhost", "--port", "8000"], check=True)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <meta http-equiv="refresh" content="0;url=http://localhost:8000" />
        <title>Redirecting to Chainlit</title>
    </head>
    <body>
        <p>Redirecting to Chainlit application...</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Start Chainlit in a background thread
    chainlit_thread = threading.Thread(target=run_chainlit)
    chainlit_thread.daemon = True
    chainlit_thread.start()
    
    # Get the port from environment variable
    port = int(os.environ.get("PORT", 10000))
    
    # Start Flask app
    app.run(host="0.0.0.0", port=port)
