#!/usr/bin/env python3
"""
Test script to debug import issues
"""

try:
    print("Testing basic imports...")
    import sys
    print(f"Python path: {sys.path}")
    
    print("Testing pymongo...")
    import pymongo
    print("✓ pymongo imported")
    
    print("Testing motor...")
    import motor
    print("✓ motor imported")
    
    print("Testing database_optimizer...")
    import app.utils.database_optimizer as db_opt
    print("✓ database_optimizer imported")
    
    print("Available in module:", [name for name in dir(db_opt) if not name.startswith('_')])
    
    print("Testing OptimizedQueryBuilder import...")
    from app.utils.database_optimizer import OptimizedQueryBuilder
    print("✓ OptimizedQueryBuilder imported")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
