from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db, get_current_user, require_admin
from app.models.user import User, UserRole
from app.models.player import Player
from app.models.parent_child import ParentChild
from app.schemas.user import UserResponse
from app.schemas.player import PlayerResponse

router = APIRouter()


@router.get("/children", response_model=List[PlayerResponse])
def get_my_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all children linked to the current parent user"""
    if current_user.role != UserRole.PARENT and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only parents can view children")
    
    children = db.query(Player).join(
        ParentChild, ParentChild.child_id == Player.id
    ).filter(ParentChild.parent_id == current_user.id).all()
    
    return children


@router.post("/children/{player_id}", response_model=UserResponse)
def link_child(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a child player to the current user as parent"""
    if current_user.role != UserRole.PARENT and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only parents can link children")
    
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Check if already linked
    existing = db.query(ParentChild).filter(
        ParentChild.parent_id == current_user.id,
        ParentChild.child_id == player_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already linked to this child")
    
    # Set role to PARENT if not already
    if current_user.role != UserRole.PARENT and current_user.role != UserRole.ADMIN:
        current_user.role = UserRole.PARENT
        db.commit()
    
    link = ParentChild(
        parent_id=current_user.id,
        child_id=player_id
    )
    db.add(link)
    db.commit()
    
    return current_user


@router.delete("/children/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_child(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unlink a child from the current parent"""
    if current_user.role != UserRole.PARENT and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    link = db.query(ParentChild).filter(
        ParentChild.parent_id == current_user.id,
        ParentChild.child_id == player_id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db.delete(link)
    db.commit()
    return {"message": "Child unlinked"}


@router.get("/{parent_id}/children", response_model=List[PlayerResponse])
def get_parent_children(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Admin: Get all children for a specific parent"""
    parent = db.query(User).filter(User.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    children = db.query(Player).join(
        ParentChild, ParentChild.child_id == Player.id
    ).filter(ParentChild.parent_id == parent_id).all()
    
    return children


@router.get("/player/{player_id}/parents", response_model=List[UserResponse])
def get_player_parents(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all parents for a specific player"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Authorization - player can see their own parents, parents their children's parents
    if current_user.role == UserRole.PLAYER:
        if player.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.PARENT:
        # Check if this is their child
        link = db.query(ParentChild).filter(
            ParentChild.parent_id == current_user.id,
            ParentChild.child_id == player_id
        ).first()
        if not link:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    parents = db.query(User).join(
        ParentChild, ParentChild.parent_id == User.id
    ).filter(ParentChild.child_id == player_id).all()
    
    return parents
