import aiohttp
import asyncio
from typing import Dict, List, Optional
import json
import re

class BasePlatformAPI:
    """Base class for all platform APIs"""
    
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
    
    async def ensure_session(self):
        """Ensure session exists"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()


class RGVikramjeetAPI(BasePlatformAPI):
    """RG Vikramjeet / Rankers Gurukul API Client"""
    
    # Try multiple possible API endpoints
    BASE_URLS = [
        "https://api.rankersgurukul.com",
        "https://rankersgurukul.com/api",
        "https://www.rankersgurukul.com/api",
        "https://backend.rankersgurukul.com"
    ]
    
    WEB_URL = "https://rankersgurukul.com"
    
    async def login_with_password(self, phone: str, password: str) -> Optional[str]:
        """Login with phone and password"""
        await self.ensure_session()
        
        # Clean phone
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('91'):
            phone = '91' + phone
        
        # Try different API endpoints and payload formats
        login_attempts = [
            # Attempt 1: Standard format
            {
                "endpoint": "/api/v1/login",
                "payload": {"mobile": phone, "password": password}
            },
            # Attempt 2: Email/username format
            {
                "endpoint": "/api/login",
                "payload": {"username": phone, "password": password}
            },
            # Attempt 3: Phone without country code
            {
                "endpoint": "/api/v1/auth/login",
                "payload": {"phone": phone[-10:], "password": password}
            },
            # Attempt 4: With country code separate
            {
                "endpoint": "/login",
                "payload": {"country_code": "+91", "mobile": phone[-10:], "password": password}
            },
            # Attempt 5: Email format (if user has email)
            {
                "endpoint": "/api/user/login",
                "payload": {"mobile": phone, "password": password, "type": "mobile"}
            }
        ]
        
        last_error = None
        
        # Try each base URL with each login attempt
        for base_url in self.BASE_URLS:
            for attempt in login_attempts:
                try:
                    url = f"{base_url}{attempt['endpoint']}"
                    
                    async with self.session.post(
                        url,
                        json=attempt['payload'],
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            try:
                                data = await resp.json()
                                # Try different token field names
                                token = (
                                    data.get('token') or 
                                    data.get('access_token') or 
                                    data.get('auth_token') or
                                    data.get('jwt') or
                                    data.get('data', {}).get('token')
                                )
                                
                                if token:
                                    self.auth_token = token
                                    print(f"✅ Login successful with {base_url}{attempt['endpoint']}")
                                    return token
                            except:
                                pass
                        
                except Exception as e:
                    last_error = str(e)
                    continue
        
        print(f"❌ All login attempts failed. Last error: {last_error}")
        return None
    
    async def send_otp(self, phone: str) -> bool:
        """Send OTP to phone"""
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('91'):
            phone = '91' + phone
        
        # Try different endpoints
        otp_endpoints = [
            {"url": "/api/v1/send-otp", "payload": {"mobile": phone}},
            {"url": "/api/send-otp", "payload": {"phone": phone}},
            {"url": "/api/v1/auth/send-otp", "payload": {"mobile": phone, "type": "login"}},
        ]
        
        for base_url in self.BASE_URLS:
            for endpoint in otp_endpoints:
                try:
                    url = f"{base_url}{endpoint['url']}"
                    async with self.session.post(
                        url,
                        json=endpoint['payload'],
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('success') or data.get('status') == 'success':
                                print(f"✅ OTP sent via {url}")
                                return True
                except:
                    continue
        
        return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[str]:
        """Verify OTP"""
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('91'):
            phone = '91' + phone
        
        verify_endpoints = [
            {"url": "/api/v1/verify-otp", "payload": {"mobile": phone, "otp": otp}},
            {"url": "/api/verify-otp", "payload": {"phone": phone, "otp": otp}},
            {"url": "/api/v1/auth/verify", "payload": {"mobile": phone, "otp": otp}},
        ]
        
        for base_url in self.BASE_URLS:
            for endpoint in verify_endpoints:
                try:
                    url = f"{base_url}{endpoint['url']}"
                    async with self.session.post(
                        url,
                        json=endpoint['payload'],
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            token = data.get('token') or data.get('access_token')
                            if token:
                                self.auth_token = token
                                return token
                except:
                    continue
        
        return None
    
    async def get_batches(self) -> List[Dict]:
        """Get user batches"""
        await self.ensure_session()
        
        if not self.auth_token:
            return []
        
        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.auth_token}"
        
        batch_endpoints = [
            "/api/v1/my-courses",
            "/api/v1/user/courses",
            "/api/courses/purchased",
            "/api/v1/batches",
            "/api/user/batches",
        ]
        
        for base_url in self.BASE_URLS:
            for endpoint in batch_endpoints:
                try:
                    url = f"{base_url}{endpoint}"
                    async with self.session.get(
                        url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            batches = (
                                data.get('courses') or 
                                data.get('batches') or 
                                data.get('data') or 
                                []
                            )
                            if batches:
                                return batches
                except:
                    continue
        
        return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        """Get batch content"""
        await self.ensure_session()
        
        if not self.auth_token:
            return []
        
        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.auth_token}"
        
        content_endpoints = [
            f"/api/v1/course/{batch_id}/content",
            f"/api/v1/batch/{batch_id}/lectures",
            f"/api/course/{batch_id}/videos",
            f"/api/v1/courses/{batch_id}/lessons",
        ]
        
        for base_url in self.BASE_URLS:
            for endpoint in content_endpoints:
                try:
                    url = f"{base_url}{endpoint}"
                    async with self.session.get(
                        url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = (
                                data.get('content') or 
                                data.get('lectures') or 
                                data.get('lessons') or
                                data.get('videos') or
                                data.get('data') or 
                                []
                            )
                            if content:
                                return content
                except:
                    continue
        
        return []


class PhysicsWallahAPI(BasePlatformAPI):
    """Physics Wallah API"""
    
    BASE_URL = "https://api.pw.live"
    
    async def login_with_password(self, phone: str, password: str) -> Optional[str]:
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        
        try:
            async with self.session.post(
                f"{self.BASE_URL}/v2/user/login",
                json={"mobile": phone, "password": password},
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token')
                    return self.auth_token
        except Exception as e:
            print(f"PW Login Error: {e}")
        
        return None
    
    async def send_otp(self, phone: str) -> bool:
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        
        try:
            async with self.session.post(
                f"{self.BASE_URL}/v2/user/send-otp",
                json={"mobile": phone},
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                return resp.status == 200
        except:
            return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[str]:
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        
        try:
            async with self.session.post(
                f"{self.BASE_URL}/v2/user/verify-otp",
                json={"mobile": phone, "otp": otp},
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token')
                    return self.auth_token
        except:
            return None
    
    async def get_batches(self) -> List[Dict]:
        await self.ensure_session()
        
        if not self.auth_token:
            return []
        
        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.auth_token}"
        
        try:
            async with self.session.get(
                f"{self.BASE_URL}/v2/batches/my-batches",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('data', [])
        except:
            pass
        
        return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        await self.ensure_session()
        
        if not self.auth_token:
            return []
        
        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.auth_token}"
        
        try:
            async with self.session.get(
                f"{self.BASE_URL}/v2/batches/{batch_id}/content",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('data', [])
        except:
            pass
        
        return []


# API Factory
def get_platform_api(app_id: str):
    """Get API client for platform"""
    apis = {
        'rgvikramjeet': RGVikramjeetAPI,
        'pw': PhysicsWallahAPI,
    }
    
    api_class = apis.get(app_id, RGVikramjeetAPI)
    return api_class()
