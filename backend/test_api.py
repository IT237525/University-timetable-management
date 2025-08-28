#!/usr/bin/env python
"""
Simple test script to verify API endpoints
Run this after starting the Django server
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure Django is running on port 8000.")
        return False

def test_admin_endpoint():
    """Test the admin endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/admin/")
        print(f"Admin Endpoint: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server.")
        return False

def test_api_endpoints():
    """Test various API endpoints"""
    endpoints = [
        "users/",
        "batches/",
        "subjects/",
        "rooms/",
        "timetables/",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}")
            print(f"{endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"{endpoint}: Connection Error")

def main():
    """Main test function"""
    print("Testing University Timetable Management System API")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1. Testing Health Endpoint:")
    health_ok = test_health_endpoint()
    
    # Test admin endpoint
    print("\n2. Testing Admin Endpoint:")
    admin_ok = test_admin_endpoint()
    
    # Test API endpoints
    print("\n3. Testing API Endpoints:")
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    if health_ok and admin_ok:
        print("✅ Basic system is working!")
        print("You can now:")
        print("- Access admin at: http://127.0.0.1:8000/admin/")
        print("- Use API at: http://127.0.0.1:8000/api/")
        print("- Login with: admin/admin")
    else:
        print("❌ Some tests failed. Check the server logs.")

if __name__ == "__main__":
    main()
