#!/usr/bin/env python3
"""Wrapper for api_health_check from src/utils/"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'utils'))
from src.utils.api_health_check import *
if __name__ == "__main__":
    main()

