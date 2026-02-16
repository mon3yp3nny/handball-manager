from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core import security
from app.core.deps import get_db, get_current_user, require_admin, require_coach
from app.models.user import User, UserRole
from app.models.player import Player
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    db_user = User(
        email=user_data.email,
        hashed_password=security.get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create player profile if role is PLAYER
    if user_data.role == UserRole.PLAYER:
        player = Player(user_id=db_user.id)
        db.add(player)
        db.commit()
    
    return db_user


@router.get("/me/activity", response_model=List[dict])
def get_my_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity log for current user"""
    from app.models.user_activity import UserActivity
    
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": a.id,
            "activity_type": a.activity_type,
            "description": a.description,
            "created_at": a.created_at
        }
        for a in activities
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Parents can only see their children and themselves
    if current_user.role == UserRole.PARENT:
        if user_id != current_user.id:
            # Check if this user is their child
            from app.models.parent_child import ParentChild
            child_ids = [pc.child_id for pc in db.query(ParentChild).filter(ParentChild.parent_id == current_user.id).all()]
            if user_id not in child_ids:
                raise HTTPException(status_code=403, detail="Not authorized to view this user")
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization check
    if current_user.id != user_id and current_user.role not in [UserRole.ADMIN, UserRole.COACH]:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only admin can change role
    if user_data.role is not None and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can change user roles")
    
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Soft delete - just deactivate
    user.is_active = False
    db.commit()
    return {"message": "User deactivated"}


@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin: Reset user password and generate temporary password"""
    import secrets
    import string
    from app.models.user_activity import UserActivity, ActivityType
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate temporary password
    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    
    # Update password
    user.hashed_password = security.get_password_hash(temp_password)
    db.commit()
    
    # Log activity
    activity = UserActivity(
        user_id=user_id,
        activity_type=ActivityType.PASSWORD_CHANGE,
        description=f"Password reset by admin ({current_user.email})"
    )
    db.add(activity)
    db.commit()
    
    return {
        "message": "Password reset successfully",
        "temp_password": temp_password
    }


@router.get("/{user_id}/activity", response_model=List[dict])
def get_user_activity(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin: Get activity log for specific user"""
    from app.models.user_activity import UserActivity
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == user_id
    ).order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": a.id,
            "activity_type": a.activity_type,
            "description": a.description,
            "created_at": a.created_at
        }
        for a in activities
    ]


@router.get("/admin/stats", response_model=dict)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin dashboard stats"""
    from sqlalchemy import func
    
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    users_by_role = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    
    # Recent activity
    recent_activity = db.query(func.count(UserActivity.id)).filter(
        UserActivity.created_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "users_by_role": {str(role): count for role, count in users_by_role},
        "recent_activity_7d": recent_activity
    }


@router.post("/admin/bulk-activate")
def bulk_activate_users(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Bulk activate multiple users"""
    updated = 0
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user and not user.is_active:
            user.is_active = True
            updated += 1
    
    db.commit()
    return {"message": f"Activated {updated} users"}


@router.post("/admin/bulk-deactivate")
def bulk_deactivate_users(
    user_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Bulk deactivate multiple users"""
    updated = 0
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_active:
            user.is_active = False
            updated += 1
    
    db.commit()
    return {"message": f"Deactivated {updated} users"}
