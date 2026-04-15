#!/usr/bin/env python
"""Database initialization script"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from server import app, init_db

if __name__ == "__main__":
    with app.app_context():
        init_db()
        print("✅ Database initialized successfully!")
