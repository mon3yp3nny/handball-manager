"""Setup script for database migration and sample data."""
import os
import sys
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.player import Player
from app.models.game import Game, GameStatus, GameType
from app.models.event import Event, EventType, EventVisibility
from app.models.parent_child import ParentChild
from app.db.session import SessionLocal
from app.core import security
import json
from datetime import datetime, timedelta


def run_migration():
    """Add roles_data column for multi-role support."""
    db = SessionLocal()
    try:
        # Check if column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'roles_data'
        """)).fetchone()
        
        if not result:
            # Add column
            db.execute(text("ALTER TABLE users ADD COLUMN roles_data TEXT"))
            print("✅ Added roles_data column")
            
            # Migrate existing data
            users = db.query(User).all()
            for user in users:
                user.roles_data = json.dumps([user.role.value])
            db.commit()
            print(f"✅ Migrated {len(users)} users to multi-role format")
        else:
            print("ℹ️ roles_data column already exists")
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        db.rollback()
    finally:
        db.close()


def create_admin_user():
    """Create admin user if not exists."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == 'admin@handball.local').first()
        if not admin:
            admin = User(
                email='admin@handball.local',
                hashed_password=security.get_password_hash('Admin123!'),
                first_name='System',
                last_name='Administrator',
                role=UserRole.ADMIN,
                is_verified=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✅ Created admin user: admin@handball.local / Admin123!")
        else:
            print("ℹ️ Admin user already exists")
            
        # Ensure admin has admin role in roles_data
        if admin.roles_data:
            roles = json.loads(admin.roles_data)
            if UserRole.ADMIN.value not in roles:
                roles.append(UserRole.ADMIN.value)
                admin.roles_data = json.dumps(roles)
                db.commit()
                print("✅ Updated admin roles")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()


def create_sample_teams(db):
    """Create sample teams."""
    teams_data = [
        {'name': 'U10 Mix', 'age_group': 'U10', 'description': 'Gemischte U10 Mannschaft'},
        {'name': 'U12 männlich', 'age_group': 'U12', 'description': 'U12 männliche Jugend'},
        {'name': 'U12 weiblich', 'age_group': 'U12', 'description': 'U12 weibliche Jugend'},
        {'name': 'U14 männlich', 'age_group': 'U14', 'description': 'U14 männliche Jugend'},
        {'name': 'U14 weiblich', 'age_group': 'U14', 'description': 'U14 weibliche Jugend'},
        {'name': 'U16 männlich', 'age_group': 'U16', 'description': 'U16 männliche Jugend'},
        {'name': 'U16 weiblich', 'age_group': 'U16', 'description': 'U16 weibliche Jugend'},
        {'name': '1. Herren', 'age_group': 'Herren', 'description': '1. Männermannschaft'},
        {'name': '1. Damen', 'age_group': 'Damen', 'description': '1. Frauenmannschaft'},
    ]
    
    created = []
    for team_data in teams_data:
        existing = db.query(Team).filter(Team.name == team_data['name']).first()
        if not existing:
            team = Team(**team_data)
            db.add(team)
            created.append(team)
    
    if created:
        db.commit()
        print(f"✅ Created {len(created)} sample teams")
    else:
        print("ℹ️ Sample teams already exist")
    
    return db.query(Team).all()


def create_sample_users_with_roles(db, teams):
    """Create users with multiple roles."""
    users_data = [
        # Multi-role: Trainer + Spieler + Elternteil
        {
            'email': 'max.mustermann@example.com',
            'password': 'Test123!',
            'first_name': 'Max',
            'last_name': 'Mustermann',
            'roles': [UserRole.COACH, UserRole.PLAYER, UserRole.PARENT],
            'player_team': 'U16 männlich',
            'coach_teams': ['U10 Mix', 'U12 männlich'],
            'children': ['Tim Mustermann', 'Lisa Mustermann']
        },
        # Multi-role: Supervisor + Elternteil
        {
            'email': 'anna.schmidt@example.com',
            'password': 'Test123!',
            'first_name': 'Anna',
            'last_name': 'Schmidt',
            'roles': [UserRole.SUPERVISOR, UserRole.PARENT],
            'children': ['Emma Schmidt']
        },
        # Multi-role: Trainer + Spieler (aktiver Spieler-Trainer)
        {
            'email': 'thomas.weber@example.com',
            'password': 'Test123!',
            'first_name': 'Thomas',
            'last_name': 'Weber',
            'roles': [UserRole.COACH, UserRole.PLAYER],
            'player_team': '1. Herren',
            'coach_teams': ['U14 männlich']
        },
        # Spieler ohne andere Rolle
        {
            'email': 'lisa.mueller@example.com',
            'password': 'Test123!',
            'first_name': 'Lisa',
            'last_name': 'Müller',
            'roles': [UserRole.PLAYER],
            'player_team': 'U14 weiblich'
        },
        # Elternteil
        {
            'email': 'klaus.klein@example.com',
            'password': 'Test123!',
            'first_name': 'Klaus',
            'last_name': 'Klein',
            'roles': [UserRole.PARENT]
        },
        # Weitere Spieler
        {'email': 'peter.schulz@example.com', 'password': 'Test123!', 'first_name': 'Peter', 'last_name': 'Schulz', 'roles': [UserRole.PLAYER], 'player_team': '1. Herren'},
        {'email': 'sarah.meyer@example.com', 'password': 'Test123!', 'first_name': 'Sarah', 'last_name': 'Meyer', 'roles': [UserRole.PLAYER], 'player_team': '1. Damen'},
        {'email': 'lukas.fischer@example.com', 'password': 'Test123!', 'first_name': 'Lukas', 'last_name': 'Fischer', 'roles': [UserRole.PLAYER], 'player_team': 'U16 männlich'},
        {'email': 'marie.becker@example.com', 'password': 'Test123!', 'first_name': 'Marie', 'last_name': 'Becker', 'roles': [UserRole.PLAYER], 'player_team': 'U16 weiblich'},
    ]
    
    created_count = 0
    player_users = {}  # Map user_id to player_ids for parent-child relationships
    
    for user_data in users_data:
        existing = db.query(User).filter(User.email == user_data['email']).first()
        if existing:
            # Update roles if user exists
            if existing.roles_data:
                roles = json.loads(existing.roles_data)
            else:
                roles = [existing.role.value]
            
            for role in [r.value for r in user_data['roles']]:
                if role not in roles:
                    roles.append(role)
            
            existing.roles_data = json.dumps(roles)
            db.commit()
            user = existing
        else:
            # Create new user
            user = User(
                email=user_data['email'],
                hashed_password=security.get_password_hash(user_data['password']),
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['roles'][0],  # Primary role
                roles_data=json.dumps([r.value for r in user_data['roles']]),
                is_verified=True,
                is_active=True
            )
            db.add(user)
            db.commit()
            created_count += 1
        
        # Create player profile if PLAYER role exists
        if UserRole.PLAYER in user_data['roles'] and 'player_team' in user_data:
            team = next((t for t in teams if t.name == user_data['player_team']), None)
            if team:
                player = db.query(Player).filter(Player.user_id == user.id).first()
                if not player:
                    player = Player(
                        user_id=user.id,
                        team_id=team.id,
                        jersey_number=None
                    )
                    db.add(player)
                    db.commit()
                    player_users[user.id] = player.id
        
        # Assign coach to teams
        if UserRole.COACH in user_data['roles'] and 'coach_teams' in user_data:
            for team_name in user_data['coach_teams']:
                team = next((t for t in teams if t.name == team_name), None)
                if team:
                    team.coach_id = user.id
            db.commit()
    
    print(f"✅ Created/updated {created_count} sample users with multi-roles")
    
    # Create children for parents
    for user_data in users_data:
        if 'children' in user_data:
            parent = db.query(User).filter(User.email == user_data['email']).first()
            if parent:
                for child_name in user_data['children']:
                    # Find child player
                    child_first, child_last = child_name.split()
                    child_user = db.query(User).filter(
                        User.first_name == child_first,
                        User.last_name == child_last
                    ).first()
                    
                    if child_user and child_user.id in player_users:
                        # Create parent-child relationship
                        existing = db.query(ParentChild).filter(
                            ParentChild.parent_id == parent.id,
                            ParentChild.child_id == player_users[child_user.id]
                        ).first()
                        
                        if not existing:
                            rel = ParentChild(
                                parent_id=parent.id,
                                child_id=player_users[child_user.id]
                            )
                            db.add(rel)
    
    db.commit()
    print("✅ Created parent-child relationships")


def create_sample_games(db, teams):
    """Create sample games."""
    games_data = [
        {'team': '1. Herren', 'opponent': 'TSV Musterstadt', 'is_home': True, 'location': 'Sporthalle Handball-Club', 'days_from_now': 7},
        {'team': '1. Damen', 'opponent': 'SG Beispiel', 'is_home': False, 'location': 'Gegnerhalle Beispiel', 'days_from_now': 14},
        {'team': 'U16 männlich', 'opponent': 'U16 SG Test', 'is_home': True, 'location': 'Sporthalle Handball-Club', 'days_from_now': 3},
        {'team': 'U14 weiblich', 'opponent': 'U14 TV Sample', 'is_home': False, 'location': 'Mädchenhalle Sample', 'days_from_now': 10},
        {'team': '1. Herren', 'opponent': 'HSC Beispielstadt', 'is_home': False, 'location': 'Halle Beispielstadt', 'days_from_now': 21},
        {'team': '1. Damen', 'opponent': 'Damen SC Test', 'is_home': True, 'location': 'Sporthalle Handball-Club', 'days_from_now': 28},
    ]
    
    created = 0
    for game_data in games_data:
        team = next((t for t in teams if t.name == game_data['team']), None)
        if team:
            scheduled = datetime.utcnow() + timedelta(days=game_data['days_from_now'])
            
            existing = db.query(Game).filter(
                Game.team_id == team.id,
                Game.opponent == game_data['opponent'],
                Game.scheduled_at >= scheduled - timedelta(hours=1),
                Game.scheduled_at <= scheduled + timedelta(hours=1)
            ).first()
            
            if not existing:
                game = Game(
                    team_id=team.id,
                    opponent=game_data['opponent'],
                    location=game_data['location'],
                    scheduled_at=scheduled,
                    game_type=GameType.LEAGUE,
                    status=GameStatus.SCHEDULED,
                    is_home_game=game_data['is_home']
                )
                db.add(game)
                created += 1
    
    db.commit()
    print(f"✅ Created {created} sample games")


def create_sample_events(db, teams):
    """Create sample events."""
    events_data = [
        {'title': 'Training U10', 'team': 'U10 Mix', 'type': EventType.TRAINING, 'days_from_now': 1, 'duration_hours': 2},
        {'title': 'Training U12 männlich', 'team': 'U12 männlich', 'type': EventType.TRAINING, 'days_from_now': 2, 'duration_hours': 2},
        {'title': 'Jahreshauptversammlung', 'team': None, 'type': EventType.MEETING, 'days_from_now': 5, 'duration_hours': 3},
        {'title': 'Training 1. Herren', 'team': '1. Herren', 'type': EventType.TRAINING, 'days_from_now': 1, 'duration_hours': 2},
        {'title': 'Turnier Vorbereitung', 'team': 'U14 männlich', 'type': EventType.TOURNAMENT, 'days_from_now': 7, 'duration_hours': 8},
        {'title': 'Elternabend U12', 'team': 'U12 männlich', 'type': EventType.MEETING, 'days_from_now': 4, 'duration_hours': 2},
    ]
    
    created = 0
    for event_data in events_data:
        team_id = None
        if event_data['team']:
            team = next((t for t in teams if t.name == event_data['team']), None)
            if team:
                team_id = team.id
        
        start = datetime.utcnow() + timedelta(days=event_data['days_from_now'])
        end = start + timedelta(hours=event_data['duration_hours'])
        
        event = Event(
            title=event_data['title'],
            team_id=team_id,
            event_type=event_data['type'],
            visibility=EventVisibility.TEAM if team_id else EventVisibility.CLUB,
            location='Sporthalle Handball-Club',
            start_time=start,
            end_time=end
        )
        db.add(event)
        created += 1
    
    db.commit()
    print(f"✅ Created {created} sample events")


def main():
    """Run all setup tasks."""
    print("=" * 50)
    print("Handball Manager - Database Setup")
    print("=" * 50)
    print()
    
    # Run migration
    print("📦 Running migrations...")
    run_migration()
    print()
    
    # Create admin
    print("👤 Creating admin user...")
    create_admin_user()
    print()
    
    # Get DB session for sample data
    db = SessionLocal()
    try:
        # Create teams
        print("🏆 Creating sample teams...")
        teams = create_sample_teams(db)
        print()
        
        # Create users with multi-roles
        print("👥 Creating sample users with multi-roles...")
        create_sample_users_with_roles(db, teams)
        print()
        
        # Create games
        print("🎮 Creating sample games...")
        create_sample_games(db, teams)
        print()
        
        # Create events
        print("📅 Creating sample events...")
        create_sample_events(db, teams)
        print()
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("=" * 50)
    print("✅ Setup complete!")
    print("=" * 50)
    print()
    print("Sample Users (email / password):")
    print("  admin@handball.local / Admin123!")
    print("  max.mustermann@example.com / Test123!")
    print("  anna.schmidt@example.com / Test123!")
    print("  thomas.weber@example.com / Test123!")
    print()
    print("Multi-role examples:")
    print("  Max Mustermann: Coach + Player + Parent")
    print("  Anna Schmidt: Supervisor + Parent")
    print("  Thomas Weber: Coach + Player")


if __name__ == "__main__":
    main()
