"""
Platform API Configuration
"""

PLATFORM_CONFIGS = {
    "rgvikramjeet": {
        "name": "RG Vikramjeet",
        "base_urls": [
            "https://rgvikramjeetapi.akamai.net.in",
            "https://www.masterapi.tech",
            "https://api.rankersgurukul.com"
        ],
        "base_url": "https://rgvikramjeetapi.akamai.net.in",
        "api_endpoints": {
            "login": "/api/v1/user/login",
            "send_otp": "/api/v1/user/send-otp",
            "verify_otp": "/api/v1/user/verify-otp",
            "get_batches": "/api/v1/user/courses",
            "get_batch_content": "/api/v1/course/{batch_id}/lectures"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        "login_payload_format": {
            "mobile": "{phone}",
            "password": "{password}"
        },
        "response_token_key": "token",
        "response_data_key": "data"
    },
    
    "pw": {
        "name": "Physics Wallah",
        "base_url": "https://api.pw.live",
        "api_endpoints": {
            "login": "/v2/user/login",
            "get_batches": "/v2/batches/my-batches",
            "get_batch_content": "/v2/batches/{batch_id}/content"
        },
        "headers": {
            "User-Agent": "PWApp/1.0",
            "Content-Type": "application/json"
        },
        "login_payload_format": {
            "mobile": "{phone}",
            "password": "{password}"
        },
        "response_token_key": "token",
        "response_data_key": "data"
    }
}


def get_platform_config(platform_id: str):
    return PLATFORM_CONFIGS.get(platform_id, PLATFORM_CONFIGS.get("rgvikramjeet"))
