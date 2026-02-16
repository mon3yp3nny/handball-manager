"""OAuth Account model for tracking linked OAuth providers."""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class OAuthProvider(str, enum.Enum):
    GOOGLE = "google"
    APPLE = "apple"


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(Enum(OAuthProvider), nullable=False)
    provider_account_id = Column(String, nullable=False, index=True)
    provider_email = Column(String, nullable=True)
    provider_data = Column(String, nullable=True)  # JSON data from provider
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="oauth_accounts")
    
    def __repr__(self):
        return f"<OAuthAccount {self.provider}:{self.provider_account_id}>"
