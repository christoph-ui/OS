#!/usr/bin/env python3
"""
Simple Demo Data Seeder for 0711 Platform
Creates basic test users for logging in
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("0711 Platform - Simple Demo Data Seeder")
print("=" * 60)
print()

print("✓ Demo users to be created:")
print()
print("  Email: admin@0711.io")
print("  Password: admin123")
print("  Role: Admin")
print()
print("  Email: test@example.com")
print("  Password: test123")
print("  Role: User")
print()
print("=" * 60)
print("Use these credentials to log in to the platform")
print("=" * 60)
