"""OAuth configuration for Apple and Google Sign In."""
import os
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

# OAuth instance
oauth = OAuth()

# Configure Google OAuth
google_config = {
    'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
    'client_secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
    'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
    'client_kwargs': {
        'scope': 'openid email profile'
    }
}

# Register Google
if google_config['client_id']:
    oauth.register(
        name='google',
        **google_config
    )

# Apple OAuth configuration
# Note: Apple uses JWT-based client authentication, not client secret
apple_config = {
    'client_id': os.getenv('APPLE_CLIENT_ID', ''),  # App ID or Service ID
    'client_secret': None,  # Will be generated dynamically as JWT
    'authorize_url': 'https://appleid.apple.com/auth/authorize',
    'access_token_url': 'https://appleid.apple.com/auth/token',
    'api_base_url': 'https://appleid.apple.com',
    'client_kwargs': {
        'scope': 'name email',
        'response_mode': 'form_post'
    },
    'jwks_uri': 'https://appleid.apple.com/auth/keys'
}

# Register Apple (configuration only, actual auth handled separately due to JWT client secret)
if apple_config['client_id']:
    oauth.register(
        name='apple',
        **apple_config
    )


def get_oauth():
    """Get configured OAuth instance."""
    return oauth


def is_oauth_configured(provider: str) -> bool:
    """Check if OAuth provider is configured."""
    if provider == 'google':
        return bool(os.getenv('GOOGLE_CLIENT_ID'))
    elif provider == 'apple':
        return bool(os.getenv('APPLE_CLIENT_ID'))
    return False