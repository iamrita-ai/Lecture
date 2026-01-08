import aiohttp
import asyncio
from typing import Dict, List, Optional
import json

class RGVikramjeetAPI:
    """RG Vikramjeet API Client"""
    
    BASE_URL = "https://api.rgvikramjeet.com"  # Replace with actual API base URL
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        }
        self.auth_token = None
    
    async def send_otp(self, phone: str) -> bool:
        """Send OTP to phone number"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "mobile": phone,
                    "country_code": "+91"
                }
                async with session.post(
                    f"{self.BASE_URL}/api/v1/auth/send-otp",
                    json=payload,
                    headers=self.headers
                ) as resp:
                    data = await resp.json()
                    return data.get('success', False)
        except Exception as e:
            print(f"Send OTP Error: {e}")
            return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[Dict]:
        """Verify OTP and get auth token"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "mobile": phone,
                    "otp": otp
                }
                async with session.post(
                    f"{self.BASE_URL}/api/v1/auth/verify-otp",
                    json=payload,
                    headers=self.headers
                ) as resp:
                    data = await resp.json()
                    if data.get('success'):
                        self.auth_token = data.get('token')
                        return data
                    return None
        except Exception as e:
            print(f"Verify OTP Error: {e}")
            return None
    
    async def get_batches(self) -> List[Dict]:
        """Get user's purchased batches"""
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/api/v1/user/batches",
                    headers=headers
                ) as resp:
                    data = await resp.json()
                    return data.get('batches', [])
        except Exception as e:
            print(f"Get Batches Error: {e}")
            return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        """Get all videos and PDFs from a batch"""
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/api/v1/batch/{batch_id}/content",
                    headers=headers
                ) as resp:
                    data = await resp.json()
                    return data.get('content', [])
        except Exception as e:
            print(f"Get Batch Content Error: {e}")
            return []


class UnacademyAPI:
    """Unacademy API Client"""
    
    BASE_URL = "https://unacademy.com/api/v3"
    
    def __init__(self):
        self.auth_token = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json'
        }
    
    async def send_otp(self, phone: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"phone": phone}
                async with session.post(
                    f"{self.BASE_URL}/user/login/send_otp",
                    json=payload,
                    headers=self.headers
                ) as resp:
                    data = await resp.json()
                    return data.get('success', False)
        except:
            return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"phone": phone, "otp": otp}
                async with session.post(
                    f"{self.BASE_URL}/user/login/verify",
                    json=payload,
                    headers=self.headers
                ) as resp:
                    data = await resp.json()
                    if data.get('token'):
                        self.auth_token = data['token']
                        return data
                    return None
        except:
            return None
    
    async def get_batches(self) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/user/purchases",
                    headers=headers
                ) as resp:
                    data = await resp.json()
                    return data.get('courses', [])
        except:
            return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/course/{batch_id}/lessons",
                    headers=headers
                ) as resp:
                    data = await resp.json()
                    return data.get('lessons', [])
        except:
            return []


class PhysicsWallahAPI:
    """Physics Wallah API Client"""
    
    BASE_URL = "https://api.pw.live"
    
    def __init__(self):
        self.auth_token = None
        self.headers = {
            'User-Agent': 'PWApp/1.0',
            'Content-Type': 'application/json'
        }
    
    async def send_otp(self, phone: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"mobile": phone}
                async with session.post(
                    f"{self.BASE_URL}/v2/user/send-otp",
                    json=payload,
                    headers=self.headers
                ) as resp:
                    data = await resp.json()
                    return data.get('success', False)
        except:
            return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"mobile": phone, "otp": otp}
                async with session.post(
                    f"{self.BASE_URL}/v2/user/verify-otp",
                    json=payload,
                    headers=self.headers
                ) as resp:
                    data = await resp.json()
                    if data.get('token'):
                        self.auth_token = data['token']
                        return data
                    return None
        except:
            return None
    
    async def get_batches(self) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/v2/batches/my-batches",
                    headers=headers
                ) as resp:
                    data = await resp.json()
                    return data.get('data', [])
        except:
            return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        try:
            if not self.auth_token:
                return []
            
            headers = self.headers.copy()
            headers['Authorization'] = f"Bearer {self.auth_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/v2/batches/{batch_id}/content",
                    headers=headers
                ) as resp:
                    data = await resp.json()
                    return data.get('data', [])
        except:
            return []


# API Client Factory
def get_api_client(app_id: str):
    """Get appropriate API client based on app"""
    clients = {
        'rgvikramjeet': RGVikramjeetAPI,
        'unacademy': UnacademyAPI,
        'pw': PhysicsWallahAPI,
        # Add more as needed
    }
    
    client_class = clients.get(app_id)
    if client_class:
        return client_class()
    return None
