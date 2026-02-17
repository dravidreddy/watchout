import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

def print_routes():
    print("Registered Routes:")
    for route in app.routes:
        print(f"{route.methods} {route.path}")

if __name__ == "__main__":
    print_routes()
