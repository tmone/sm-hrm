#!/usr/bin/env python3
"""
Test the identity groups API
"""
import requests
import json

# Test the API endpoint
try:
    response = requests.get('http://localhost:7860/api/identity-groups')
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response type: {type(data)}")
        print(f"Response keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        
        if 'groups' in data:
            groups = data['groups']
            print(f"Groups type: {type(groups)}")
            print(f"Number of groups: {len(groups) if hasattr(groups, '__len__') else 'No length'}")
            
            if groups:
                # Show first group structure
                if isinstance(groups, list):
                    print(f"First group: {groups[0] if groups else 'Empty list'}")
                elif isinstance(groups, dict):
                    first_key = list(groups.keys())[0] if groups else None
                    print(f"First group key: {first_key}")
                    print(f"First group value: {groups[first_key] if first_key else 'Empty dict'}")
                    
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")