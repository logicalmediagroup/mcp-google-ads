#!/usr/bin/env python3
"""
Subprocess-based Google Ads API client to ensure complete process isolation.

This module implements a subprocess-based approach to Google Ads API calls
to prevent any state accumulation that could cause nesting counter errors.
"""

import subprocess
import json
import tempfile
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger('subprocess_api_client')

class SubprocessGoogleAdsAPIClient:
    """
    Google Ads API client that uses subprocess calls for complete isolation.
    
    This ensures that each API call runs in a completely separate process,
    preventing any state accumulation that could cause nesting counter errors.
    """
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.isolated_script = self.script_dir / "isolated_api_call.py"
        self._create_isolated_script()
    
    def _create_isolated_script(self):
        """Create the isolated API call script."""
        script_content = '''#!/usr/bin/env python3
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
'''
        
        with open(self.isolated_script, 'w') as f:
            f.write(script_content)
        
        # Make the script executable
        os.chmod(self.isolated_script, 0o755)
    
    def make_request(self, url: str, headers: dict, payload: dict):
        """
        Make a Google Ads API request using subprocess isolation.
        
        Args:
            url: The API endpoint URL
            headers: Request headers including authorization
            payload: Request payload
            
        Returns:
            Response object from the API
        """
        try:
            # Prepare the data for the subprocess
            data = {
                'url': url,
                'headers': headers,
                'payload': payload
            }
            
            # Run the isolated API call
            result = subprocess.run(
                [sys.executable, str(self.isolated_script), json.dumps(data)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.script_dir)
            )
            
            if result.returncode != 0:
                logger.error(f"Subprocess failed with return code {result.returncode}")
                logger.error(f"Stderr: {result.stderr}")
                return None
            
            # Parse the result
            response_data = json.loads(result.stdout)
            
            # Create a mock response object
            class MockResponse:
                def __init__(self, data):
                    self.status_code = data['status_code']
                    self.text = data['text']
                    self.headers = data['headers']
                
                def json(self):
                    try:
                        return json.loads(self.text)
                    except:
                        return {}
            
            return MockResponse(response_data)
            
        except subprocess.TimeoutExpired:
            logger.error("Subprocess timed out")
            return None
        except Exception as e:
            logger.error(f"Error in subprocess API call: {str(e)}")
            return None
