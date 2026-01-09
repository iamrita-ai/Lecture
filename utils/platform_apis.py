import aiohttp
import asyncio
from typing import Dict, List, Optional
import json
import re
from platforms.config import get_platform_config

class UniversalPlatformAPI:
    """Universal API client that works with any platform using config"""
    
    def __init__(self, platform_id: str):
        self.platform_id = platform_id
        self.config = get_platform_config(platform_id)
        self.session = None
        self.auth_token = None
        
        self.base_url = self.config.get('base_url')
        self.endpoints = self.config.get('api_endpoints', {})
        self.headers = self.config.get('headers', {})
        self.payload_format = self.config.get('login_payload_format', {})
        self.token_key = self.config.get('response_token_key', 'token')
        self.data_key = self.config.get('response_data_key', 'data')
    
    async def ensure_session(self):
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def format_payload(self, template: dict, **kwargs) -> dict:
        formatted = {}
        for key, value in template.items():
            if isinstance(value, str):
                formatted[key] = value.format(**kwargs)
            else:
                formatted[key] = value
        return formatted
    
    async def login_with_password(self, phone: str, password: str) -> Optional[str]:
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        
        login_endpoint = self.endpoints.get('login')
        if not login_endpoint:
            print(f"No login endpoint for {self.platform_id}")
            return None
        
        payload = self.format_payload(self.payload_format, phone=phone, password=password)
        
        base_urls = self.config.get('base_urls', [self.base_url])
        
        for base_url in base_urls:
            url = f"{base_url}{login_endpoint}"
            
            try:
                print(f"Trying: {url}")
                
                async with self.session.post(url, json=payload, headers=self.headers) as resp:
                    print(f"Status: {resp.status}")
                    
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            print(f"Response: {json.dumps(data, indent=2)[:500]}")
                            
                            token = None
                            
                            if self.token_key in data:
                                token = data[self.token_key]
                            elif self.data_key in data and isinstance(data[self.data_key], dict):
                                token = data[self.data_key].get(self.token_key)
                            else:
                                for key in ['token', 'access_token', 'auth_token', 'jwt']:
                                    if key in data:
                                        token = data[key]
                                        break
                            
                            if token:
                                self.auth_token = token
                                self.base_url = base_url
                                print(f"Login successful!")
                                return token
                        except Exception as e:
                            print(f"JSON Error: {e}")
                            
            except Exception as e:
                print(f"Error for {base_url}: {e}")
                continue
        
        print("All login attempts failed")
        return None
    
    async def send_otp(self, phone: str) -> bool:
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        
        endpoint = self.endpoints.get('send_otp')
        if not endpoint:
            return False
        
        url = f"{self.base_url}{endpoint}"
        payload = {"mobile": phone, "phone": phone}
        
        try:
            async with self.session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('success', False) or data.get('status') == 'success'
        except:
            pass
        
        return False
    
    async def verify_otp(self, phone: str, otp: str) -> Optional[str]:
        await self.ensure_session()
        
        phone = re.sub(r'\D', '', phone)
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        
        endpoint = self.endpoints.get('verify_otp')
        if not endpoint:
            return None
        
        url = f"{self.base_url}{endpoint}"
        payload = {"mobile": phone, "phone": phone, "otp": otp}
        
        try:
            async with self.session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = data.get(self.token_key) or data.get('token')
                    if token:
                        self.auth_token = token
                        return token
        except:
            pass
        
        return None
    
    async def get_batches(self) -> List[Dict]:
        await self.ensure_session()
        
        if not self.auth_token:
            print("No auth token")
            return []
        
        endpoint = self.endpoints.get('get_batches')
        if not endpoint:
            print("No get_batches endpoint")
            return []
        
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.auth_token}"
        
        try:
            print(f"Fetching batches from {url}")
            
            async with self.session.get(url, headers=headers) as resp:
                print(f"Status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Batches: {json.dumps(data, indent=2)[:500]}")
                    
                    batches = None
                    
                    if self.data_key in data:
                        batches = data[self.data_key]
                    else:
                        for key in ['courses', 'batches', 'data', 'subscriptions']:
                            if key in data:
                                batches = data[key]
                                break
                    
                    if not batches and isinstance(data, list):
                        batches = data
                    
                    if batches and isinstance(batches, list):
                        print(f"Found {len(batches)} batches")
                        return batches
                    else:
                        print("No batches in response")
                else:
                    text = await resp.text()
                    print(f"Failed: {text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")
        
        return []
    
    async def get_batch_content(self, batch_id: str) -> List[Dict]:
        await self.ensure_session()
        
        if not self.auth_token:
            print("No auth token")
            return []
        
        endpoint = self.endpoints.get('get_batch_content')
        if not endpoint:
            print("No content endpoint")
            return []
        
        endpoint = endpoint.replace('{batch_id}', str(batch_id))
        
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        headers['Authorization'] = f"Bearer {self.auth_token}"
        
        try:
            print(f"Fetching content from {url}")
            
            async with self.session.get(url, headers=headers) as resp:
                print(f"Status: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Content: {json.dumps(data, indent=2)[:800]}")
                    
                    content = None
                    
                    if self.data_key in data:
                        content = data[self.data_key]
                    else:
                        for key in ['content', 'lectures', 'lessons', 'videos', 'data']:
                            if key in data:
                                content = data[key]
                                break
                    
                    if not content and isinstance(data, list):
                        content = data
                    
                    if content and isinstance(content, list):
                        print(f"Found {len(content)} items")
                        return content
                    else:
                        print("No content found")
                else:
                    text = await resp.text()
                    print(f"Failed: {text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")
        
        return []


def get_platform_api(platform_id: str):
    return UniversalPlatformAPI(platform_id)
