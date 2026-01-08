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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    async def create_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        if self.session:
            await self.session.close()


class RGVikramjeetAPI(BasePlatformAPI):
    """RG Vikramjeet / Rankers Gurukul API"""
    
    BASE_URL = "https://api.rankersgurukul.com"  # API endpoint
    WEB_URL = "https://rankersgurukul.com"
    
    async def send_otp(self, phone: str) -> bool:
        """Send OTP to user's phone"""
        try:
            await self.create_session()
            
            # Clean phone number
            phone = re.sub(r'\D', '', phone)
            if not phone.startswith('91'):
                phone = '91' + phone
            
            payload = {
                "mobile": phone,
                "type": "login"
            }
            
            async with self.session.post(
                f"{self.BASE_URL}/api/v1/send-otp",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('success', False) or data.get('status') == 'success'
                return False
                
        except Exception as e:
            print(f"RG Vikramjeet Send OTP Error: {e}")
            return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[str]:
        """Verify OTP and get auth token"""
        try:
            phone = re.sub(r'\D', '', phone)
            if not phone.startswith('91'):
                phone = '91' + phone
            
            payload = {
                "mobile": phone,
                "otp": otp
            }
            
            async with self.session.post(
                f"{self.BASE_URL}/api/v1/verify-otp",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token') or data.get('access_token')
                    return self.auth_token
                return None
                
        except Exception as e:
            print(f"RG Vikramjeet Verify OTP Error: {e}")
            return None
    
    async def login_with_password(self, phone: str, password: str) -> Optional[str]:
        """Login with phone and password"""
        try:
            phone = re.sub(r'\D', '', phone)
            if not phone.startswith('91'):
                phone = '91' + phone
            
            payload = {
                "mobile": phone,
                "password": password
            }
            
            async with self.session.post(
                f"{self.BASE_URL}/api/v1/login",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token') or data.get('access_token')
                    return self.auth_token
                return None
                
        except Exception as e:
            print(f"RG Vikramjeet Password Login Error: {e}")
            return None
    
    async def get_batches(self) -> List[Dict]:
        """Get user's purchased batches"""
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with self.session.get(
                f"{self.BASE_URL}/api/v1/my-courses",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('courses', []) or data.get('batches', []) or data.get('data', [])
                return []
                
        except Exception as e:
            print(f"RG Vikramjeet Get Batches Error: {e}")
            return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        """Get batch videos and PDFs"""
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with self.session.get(
                f"{self.BASE_URL}/api/v1/course/{batch_id}/content",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('content', []) or data.get('lectures', []) or data.get('data', [])
                return []
                
        except Exception as e:
            print(f"RG Vikramjeet Get Content Error: {e}")
            return []


class PhysicsWallahAPI(BasePlatformAPI):
    """Physics Wallah (PW) API"""
    
    BASE_URL = "https://api.pw.live"
    
    async def send_otp(self, phone: str) -> bool:
        try:
            await self.create_session()
            
            phone = re.sub(r'\D', '', phone)
            
            payload = {"mobile": phone}
            
            async with self.session.post(
                f"{self.BASE_URL}/v2/user/send-otp",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('success', False)
                return False
        except Exception as e:
            print(f"PW Send OTP Error: {e}")
            return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[str]:
        try:
            phone = re.sub(r'\D', '', phone)
            
            payload = {"mobile": phone, "otp": otp}
            
            async with self.session.post(
                f"{self.BASE_URL}/v2/user/verify-otp",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token')
                    return self.auth_token
                return None
        except Exception as e:
            print(f"PW Verify OTP Error: {e}")
            return None
    
    async def login_with_password(self, phone: str, password: str) -> Optional[str]:
        try:
            phone = re.sub(r'\D', '', phone)
            
            payload = {"mobile": phone, "password": password}
            
            async with self.session.post(
                f"{self.BASE_URL}/v2/user/login",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token')
                    return self.auth_token
                return None
        except:
            return None
    
    async def get_batches(self) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with self.session.get(
                f"{self.BASE_URL}/v2/batches/my-batches",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('data', [])
                return []
        except:
            return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with self.session.get(
                f"{self.BASE_URL}/v2/batches/{batch_id}/content",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('data', [])
                return []
        except:
            return []


class UnacademyAPI(BasePlatformAPI):
    """Unacademy API"""
    
    BASE_URL = "https://unacademy.com/api/v3"
    
    async def send_otp(self, phone: str) -> bool:
        try:
            await self.create_session()
            phone = re.sub(r'\D', '', phone)
            
            payload = {"phone": phone}
            
            async with self.session.post(
                f"{self.BASE_URL}/user/login/initiate",
                json=payload,
                headers=self.headers
            ) as resp:
                return resp.status == 200
        except:
            return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[str]:
        try:
            phone = re.sub(r'\D', '', phone)
            
            payload = {"phone": phone, "otp": otp}
            
            async with self.session.post(
                f"{self.BASE_URL}/user/login/verify",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token')
                    return self.auth_token
                return None
        except:
            return None
    
    async def login_with_password(self, phone: str, password: str) -> Optional[str]:
        try:
            phone = re.sub(r'\D', '', phone)
            
            payload = {"phone": phone, "password": password}
            
            async with self.session.post(
                f"{self.BASE_URL}/user/login",
                json=payload,
                headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.auth_token = data.get('token')
                    return self.auth_token
                return None
        except:
            return None
    
    async def get_batches(self) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with self.session.get(
                f"{self.BASE_URL}/user/purchases",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('subscriptions', [])
                return []
        except:
            return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with self.session.get(
                f"{self.BASE_URL}/course/{batch_id}/lessons",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('lessons', [])
                return []
        except:
            return []


# API Factory
def get_platform_api(app_id: str):
    """Get API client for platform"""
    apis = {
        'rgvikramjeet': RGVikramjeetAPI,
        'pw': PhysicsWallahAPI,
        'unacademy': UnacademyAPI,
        # Add more platforms here
    }
    
    api_class = apis.get(app_id, RGVikramjeetAPI)  # Default to RG Vikramjeet
    return api_class()
