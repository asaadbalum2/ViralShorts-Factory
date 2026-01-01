#!/usr/bin/env python3
"""
ViralShorts Factory - Main Entry Point
=======================================
This is a wrapper that imports from the reorganized structure.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'enhancements'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'analytics'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'quota'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'platforms'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'ai'))

# Import and run the actual generator
from src.core.pro_video_generator import *

if __name__ == "__main__":
    main()

