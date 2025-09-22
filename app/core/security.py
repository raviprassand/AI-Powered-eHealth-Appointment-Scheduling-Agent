# This file can be expanded for API security, JWT tokens, etc.
# Currently empty as the basic implementation doesn't require auth

def get_api_key_header(api_key: str) -> dict:
    """Generate API key header for external services"""
    return {"x-api-key": api_key}