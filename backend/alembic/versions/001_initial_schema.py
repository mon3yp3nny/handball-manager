"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column(
            "role",
            sa.Enum("admin", "coach", "supervisor", "player", "parent", name="userrole"),
            nullable=False,
            server_default="player",
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_oauth_only", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("age_group", sa.String(), nullable=True),
        sa.Column("coach_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- players ---
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("jersey_number", sa.Integer(), nullable=True),
        sa.Column(
            "position",
            sa.Enum(
                "goalkeeper", "left_wing", "left_back", "center_back",
                "right_back", "right_wing", "pivot", "defense",
                name="position",
            ),
            nullable=True,
        ),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("emergency_contact_name", sa.String(), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(), nullable=True),
        sa.Column("games_played", sa.Integer(), server_default="0"),
        sa.Column("goals_scored", sa.Integer(), server_default="0"),
        sa.Column("assists", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- parent_children ---
    op.create_table(
        "parent_children",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("child_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- games ---
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("opponent", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column(
            "game_type",
            sa.Enum("league", "tournament", "friendly", "cup", name="gametype"),
            server_default="league",
        ),
        sa.Column(
            "status",
            sa.Enum("scheduled", "in_progress", "completed", "cancelled", name="gamestatus"),
            server_default="scheduled",
        ),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("is_home_game", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- events ---
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum("training", "meeting", "tournament", "other", name="eventtype"),
            server_default="training",
        ),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- attendance ---
    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=True),
        sa.Column(
            "status",
            sa.Enum("present", "absent", "excused", "pending", name="attendancestatus"),
            server_default="pending",
        ),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("recorded_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- news ---
    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- oauth_accounts ---
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("google", "apple", name="oauthprovider"),
            nullable=False,
        ),
        sa.Column("provider_account_id", sa.String(), nullable=False, index=True),
        sa.Column("provider_email", sa.String(), nullable=True),
        sa.Column("provider_data", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # --- invitations ---
    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(), nullable=False, index=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("invited_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "expired", "revoked", name="invitationstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("token", sa.String(), unique=True, nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("invitations")
    op.drop_table("oauth_accounts")
    op.drop_table("news")
    op.drop_table("attendance")
    op.drop_table("events")
    op.drop_table("games")
    op.drop_table("parent_children")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("users")

    # Drop enum types
    sa.Enum(name="invitationstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="oauthprovider").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="attendancestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="eventtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="gamestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="gametype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="position").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
