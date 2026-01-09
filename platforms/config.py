"""
Platform API Configuration
Update API endpoints here as you discover them
"""

PLATFORM_CONFIGS = {
    "rgvikramjeet": {
        "name": "RG Vikramjeet",
        # Updated base URLs - try multiple
        "base_urls": [
            "https://rgvikramjeetapi.akamai.net.in",
            "https://www.masterapi.tech",
            "https://api.rankersgurukul.com",
            "https://rankersgurukul.com/api"
        ],
        "base_url": "https://rgvikramjeetapi.akamai.net.in",  # Primary
        "api_endpoints": {
            "login": "/api/v1/user/login",
            "send_otp": "/api/v1/user/send-otp",
            "verify_otp": "/api/v1/user/verify-otp",
            "get_batches": "/api/v1/user/courses",
            "get_batch_content": "/api/v1/course/{batch_id}/lectures"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://rankersgurukul.com",
            "Referer": "https://rankersgurukul.com/"
        },
        "login_payload_format": {
            "mobile": "{phone}",
            "password": "{password}"
        },
        "response_token_key": "token",
        "response_data_key": "data",
        # Known working domains for content
        "content_domains": [
            "https://www.masterapi.tech/get/appx/signedUrl",
            "https://www.masterapi.tech/get/appx-pdf/signedUrl",
            "https://rgvikramjeetapi.akamai.net.in"
        ]
    },
    
    "pw": {
        "name": "Physics Wallah",
        "base_url": "https://api.pw.live",
        "api_endpoints": {
            "login": "/v2/user/login",
            "send_otp": "/v2/user/send-otp",
            "verify_otp": "/v2/user/verify-otp",
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
    },
}


def get_platform_config(platform_id: str):
    """Get configuration for a specific platform"""
    return PLATFORM_CONFIGS.get(platform_id, PLATFORM_CONFIGS.get("rgvikramjeet"))
