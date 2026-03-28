"""Database migration endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.deps import get_db, require_admin

router = APIRouter()


@router.post("/run-migrations")
def run_migrations(
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Run database migrations (admin only)."""
    results = []
    
    # Migration: Add roles_data column for multi-role support
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS roles_data TEXT"))
        db.commit()
        results.append("✅ Added roles_data column to users table")
    except Exception as e:
        results.append(f"⚠️ roles_data column: {str(e)}")
    
    # Migration: Copy existing roles to roles_data
    try:
        db.execute(text("""
            UPDATE users 
            SET roles_data = CONCAT('["', role::text, '"]') 
            WHERE roles_data IS NULL
        """))
        db.commit()
        results.append("✅ Migrated existing roles to roles_data")
    except Exception as e:
        results.append(f"⚠️ Migrate roles: {str(e)}")
    
    return {
        "status": "completed",
        "migrations": results
    }


@router.get("/check-migration-status")
def check_migration_status(
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """Check if multi-role migration has been applied."""
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'roles_data'
        """)).fetchone()
        
        if result:
            # Check if data was migrated
            migrated = db.execute(text("""
                SELECT COUNT(*) FROM users WHERE roles_data IS NOT NULL
            """)).scalar()
            total = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            
            return {
                "roles_data_column": True,
                "migrated_users": migrated,
                "total_users": total,
                "status": "complete" if migrated == total else "partial"
            }
        else:
            return {
                "roles_data_column": False,
                "status": "pending"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
