"""
Platform API Configuration
Easily update API endpoints for each platform here
"""

PLATFORM_CONFIGS = {
    "rgvikramjeet": {
        "name": "RG Vikramjeet",
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
            "Accept": "application/json",
            "Origin": "https://rankersgurukul.com",
            "Referer": "https://rankersgurukul.com/"
        },
        "login_payload_format": {
            "mobile": "{phone}",
            "password": "{password}"
        },
        "response_token_key": "token",  # Where to find token in response
        "response_data_key": "data",    # Where to find data in response
        "domain_patterns": [
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
            "User-Agent": "PWApp/1.0 Android",
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
    
    "unacademy": {
        "name": "Unacademy",
        "base_url": "https://unacademy.com/api/v3",
        "api_endpoints": {
            "login": "/user/login",
            "send_otp": "/user/login/initiate",
            "verify_otp": "/user/login/verify",
            "get_batches": "/user/purchases",
            "get_batch_content": "/course/{batch_id}/lessons"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        },
        "login_payload_format": {
            "phone": "{phone}",
            "password": "{password}"
        },
        "response_token_key": "token",
        "response_data_key": "subscriptions"
    },
    
    "carrierwill": {
        "name": "Carrier Will",
        "base_url": "https://api.carrierwill.in",
        "api_endpoints": {
            "login": "/api/login",
            "get_batches": "/api/my-courses",
            "get_batch_content": "/api/course/{batch_id}/content"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        },
        "login_payload_format": {
            "mobile": "{phone}",
            "password": "{password}"
        },
        "response_token_key": "access_token",
        "response_data_key": "data"
    },
    
    "studyiq": {
        "name": "Study IQ",
        "base_url": "https://www.studyiq.com/api",
        "api_endpoints": {
            "login": "/v1/login",
            "get_batches": "/v1/courses/purchased",
            "get_batch_content": "/v1/course/{batch_id}/videos"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json"
        },
        "login_payload_format": {
            "phone": "{phone}",
            "password": "{password}"
        },
        "response_token_key": "token",
        "response_data_key": "data"
    },
    
    # Add more platforms here - Easy to configure!
    # Template:
    # "platform_id": {
    #     "name": "Platform Name",
    #     "base_url": "https://api.platform.com",
    #     "api_endpoints": {
    #         "login": "/endpoint",
    #         "get_batches": "/endpoint",
    #         "get_batch_content": "/endpoint"
    #     },
    #     "headers": {},
    #     "login_payload_format": {},
    #     "response_token_key": "token",
    #     "response_data_key": "data"
    # }
}


def get_platform_config(platform_id: str):
    """Get configuration for a specific platform"""
    return PLATFORM_CONFIGS.get(platform_id, PLATFORM_CONFIGS.get("rgvikramjeet"))


def update_platform_config(platform_id: str, config: dict):
    """Update platform configuration - For future admin panel"""
    PLATFORM_CONFIGS[platform_id] = config
