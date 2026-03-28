"""Setup endpoint for initial data and migrations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from datetime import datetime, timedelta

from app.core.deps import get_db
from app.core import security
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.player import Player
from app.models.game import Game, GameStatus, GameType
from app.models.event import Event, EventType, EventVisibility
from app.models.parent_child import ParentChild

router = APIRouter()


@router.post("/init")
def init_database(
    secret: str,
    db: Session = Depends(get_db)
):
    """Initialize database with migration and sample data.
    
    Requires secret key for protection.
    """
    # Simple protection - in production use proper auth
    if secret != "init-handball-2024":
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    results = []
    
    # 1. Migration: Add roles_data column
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'roles_data'
        """)).fetchone()
        
        if not result:
            db.execute(text("ALTER TABLE users ADD COLUMN roles_data TEXT"))
            db.commit()
            results.append("✅ Added roles_data column")
            
            # Migrate existing users
            users = db.query(User).all()
            for user in users:
                user.roles_data = json.dumps([user.role.value])
            db.commit()
            results.append(f"✅ Migrated {len(users)} users")
        else:
            results.append("ℹ️ roles_data column already exists")
    except Exception as e:
        results.append(f"❌ Migration error: {str(e)}")
    
    # 2. Create admin user
    try:
        admin = db.query(User).filter(User.email == "admin@handball.local").first()
        if not admin:
            admin = User(
                email="admin@handball.local",
                hashed_password=security.get_password_hash("Admin123!"),
                first_name="System",
                last_name="Administrator",
                role=UserRole.ADMIN,
                roles_data=json.dumps([UserRole.ADMIN.value]),
                is_verified=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            results.append("✅ Created admin: admin@handball.local / Admin123!")
        else:
            # Ensure admin has proper roles
            if admin.roles_data:
                roles = json.loads(admin.roles_data)
                if UserRole.ADMIN.value not in roles:
                    roles.append(UserRole.ADMIN.value)
                    admin.roles_data = json.dumps(roles)
                    db.commit()
            results.append("ℹ️ Admin user already exists")
    except Exception as e:
        results.append(f"❌ Admin error: {str(e)}")
    
    # 3. Create sample teams
    try:
        teams_data = [
            {'name': 'U10 Mix', 'age_group': 'U10'},
            {'name': 'U12 männlich', 'age_group': 'U12'},
            {'name': 'U12 weiblich', 'age_group': 'U12'},
            {'name': 'U14 männlich', 'age_group': 'U14'},
            {'name': 'U14 weiblich', 'age_group': 'U14'},
            {'name': 'U16 männlich', 'age_group': 'U16'},
            {'name': 'U16 weiblich', 'age_group': 'U16'},
            {'name': '1. Herren', 'age_group': 'Herren'},
            {'name': '1. Damen', 'age_group': 'Damen'},
        ]
        
        created = 0
        for team_data in teams_data:
            existing = db.query(Team).filter(Team.name == team_data['name']).first()
            if not existing:
                team = Team(**team_data)
                db.add(team)
                created += 1
        
        if created > 0:
            db.commit()
            results.append(f"✅ Created {created} teams")
        else:
            results.append("ℹ️ Teams already exist")
    except Exception as e:
        results.append(f"❌ Teams error: {str(e)}")
    
    # 4. Create multi-role users
    try:
        users_data = [
            {
                'email': 'max.mustermann@example.com',
                'password': 'Test123!',
                'first_name': 'Max',
                'last_name': 'Mustermann',
                'roles': [UserRole.COACH, UserRole.PLAYER, UserRole.PARENT],
                'player_team': 'U16 männlich',
                'coach_teams': ['U10 Mix'],
            },
            {
                'email': 'anna.schmidt@example.com',
                'password': 'Test123!',
                'first_name': 'Anna',
                'last_name': 'Schmidt',
                'roles': [UserRole.SUPERVISOR, UserRole.PARENT],
            },
            {
                'email': 'thomas.weber@example.com',
                'password': 'Test123!',
                'first_name': 'Thomas',
                'last_name': 'Weber',
                'roles': [UserRole.COACH, UserRole.PLAYER],
                'player_team': '1. Herren',
                'coach_teams': ['U14 männlich'],
            },
            {
                'email': 'lisa.mueller@example.com',
                'password': 'Test123!',
                'first_name': 'Lisa',
                'last_name': 'Müller',
                'roles': [UserRole.PLAYER],
                'player_team': 'U14 weiblich',
            },
        ]
        
        created = 0
        for user_data in users_data:
            existing = db.query(User).filter(User.email == user_data['email']).first()
            if not existing:
                user = User(
                    email=user_data['email'],
                    hashed_password=security.get_password_hash(user_data['password']),
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['roles'][0],
                    roles_data=json.dumps([r.value for r in user_data['roles']]),
                    is_verified=True,
                    is_active=True
                )
                db.add(user)
                db.commit()
                created += 1
                
                # Create player profile if needed
                if UserRole.PLAYER in user_data['roles'] and 'player_team' in user_data:
                    team = db.query(Team).filter(Team.name == user_data['player_team']).first()
                    if team:
                        player = Player(user_id=user.id, team_id=team.id)
                        db.add(player)
                        db.commit()
                
                # Assign as coach
                if UserRole.COACH in user_data['roles'] and 'coach_teams' in user_data:
                    for team_name in user_data['coach_teams']:
                        team = db.query(Team).filter(Team.name == team_name).first()
                        if team:
                            team.coach_id = user.id
                    db.commit()
        
        if created > 0:
            results.append(f"✅ Created {created} multi-role users")
        else:
            results.append("ℹ️ Sample users already exist")
    except Exception as e:
        results.append(f"❌ Users error: {str(e)}")
    
    # 5. Create sample games
    try:
        teams = db.query(Team).all()
        teams_map = {t.name: t for t in teams}
        
        games_data = [
            {'team': '1. Herren', 'opponent': 'TSV Musterstadt', 'days': 7},
            {'team': '1. Damen', 'opponent': 'SG Beispiel', 'days': 14},
            {'team': 'U16 männlich', 'opponent': 'U16 SG Test', 'days': 3},
        ]
        
        created = 0
        for game_data in games_data:
            if game_data['team'] in teams_map:
                team = teams_map[game_data['team']]
                scheduled = datetime.utcnow() + timedelta(days=game_data['days'])
                game = Game(
                    team_id=team.id,
                    opponent=game_data['opponent'],
                    location='Sporthalle',
                    scheduled_at=scheduled,
                    game_type=GameType.LEAGUE,
                    status=GameStatus.SCHEDULED,
                    is_home_game=True
                )
                db.add(game)
                created += 1
        
        if created > 0:
            db.commit()
            results.append(f"✅ Created {created} games")
        else:
            results.append("ℹ️ Games already exist")
    except Exception as e:
        results.append(f"❌ Games error: {str(e)}")
    
    # 6. Create sample events
    try:
        events_data = [
            {'title': 'Training U10', 'team': 'U10 Mix', 'days': 1, 'hours': 2},
            {'title': 'Jahreshauptversammlung', 'team': None, 'days': 5, 'hours': 3},
            {'title': 'Training 1. Herren', 'team': '1. Herren', 'days': 1, 'hours': 2},
        ]
        
        created = 0
        for event_data in events_data:
            team_id = None
            if event_data['team'] and event_data['team'] in teams_map:
                team_id = teams_map[event_data['team']].id
            
            start = datetime.utcnow() + timedelta(days=event_data['days'])
            end = start + timedelta(hours=event_data['hours'])
            
            event = Event(
                title=event_data['title'],
                team_id=team_id,
                event_type=EventType.TRAINING if 'Training' in event_data['title'] else EventType.MEETING,
                visibility=EventVisibility.TEAM if team_id else EventVisibility.CLUB,
                location='Sporthalle',
                start_time=start,
                end_time=end
            )
            db.add(event)
            created += 1
        
        if created > 0:
            db.commit()
            results.append(f"✅ Created {created} events")
        else:
            results.append("ℹ️ Events already exist")
    except Exception as e:
        results.append(f"❌ Events error: {str(e)}")
    
    return {
        "status": "completed",
        "results": results
    }


@router.get("/status")
def get_setup_status(
    db: Session = Depends(get_db)
):
    """Check setup status."""
    # Check migration
    migration_done = db.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'roles_data'
    """)).fetchone() is not None
    
    # Count entities
    stats = {
        "migration": "complete" if migration_done else "pending",
        "users": db.query(User).count(),
        "teams": db.query(Team).count(),
        "players": db.query(Player).count(),
        "games": db.query(Game).count(),
        "events": db.query(Event).count(),
    }
    
    # Check for multi-role users
    if migration_done:
        multi_role_users = db.query(User).filter(User.roles_data.isnot(None)).count()
        stats["multi_role_users"] = multi_role_users
    
    return stats
