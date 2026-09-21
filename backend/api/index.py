import os
import sys

# Ensure parent directory is in sys.path so main, models, database, etc. can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Export app for Vercel Serverless Function engine
__all__ = ["app"]
