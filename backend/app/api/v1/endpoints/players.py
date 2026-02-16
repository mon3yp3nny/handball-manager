from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_coach, require_admin
from app.models.user import User, UserRole
from app.models.player import Player
from app.models.team import Team
from app.schemas.player import PlayerCreate, PlayerUpdate, PlayerResponse, PlayerWithStats

router = APIRouter()


@router.get("/", response_model=List[PlayerResponse])
def get_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Player).join(User, Player.user_id == User.id)
    
    # Role-based filtering
    if current_user.role == UserRole.PLAYER:
        # Players see themselves and teammates
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and current_player.team_id:
            query = query.filter(Player.team_id == current_player.team_id)
    elif current_user.role == UserRole.PARENT:
        # Parents see their children and their teammates
        from app.models.parent_child import ParentChild
        child_ids = db.query(ParentChild.child_id).filter(ParentChild.parent_id == current_user.id).subquery()
        child_team_ids = db.query(Player.team_id).filter(Player.id.in_(child_ids)).subquery()
        query = query.filter(
            (Player.id.in_(child_ids)) | (Player.team_id.in_(child_team_ids))
        )
    elif current_user.role == UserRole.COACH:
        # Coaches see players in their teams
        coach_team_ids = db.query(Team.id).filter(Team.coach_id == current_user.id).subquery()
        query = query.filter(Player.team_id.in_(coach_team_ids))
    
    if team_id:
        query = query.filter(Player.team_id == team_id)
    
    players = query.offset(skip).limit(limit).all()
    return players


@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(
    player_data: PlayerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    """Create player with optional parent linking."""
    from app.models.parent_child import ParentChild
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    import secrets
    import string
    
    # Check if user exists
    user = db.query(User).filter(User.id == player_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if player profile already exists
    existing = db.query(Player).filter(Player.user_id == player_data.user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Player profile already exists for this user")
    
    # Extract parent_ids and create_parents from data
    parent_ids = player_data.parent_ids or []
    create_parents = player_data.create_parents or []
    
    # Remove from player_data dict before creating player
    player_dict = player_data.dict(exclude={"parent_ids", "create_parents"}, exclude_unset=True)
    
    db_player = Player(**player_dict)
    db.add(db_player)
    db.flush()  # Get player ID before commit
    
    # Create new parent users
    created_parent_ids = []
    for parent_data in create_parents:
        # Generate random password
        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.email == parent_data['email']).first()
        if existing_user:
            # If exists and is a parent, link them
            if existing_user.role == UserRole.PARENT:
                created_parent_ids.append(existing_user.id)
                # Send notification
                print(f"📧 Email sent to {parent_data['email']}: Ihr Kind wurde hinzugefügt")
            continue
        
        # Create new parent user
        new_parent = User(
            email=parent_data['email'],
            first_name=parent_data['first_name'],
            last_name=parent_data['last_name'],
            phone=parent_data.get('phone'),
            role=UserRole.PARENT,
            hashed_password=get_password_hash(password),
            is_verified=True
        )
        db.add(new_parent)
        db.flush()
        created_parent_ids.append(new_parent.id)
        
        # TODO: Send email with credentials
        print(f"""
        📧 NEW PARENT ACCOUNT
        To: {parent_data['email']}
        Subject: Ihr Handball Manager Konto
        
        Hallo {parent_data['first_name']},
        
        Ein Konto wurde für Sie erstellt. Sie können sich mit folgenden Daten anmelden:
        
        Email: {parent_data['email']}
        Passwort: {password}
        
        Bitte ändern Sie Ihr Passwort nach dem ersten Login.
        """)
    
    # Link parents to player
    all_parent_ids = set(parent_ids + created_parent_ids)
    for parent_id in all_parent_ids:
        # Verify parent exists and has PARENT role
        parent = db.query(User).filter(User.id == parent_id).first()
        if parent and (parent.role == UserRole.PARENT or parent.role == UserRole.ADMIN):
            link = ParentChild(parent_id=parent_id, child_id=db_player.id)
            db.add(link)
            
            # Send notification to parent
            print(f"📧 Parent {parent.email} linked to player {user.first_name} {user.last_name}")
    
    db.commit()
    db.refresh(db_player)
    return db_player


@router.get("/{player_id}", response_model=PlayerWithStats)
def get_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Authorization check
    if current_user.role == UserRole.PLAYER:
        # Can see themselves and teammates
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and player.team_id != current_player.team_id and player.id != current_player.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.PARENT:
        # Can see their children and children's teammates
        from app.models.parent_child import ParentChild
        child_ids = [pc.child_id for pc in db.query(ParentChild).filter(ParentChild.parent_id == current_user.id).all()]
        if player.id not in child_ids:
            child_team_ids = [db.query(Player.team_id).filter(Player.id == cid).scalar() for cid in child_ids]
            if player.team_id not in child_team_ids:
                raise HTTPException(status_code=403, detail="Not authorized")
    
    # Load team name and parents
    team = db.query(Team).filter(Team.id == player.team_id).first()
    parents = db.query(User).join(
        ParentChild, ParentChild.parent_id == User.id
    ).filter(ParentChild.child_id == player_id).all()
    
    player_data = {
        "id": player.id,
        "user_id": player.user_id,
        "team_id": player.team_id,
        "jersey_number": player.jersey_number,
        "position": player.position,
        "date_of_birth": player.date_of_birth,
        "emergency_contact_name": player.emergency_contact_name,
        "emergency_contact_phone": player.emergency_contact_phone,
        "games_played": player.games_played,
        "goals_scored": player.goals_scored,
        "assists": player.assists,
        "created_at": player.created_at,
        "updated_at": player.updated_at,
        "user": {
            "id": player.user.id,
            "email": player.user.email,
            "first_name": player.user.first_name,
            "last_name": player.user.last_name,
            "phone": player.user.phone,
            "role": player.user.role,
            "is_active": player.user.is_active,
            "is_verified": player.user.is_verified,
            "created_at": player.user.created_at,
            "updated_at": player.user.updated_at
        },
        "team_name": team.name if team else None,
        "parents": [
            {
                "id": p.id,
                "email": p.email,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "phone": p.phone
            }
            for p in parents
        ]
    }
    
    return player_data


@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: int,
    player_data: PlayerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Authorization
    if current_user.role == UserRole.PLAYER:
        # Players can only update their own info (limited)
        if player.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Players can't change team or stats
        update_data = player_data.dict(exclude_unset=True, exclude={"team_id", "games_played", "goals_scored", "assists"})
    elif current_user.role == UserRole.COACH:
        # Coaches can update their team's players
        team = db.query(Team).filter(Team.id == player.team_id).first()
        if not team or team.coach_id != current_user.id:
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized")
        update_data = player_data.dict(exclude_unset=True)
    else:
        update_data = player_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(player, field, value)
    
    db.commit()
    db.refresh(player)
    return player


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    db.delete(player)
    db.commit()
    return {"message": "Player deleted"}


@router.get("/{player_id}/children", response_model=List[PlayerResponse])
def get_player_children(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get linked children (for parent-child relationship)"""
    from app.models.parent_child import ParentChild
    
    # Check if current user is parent of this player
    parent_rel = db.query(ParentChild).filter(
        ParentChild.child_id == player_id,
        ParentChild.parent_id == current_user.id
    ).first()
    
    if not parent_rel and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    children = db.query(Player).join(
        ParentChild, ParentChild.child_id == Player.id
    ).filter(ParentChild.parent_id == current_user.id).all()
    
    return children
