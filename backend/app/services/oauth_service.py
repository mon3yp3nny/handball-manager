"""OAuth service for handling OAuth authentication."""
import json
import jwt
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.oauth_account import OAuthAccount, OAuthProvider
from app.schemas.oauth import OAuthUserInfo
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings


def verify_google_token(token: str) -> Optional[OAuthUserInfo]:
    """Verify Google ID token and extract user info."""
    try:
        # Decode token without verification (in production, verify signature using Google's certs)
        # For production, use Google's verification endpoint or library
        from google.auth.transport import requests
        from google.oauth2 import id_token
        
        request = requests.Request()
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, request, clock_skew_in_seconds=10
        )
        
        # Check issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return None
            
        return OAuthUserInfo(
            email=idinfo['email'],
            provider='google',
            provider_account_id=idinfo['sub'],
            first_name=idinfo.get('given_name'),
            last_name=idinfo.get('family_name'),
            picture=idinfo.get('picture'),
            is_verified_email=idinfo.get('email_verified', False)
        )
    except Exception as e:
        print(f"Google token verification error: {e}")
        return None


def verify_apple_token(token: str) -> Optional[OAuthUserInfo]:
    """Verify Apple ID token and extract user info."""
    try:
        # Apple's public keys URL
        import requests
        
        # Get Apple's public keys
        apple_keys_url = "https://appleid.apple.com/auth/keys"
        response = requests.get(apple_keys_url)
        keys = response.json()['keys']
        
        # Find the correct key
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header['kid']
        
        apple_key = None
        for key in keys:
            if key['kid'] == key_id:
                apple_key = key
                break
        
        if not apple_key:
            return None
        
        # Construct the public key
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        # Build RSA public key from JWK
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
        
        def base64url_to_int(data):
            import base64
            return int.from_bytes(base64.urlsafe_b64decode(data + '=='), 'big')
        
        n = base64url_to_int(apple_key['n'])
        e = base64url_to_int(apple_key['e'])
        
        public_key = RSAPublicNumbers(e, n).public_key(default_backend())
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=settings.APPLE_CLIENT_ID if hasattr(settings, 'APPLE_CLIENT_ID') else None,
            issuer='https://appleid.apple.com'
        )
        
        return OAuthUserInfo(
            email=payload['email'],
            provider='apple',
            provider_account_id=payload['sub'],
            first_name=None,  # Apple only provides name on first login
            last_name=None,
            picture=None,
            is_verified_email=payload.get('email_verified', False)
        )
    except Exception as e:
        print(f"Apple token verification error: {e}")
        return None


class OAuthService:
    """Service for OAuth authentication."""
    
    @staticmethod
    def get_or_create_user(
        db: Session, 
        oauth_info: OAuthUserInfo
    ) -> tuple[User, bool]:
        """
        Get or create user from OAuth info.
        Returns (user, is_new_user).
        """
        # Check if OAuth account already exists
        existing_oauth = db.query(OAuthAccount).filter(
            OAuthAccount.provider == OAuthProvider(oauth_info.provider),
            OAuthAccount.provider_account_id == oauth_info.provider_account_id
        ).first()
        
        if existing_oauth:
            # Update provider email if changed
            if existing_oauth.provider_email != oauth_info.email:
                existing_oauth.provider_email = oauth_info.email
                db.commit()
            return existing_oauth.user, False
        
        # Check if user exists with same email
        existing_user = db.query(User).filter(
            User.email == oauth_info.email
        ).first()
        
        if existing_user:
            # Link OAuth account to existing user
            oauth_account = OAuthAccount(
                user_id=existing_user.id,
                provider=OAuthProvider(oauth_info.provider),
                provider_account_id=oauth_info.provider_account_id,
                provider_email=oauth_info.email,
                provider_data=json.dumps({
                    'picture': oauth_info.picture,
                    'is_verified_email': oauth_info.is_verified_email
                })
            )
            db.add(oauth_account)
            db.commit()
            return existing_user, False
        
        # Create new user
        new_user = User(
            email=oauth_info.email,
            first_name=oauth_info.first_name or 'New',
            last_name=oauth_info.last_name or 'User',
            role=UserRole.PLAYER,  # Default role, can be changed later
            is_verified=oauth_info.is_verified_email,
            is_oauth_only=True
        )
        db.add(new_user)
        db.flush()
        
        # Create OAuth account
        oauth_account = OAuthAccount(
            user_id=new_user.id,
            provider=OAuthProvider(oauth_info.provider),
            provider_account_id=oauth_info.provider_account_id,
            provider_email=oauth_info.email,
            provider_data=json.dumps({
                'picture': oauth_info.picture,
                'is_verified_email': oauth_info.is_verified_email
            })
        )
        db.add(oauth_account)
        db.commit()
        
        return new_user, True
    
    @staticmethod
    def create_tokens(user: User) -> Dict[str, str]:
        """Create access and refresh tokens for user."""
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }


oauth_service = OAuthService()
