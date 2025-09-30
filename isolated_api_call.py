#!/usr/bin/env python3
"""
Isolated Google Ads API call script.
This script runs in a separate process to ensure complete state isolation.
"""

import sys
import json
import os
import requests
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from auth import get_credentials, get_headers, format_customer_id, API_VERSION

def make_api_call(url, headers, payload):
    """Make a single Google Ads API call with fresh state."""
    try:
        # Create a completely fresh session
        session = requests.Session()
        
        # Set headers to prevent caching
        session.headers.update({
            'User-Agent': 'GoogleAdsMCP-Isolated/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Connection': 'close',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        
        # Make the request
        response = session.post(url, headers=headers, json=payload, timeout=30)
        
        # Return the response data
        return {
            'status_code': response.status_code,
            'text': response.text,
            'headers': dict(response.headers)
        }
        
    except Exception as e:
        return {
            'status_code': 500,
            'text': f"Error in isolated API call: {str(e)}",
            'headers': {}
        }
    finally:
        # Ensure session is closed
        try:
            session.close()
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({
            'status_code': 400,
            'text': 'Usage: python isolated_api_call.py <json_data>',
            'headers': {}
        }))
        sys.exit(1)
    
    try:
        # Parse the input data
        data = json.loads(sys.argv[1])
        url = data['url']
        headers = data['headers']
        payload = data['payload']
        
        # Make the API call
        result = make_api_call(url, headers, payload)
        
        # Return the result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'status_code': 500,
            'text': f"Error parsing input: {str(e)}",
            'headers': {}
        }))
        sys.exit(1)
