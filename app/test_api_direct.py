#!/usr/bin/env python3
"""
Direct test of identity groups API
"""
import requests
import json

# Test the API endpoint directly
url = 'http://127.0.0.1:7860/api/identity-groups'

try:
    # Make request without authentication
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Headers: {response.headers}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nResponse type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            
            if 'groups' in data:
                groups = data['groups']
                print(f"\nGroups type: {type(groups)}")
                
                if isinstance(groups, list):
                    print(f"Number of groups: {len(groups)}")
                    if groups:
                        print(f"\nFirst group structure:")
                        print(json.dumps(groups[0], indent=2))
                else:
                    print(f"Groups is not a list: {type(groups)}")
        else:
            print(f"Response is not a dict: {data}")
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()