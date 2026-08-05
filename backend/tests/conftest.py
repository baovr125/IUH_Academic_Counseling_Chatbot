"""
Shared pytest fixtures and configuration for backend tests.
"""
import sys
import os

# Ensure backend root is on the path so `from app.xxx` imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
