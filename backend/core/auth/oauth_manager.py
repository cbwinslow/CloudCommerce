import asyncio
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import hashlib
import jwt
from letta import LettaClient
from litellm import completion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Platform(Enum):
    EBAY = "ebay"
    AMAZON = "amazon"
    MERCARI = "mercari"
    FACEBOOK_MARKETPLACE = "facebook_marketplace"

@dataclass
class OAuthToken:
    platform: Platform
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    scope: str = ""
    user_id: str = ""
    platform_user_id: str = ""
    platform_username: str = ""

@dataclass
class OAuthConfig:
    platform: Platform
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_url: str
    token_url: str
    scope: str
    is_enabled: bool = True

@dataclass
class ConnectedAccount:
    id: str
    user_id: str
    platform: Platform
    username: str
    platform_user_id: str
    is_active: bool = True
    last_sync: Optional[datetime] = None
    metadata: Dict[str, Any] = None

class OAuthManager:
    def __init__(self, supabase_client, letta_client: LettaClient):
        self.supabase = supabase_client
        self.letta = letta_client
        self.oauth_configs: Dict[Platform, OAuthConfig] = {}
        self.tokens: Dict[str, OAuthToken] = {}  # key: (user_id, platform)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize OAuth configurations
        self._initialize_oauth_configs()
        
    def _initialize_oauth_configs(self):
        """Initialize OAuth configurations for each platform"""
        # These would be loaded from environment variables or database
        self.oauth_configs = {
            Platform.EBAY: OAuthConfig(
                platform=Platform.EBAY,
                client_id=os.getenv("EBAY_CLIENT_ID", ""),
                client_secret=os.getenv("EBAY_CLIENT_SECRET", ""),
                redirect_uri=os.getenv("EBAY_REDIRECT_URI", ""),
                auth_url="https://auth.ebay.com/oauth2/authorize",
                token_url="https://api.ebay.com/identity/v1/oauth2/token",
                scope="https://api.ebay.com/oauth/api_scope"
            ),
            Platform.AMAZON: OAuthConfig(
                platform=Platform.AMAZON,
                client_id=os.getenv("AMAZON_CLIENT_ID", ""),
                client_secret=os.getenv("AMAZON_CLIENT_SECRET", ""),
                redirect_uri=os.getenv("AMAZON_REDIRECT_URI", ""),
                auth_url="https://www.amazon.com/ap/oa",
                token_url="https://api.amazon.com/auth/o2/token",
                scope="profile:read_orders payments:read"
            ),
            Platform.MERCARI: OAuthConfig(
                platform=Platform.MERCARI,
                client_id=os.getenv("MERCARI_CLIENT_ID", ""),
                client_secret=os.getenv("MERCARI_CLIENT_SECRET", ""),
                redirect_uri=os.getenv("MERCARI_REDIRECT_URI", ""),
                auth_url="https://auth.mercari.com/oauth2/authorize",
                token_url="https://api.mercari.com/v1/oauth2/token",
                scope="read write"
            ),
            Platform.FACEBOOK_MARKETPLACE: OAuthConfig(
                platform=Platform.FACEBOOK_MARKETPLACE,
                client_id=os.getenv("FACEBOOK_CLIENT_ID", ""),
                client_secret=os.getenv("FACEBOOK_CLIENT_SECRET", ""),
                redirect_uri=os.getenv("FACEBOOK_REDIRECT_URI", ""),
                auth_url="https://www.facebook.com/v18.0/dialog/oauth",
                token_url="https://graph.facebook.com/v18.0/oauth/access_token",
                scope="read_insights read_page_mailboxes"
            )
        }
    
    async def get_authorization_url(self, platform: Platform, user_id: str, state: str = None) -> str:
        """Generate OAuth authorization URL for a platform"""
        config = self.oauth_configs.get(platform)
        if not config or not config.is_enabled:
            raise ValueError(f"OAuth not enabled for {platform.value}")
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Store state for verification
        await self._store_oauth_state(user_id, platform, state)
        
        # Generate authorization URL
        auth_params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": config.scope,
            "state": state,
            "prompt": "consent"
        }
        
        # Platform-specific URL construction
        if platform == Platform.EBAY:
            auth_params["redirect_uri"] = f"{config.redirect_uri}?state={state}"
        elif platform == Platform.AMAZON:
            auth_params["redirect_uri"] = f"{config.redirect_uri}?state={state}"
        elif platform == Platform.MERCARI:
            auth_params["redirect_uri"] = f"{config.redirect_uri}?state={state}"
        elif platform == Platform.FACEBOOK_MARKETPLACE:
            auth_params["redirect_uri"] = f"{config.redirect_uri}?state={state}"
        
        # Build URL
        from urllib.parse import urlencode
        auth_url = f"{config.auth_url}?{urlencode(auth_params)}"
        
        return auth_url
    
    async def handle_oauth_callback(self, platform: Platform, user_id: str, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens"""
        try:
            # Verify state
            stored_state = await self._get_oauth_state(user_id, platform)
            if not stored_state or stored_state != state:
                raise ValueError("Invalid or expired state parameter")
            
            # Exchange code for tokens
            token_data = await self._exchange_code_for_tokens(platform, code)
            
            # Store tokens
            token = OAuthToken(
                platform=platform,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", ""),
                expires_at=datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600)),
                token_type=token_data.get("token_type", "Bearer"),
                scope=token_data.get("scope", ""),
                user_id=user_id
            )
            
            await self._store_token(user_id, platform, token)
            
            # Get user info from platform
            user_info = await self._get_platform_user_info(platform, token)
            
            # Store connected account
            connected_account = ConnectedAccount(
                id=hashlib.md5(f"{user_id}_{platform.value}_{user_info['id']}").hexdigest(),
                user_id=user_id,
                platform=platform,
                username=user_info.get("username", user_info.get("name", "")),
                platform_user_id=user_info["id"],
                metadata=user_info
            )
            
            await self._store_connected_account(connected_account)
            
            return {
                "success": True,
                "message": f"Successfully connected to {platform.value}",
                "account_id": connected_account.id,
                "username": connected_account.username
            }
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback for {platform.value}: {e}")
            return {
                "success": False,
                "message": f"Failed to connect to {platform.value}: {str(e)}"
            }
    
    async def _exchange_code_for_tokens(self, platform: Platform, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        config = self.oauth_configs.get(platform)
        if not config:
            raise ValueError(f"No OAuth config found for {platform.value}")
        
        try:
            # Prepare token request
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.redirect_uri,
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
            
            # Platform-specific token request
            if platform == Platform.AMAZON:
                token_data["grant_type"] = "authorization_code"
            elif platform == Platform.FACEBOOK_MARKETPLACE:
                token_data["client_id"] = config.client_id
                token_data["client_secret"] = config.client_secret
            
            # Make token request
            async with aiohttp.ClientSession() as session:
                async with session.post(config.token_url, data=token_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Token exchange failed: {error_text}")
                    
                    token_response = await response.json()
                    return token_response
                    
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            raise
    
    async def _get_platform_user_info(self, platform: Platform, token: OAuthToken) -> Dict[str, Any]:
        """Get user information from the platform"""
        try:
            if platform == Platform.EBAY:
                return await self._get_ebay_user_info(token)
            elif platform == Platform.AMAZON:
                return await self._get_amazon_user_info(token)
            elif platform == Platform.MERCARI:
                return await self._get_mercari_user_info(token)
            elif platform == Platform.FACEBOOK_MARKETPLACE:
                return await self._get_facebook_user_info(token)
            else:
                raise ValueError(f"Unsupported platform: {platform.value}")
                
        except Exception as e:
            logger.error(f"Error getting user info from {platform.value}: {e}")
            raise
    
    async def _get_ebay_user_info(self, token: OAuthToken) -> Dict[str, Any]:
        """Get eBay user information"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}",
                    "Content-Type": "application/json"
                }
                
                async with session.get("https://api.ebay.com/identity/v1/user", headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get eBay user info: {response.status}")
                    
                    user_data = await response.json()
                    return {
                        "id": user_data.get("user_id", ""),
                        "username": user_data.get("username", ""),
                        "email": user_data.get("email", ""),
                        "name": user_data.get("display_name", "")
                    }
                    
        except Exception as e:
            logger.error(f"Error getting eBay user info: {e}")
            raise
    
    async def _get_amazon_user_info(self, token: OAuthToken) -> Dict[str, Any]:
        """Get Amazon user information"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}"
                }
                
                async with session.get("https://api.amazon.com/user/profile", headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get Amazon user info: {response.status}")
                    
                    user_data = await response.json()
                    return {
                        "id": user_data.get("user_id", ""),
                        "username": user_data.get("name", ""),
                        "email": user_data.get("email", ""),
                        "name": user_data.get("name", "")
                    }
                    
        except Exception as e:
            logger.error(f"Error getting Amazon user info: {e}")
            raise
    
    async def _get_mercari_user_info(self, token: OAuthToken) -> Dict[str, Any]:
        """Get Mercari user information"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}",
                    "Content-Type": "application/json"
                }
                
                async with session.get("https://api.mercari.com/v1/user/me", headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get Mercari user info: {response.status}")
                    
                    user_data = await response.json()
                    return {
                        "id": user_data.get("id", ""),
                        "username": user_data.get("username", ""),
                        "email": user_data.get("email", ""),
                        "name": user_data.get("name", "")
                    }
                    
        except Exception as e:
            logger.error(f"Error getting Mercari user info: {e}")
            raise
    
    async def _get_facebook_user_info(self, token: OAuthToken) -> Dict[str, Any]:
        """Get Facebook user information"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}"
                }
                
                async with session.get("https://graph.facebook.com/v18.0/me", headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get Facebook user info: {response.status}")
                    
                    user_data = await response.json()
                    return {
                        "id": user_data.get("id", ""),
                        "username": user_data.get("name", ""),
                        "email": user_data.get("email", ""),
                        "name": user_data.get("name", "")
                    }
                    
        except Exception as e:
            logger.error(f"Error getting Facebook user info: {e}")
            raise
    
    async def refresh_token(self, platform: Platform, user_id: str) -> bool:
        """Refresh OAuth token if expired"""
        try:
            token_key = f"{user_id}_{platform.value}"
            token = self.tokens.get(token_key)
            
            if not token:
                return False
            
            # Check if token needs refresh
            if datetime.now() < token.expires_at - timedelta(minutes=5):
                return True
            
            config = self.oauth_configs.get(platform)
            if not config:
                return False
            
            # Prepare refresh request
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
            
            # Make refresh request
            async with aiohttp.ClientSession() as session:
                async with session.post(config.token_url, data=refresh_data) as response:
                    if response.status != 200:
                        logger.error(f"Failed to refresh token for {platform.value}: {response.status}")
                        return False
                    
                    token_response = await response.json()
                    
                    # Update token
                    token.access_token = token_response["access_token"]
                    token.refresh_token = token_response.get("refresh_token", token.refresh_token)
                    token.expires_at = datetime.now() + timedelta(seconds=token_response.get("expires_in", 3600))
                    
                    # Store updated token
                    await self._store_token(user_id, platform, token)
                    
                    logger.info(f"Successfully refreshed token for {platform.value}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error refreshing token for {platform.value}: {e}")
            return False
    
    async def get_user_accounts(self, user_id: str) -> List[ConnectedAccount]:
        """Get all connected accounts for a user"""
        try:
            response = await self.supabase.from("connected_accounts").select("*").eq("user_id", user_id).execute()
            
            accounts = []
            for account_data in response.data:
                account = ConnectedAccount(
                    id=account_data["id"],
                    user_id=account_data["user_id"],
                    platform=Platform(account_data["platform"]),
                    username=account_data["username"],
                    platform_user_id=account_data["platform_user_id"],
                    is_active=account_data["is_active"],
                    last_sync=datetime.fromisoformat(account_data["last_sync"]) if account_data["last_sync"] else None,
                    metadata=account_data.get("metadata", {})
                )
                accounts.append(account)
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error getting user accounts: {e}")
            return []
    
    async def disconnect_account(self, user_id: str, platform: Platform) -> bool:
        """Disconnect a user's account from a platform"""
        try:
            # Remove from database
            await self.supabase.from("connected_accounts").delete().eq("user_id", user_id).eq("platform", platform.value).execute()
            
            # Remove token
            token_key = f"{user_id}_{platform.value}"
            if token_key in self.tokens:
                del self.tokens[token_key]
            
            logger.info(f"Disconnected {platform.value} account for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting account: {e}")
            return False
    
    async def get_platform_items(self, user_id: str, platform: Platform, limit: int = 50) -> List[Dict[str, Any]]:
        """Get items from a user's connected platform account"""
        try:
            # Get token
            token = await self._get_token(user_id, platform)
            if not token:
                raise Exception(f"No token found for {platform.value}")
            
            # Refresh token if needed
            if not await self.refresh_token(platform, user_id):
                raise Exception(f"Failed to refresh token for {platform.value}")
            
            # Get platform-specific items
            if platform == Platform.EBAY:
                return await self._get_ebay_items(token, limit)
            elif platform == Platform.AMAZON:
                return await self._get_amazon_items(token, limit)
            elif platform == Platform.MERCARI:
                return await self._get_mercari_items(token, limit)
            elif platform == Platform.FACEBOOK_MARKETPLACE:
                return await self._get_facebook_items(token, limit)
            else:
                raise ValueError(f"Unsupported platform: {platform.value}")
                
        except Exception as e:
            logger.error(f"Error getting items from {platform.value}: {e}")
            return []
    
    async def _get_ebay_items(self, token: OAuthToken, limit: int) -> List[Dict[str, Any]]:
        """Get eBay items for user"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Get user's listings
                async with session.get("https://api.ebay.com/sell/fulfillment/v1/order", headers=headers, params={"limit": limit}) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get eBay items: {response.status}")
                    
                    data = await response.json()
                    return data.get("orders", [])
                    
        except Exception as e:
            logger.error(f"Error getting eBay items: {e}")
            return []
    
    async def _get_amazon_items(self, token: OAuthToken, limit: int) -> List[Dict[str, Any]]:
        """Get Amazon items for user"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}"
                }
                
                # Get user's orders
                async with session.get("https://api.amazon.com/orders/v0/orders", headers=headers, params={"limit": limit}) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get Amazon items: {response.status}")
                    
                    data = await response.json()
                    return data.get("orders", [])
                    
        except Exception as e:
            logger.error(f"Error getting Amazon items: {e}")
            return []
    
    async def _get_mercari_items(self, token: OAuthToken, limit: int) -> List[Dict[str, Any]]:
        """Get Mercari items for user"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Get user's items
                async with session.get("https://api.mercari.com/v1/user/items", headers=headers, params={"limit": limit}) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get Mercari items: {response.status}")
                    
                    data = await response.json()
                    return data.get("items", [])
                    
        except Exception as e:
            logger.error(f"Error getting Mercari items: {e}")
            return []
    
    async def _get_facebook_items(self, token: OAuthToken, limit: int) -> List[Dict[str, Any]]:
        """Get Facebook Marketplace items for user"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"{token.token_type} {token.access_token}"
                }
                
                # Get user's marketplace items
                async with session.get("https://graph.facebook.com/v18.0/me/marketplace_listings", headers=headers, params={"limit": limit}) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get Facebook items: {response.status}")
                    
                    data = await response.json()
                    return data.get("data", [])
                    
        except Exception as e:
            logger.error(f"Error getting Facebook items: {e}")
            return []
    
    async def _store_oauth_state(self, user_id: str, platform: Platform, state: str):
        """Store OAuth state for verification"""
        try:
            state_data = {
                "user_id": user_id,
                "platform": platform.value,
                "state": state,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
            
            await self.supabase.from("oauth_states").insert(state_data)
            
        except Exception as e:
            logger.error(f"Error storing OAuth state: {e}")
    
    async def _get_oauth_state(self, user_id: str, platform: Platform) -> Optional[str]:
        """Get stored OAuth state"""
        try:
            response = await self.supabase.from("oauth_states").select("state").eq("user_id", user_id).eq("platform", platform.value).order("created_at", desc=True).limit(1).execute()
            
            if response.data:
                state_data = response.data[0]
                # Check if state is expired
                expires_at = datetime.fromisoformat(state_data["expires_at"])
                if datetime.now() < expires_at:
                    return state_data["state"]
                else:
                    # Delete expired state
                    await self.supabase.from("oauth_states").delete().eq("id", state_data["id"]).execute()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting OAuth state: {e}")
            return None
    
    async def _store_token(self, user_id: str, platform: Platform, token: OAuthToken):
        """Store OAuth token"""
        try:
            token_key = f"{user_id}_{platform.value}"
            self.tokens[token_key] = token
            
            # Store in database
            token_data = {
                "user_id": user_id,
                "platform": platform.value,
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "expires_at": token.expires_at.isoformat(),
                "token_type": token.token_type,
                "scope": token.scope,
                "platform_user_id": token.platform_user_id,
                "platform_username": token.platform_username
            }
            
            await self.supabase.from("oauth_tokens").upsert(token_data)
            
        except Exception as e:
            logger.error(f"Error storing token: {e}")
    
    async def _get_token(self, user_id: str, platform: Platform) -> Optional[OAuthToken]:
        """Get OAuth token"""
        try:
            token_key = f"{user_id}_{platform.value}"
            
            # Check if token is already loaded
            if token_key in self.tokens:
                token = self.tokens[token_key]
                # Check if token is expired
                if datetime.now() < token.expires_at:
                    return token
                else:
                    # Remove expired token
                    del self.tokens[token_key]
            
            # Load from database
            response = await self.supabase.from("oauth_tokens").select("*").eq("user_id", user_id).eq("platform", platform.value).execute()
            
            if response.data:
                token_data = response.data[0]
                token = OAuthToken(
                    platform=Platform(token_data["platform"]),
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"],
                    expires_at=datetime.fromisoformat(token_data["expires_at"]),
                    token_type=token_data["token_type"],
                    scope=token_data["scope"],
                    user_id=token_data["user_id"],
                    platform_user_id=token_data.get("platform_user_id", ""),
                    platform_username=token_data.get("platform_username", "")
                )
                
                self.tokens[token_key] = token
                return token
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting token: {e}")
            return None
    
    async def _store_connected_account(self, account: ConnectedAccount):
        """Store connected account"""
        try:
            account_data = {
                "id": account.id,
                "user_id": account.user_id,
                "platform": account.platform.value,
                "username": account.username,
                "platform_user_id": account.platform_user_id,
                "is_active": account.is_active,
                "last_sync": account.last_sync.isoformat() if account.last_sync else None,
                "metadata": account.metadata
            }
            
            await self.supabase.from("connected_accounts").upsert(account_data)
            
        except Exception as e:
            logger.error(f"Error storing connected account: {e}")
    
    async def sync_user_data(self, user_id: str) -> Dict[str, Any]:
        """Sync data from all connected platforms"""
        try:
            accounts = await self.get_user_accounts(user_id)
            sync_results = {}
            
            for account in accounts:
                if not account.is_active:
                    continue
                
                platform = account.platform
                try:
                    # Get items from platform
                    items = await self.get_platform_items(user_id, platform)
                    
                    # Store items in database
                    await self._store_synced_items(user_id, platform, items)
                    
                    # Update last sync time
                    account.last_sync = datetime.now()
                    await self._store_connected_account(account)
                    
                    sync_results[platform.value] = {
                        "success": True,
                        "items_count": len(items)
                    }
                    
                except Exception as e:
                    sync_results[platform.value] = {
                        "success": False,
                        "error": str(e)
                    }
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Error syncing user data: {e}")
            return {"error": str(e)}
    
    async def _store_synced_items(self, user_id: str, platform: Platform, items: List[Dict[str, Any]]):
        """Store synced items in database"""
        try:
            synced_items = []
            for item in items:
                synced_item = {
                    "user_id": user_id,
                    "platform": platform.value,
                    "item_data": item,
                    "synced_at": datetime.now().isoformat()
                }
                synced_items.append(synced_item)
            
            # Batch insert
            if synced_items:
                await self.supabase.from("synced_items").insert(synced_items)
                
        except Exception as e:
            logger.error(f"Error storing synced items: {e}")