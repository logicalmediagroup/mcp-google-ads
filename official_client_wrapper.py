#!/usr/bin/env python3
"""
Official Google Ads API client wrapper to completely avoid nesting counter issues.

This module uses the official Google Ads API Python client library which handles
session management internally and should not have nesting counter issues.
"""

import os
import logging
import json
from typing import Dict, Any, List
import sys
from pathlib import Path

logger = logging.getLogger('official_client_wrapper')

class OfficialGoogleAdsAPIClient:
    """
    Wrapper around the official Google Ads API Python client library.
    
    This should completely avoid nesting counter issues since it uses
    the official client's internal session management.
    """
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the official Google Ads API client."""
        try:
            # Try to import the official Google Ads API client
            from google.ads.googleads.client import GoogleAdsClient
            
            # Get configuration from environment variables
            developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
            login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace('-', '')
            
            # Determine authentication method
            auth_type = os.environ.get("GOOGLE_ADS_AUTH_TYPE", "oauth").lower()
            
            if auth_type == "service_account":
                # Service account configuration
                credentials_path = os.environ.get("GOOGLE_ADS_CREDENTIALS_PATH")
                if not credentials_path or not os.path.exists(credentials_path):
                    raise ValueError(f"Service account file not found: {credentials_path}")
                
                # Create configuration for service account
                config = {
                    "developer_token": developer_token,
                    "json_key_file_path": credentials_path,
                    "login_customer_id": login_customer_id,
                    "use_proto_plus": True
                }
            else:
                # OAuth configuration - for now, fall back to service account
                # since OAuth requires additional setup
                logger.info("OAuth not fully configured, falling back to service account")
                credentials_path = os.environ.get("GOOGLE_ADS_CREDENTIALS_PATH")
                if not credentials_path or not os.path.exists(credentials_path):
                    raise ValueError(f"Service account file not found: {credentials_path}")
                
                config = {
                    "developer_token": developer_token,
                    "json_key_file_path": credentials_path,
                    "login_customer_id": login_customer_id,
                    "use_proto_plus": True
                }
            
            # Initialize the client
            self.client = GoogleAdsClient.load_from_dict(config)
            logger.info("Successfully initialized official Google Ads API client")
            
        except ImportError:
            logger.error("Official Google Ads API client library not installed")
            logger.error("Install with: pip install google-ads")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize official Google Ads API client: {str(e)}")
            self.client = None
    
    def make_request(self, url: str, headers: dict, payload: dict):
        """
        Make a Google Ads API request using the official client.
        
        This method translates the raw HTTP request to use the official client's
        search method, which should avoid nesting counter issues.
        """
        if not self.client:
            return self._create_error_response("Official client not available")
        
        try:
            # Extract customer ID from URL
            # URL format: https://googleads.googleapis.com/v19/customers/{customer_id}/googleAds:search
            url_parts = url.split('/')
            customer_id = None
            for i, part in enumerate(url_parts):
                if part == 'customers' and i + 1 < len(url_parts):
                    customer_id = url_parts[i + 1]
                    break
            
            if not customer_id:
                return self._create_error_response("Could not extract customer ID from URL")
            
            # Extract query from payload
            query = payload.get('query', '')
            if not query:
                return self._create_error_response("No query found in payload")
            
            # Get the Google Ads service
            ga_service = self.client.get_service("GoogleAdsService")
            
            # Execute the search request
            search_request = self.client.get_type("SearchGoogleAdsRequest")
            search_request.customer_id = customer_id
            search_request.query = query
            
            # Perform the search
            results = ga_service.search(request=search_request)
            
            # Convert results to the expected format
            formatted_results = []
            for row in results:
                # Convert protobuf message to dict
                row_dict = {}
                
                # Handle different types of results
                if hasattr(row, 'campaign') and row.campaign:
                    row_dict['campaign'] = self._protobuf_to_dict(row.campaign)
                if hasattr(row, 'ad_group') and row.ad_group:
                    row_dict['adGroup'] = self._protobuf_to_dict(row.ad_group)
                if hasattr(row, 'ad_group_ad') and row.ad_group_ad:
                    row_dict['adGroupAd'] = self._protobuf_to_dict(row.ad_group_ad)
                if hasattr(row, 'customer') and row.customer:
                    row_dict['customer'] = self._protobuf_to_dict(row.customer)
                if hasattr(row, 'customer_client') and row.customer_client:
                    row_dict['customerClient'] = self._protobuf_to_dict(row.customer_client)
                if hasattr(row, 'metrics') and row.metrics:
                    row_dict['metrics'] = self._protobuf_to_dict(row.metrics)
                if hasattr(row, 'segments') and row.segments:
                    row_dict['segments'] = self._protobuf_to_dict(row.segments)
                if hasattr(row, 'asset') and row.asset:
                    row_dict['asset'] = self._protobuf_to_dict(row.asset)
                
                if row_dict:  # Only add non-empty results
                    formatted_results.append(row_dict)
            
            # Create response in expected format
            response_data = {
                'results': formatted_results
            }
            
            return self._create_success_response(json.dumps(response_data))
            
        except Exception as e:
            logger.error(f"Error executing query with official client: {str(e)}")
            return self._create_error_response(f"Official client error: {str(e)}")
    
    def _protobuf_to_dict(self, protobuf_obj):
        """Convert protobuf object to dictionary."""
        try:
            # Use the official conversion method if available
            if hasattr(protobuf_obj, '_pb'):
                from google.protobuf.json_format import MessageToDict
                return MessageToDict(protobuf_obj._pb)
            else:
                # Fallback: manual conversion
                result = {}
                for field in protobuf_obj.DESCRIPTOR.fields:
                    value = getattr(protobuf_obj, field.name)
                    if value is not None:
                        if hasattr(value, '_pb'):
                            result[field.name] = self._protobuf_to_dict(value)
                        elif isinstance(value, list):
                            result[field.name] = [
                                self._protobuf_to_dict(item) if hasattr(item, '_pb') else str(item)
                                for item in value
                            ]
                        else:
                            result[field.name] = str(value)
                return result
        except Exception as e:
            logger.warning(f"Error converting protobuf to dict: {str(e)}")
            return {"error": f"Conversion error: {str(e)}"}
    
    def _create_success_response(self, response_text):
        """Create a mock response object for successful requests."""
        class MockResponse:
            def __init__(self, text):
                self.status_code = 200
                self.text = text
                self.headers = {'content-type': 'application/json'}
            
            def json(self):
                return json.loads(self.text)
        
        return MockResponse(response_text)
    
    def _create_error_response(self, error_message):
        """Create a mock response object for error cases."""
        class MockResponse:
            def __init__(self, text):
                self.status_code = 500
                self.text = text
                self.headers = {'content-type': 'application/json'}
            
            def json(self):
                return {"error": {"message": self.text}}
        
        return MockResponse(error_message)


# Factory function to create the appropriate client
def create_official_google_ads_client():
    """Create an official Google Ads API client instance."""
    return OfficialGoogleAdsAPIClient()
