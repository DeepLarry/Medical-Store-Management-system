import sys
import os

# Add the 'backend' directory to the Python path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

# Vercel requires the variable to be named 'app'
# This is already correctly named

if __name__ == "__main__":
    app.run()
