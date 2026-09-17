"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sys_user",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(128), nullable=False, unique=True),
        sa.Column("nickname", sa.String(64), nullable=True),
        sa.Column("avatar", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("user", "admin", name="user_role"), nullable=False, server_default="user"),
        sa.Column("status", sa.Integer, nullable=False, server_default="1"),
        sa.Column("settings_json", sa.JSON, nullable=True),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
        sa.Column("last_login_ip", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_email", "sys_user", ["email"])
    op.create_index("idx_role_status", "sys_user", ["role", "status"])
    op.create_index("idx_created_at", "sys_user", ["created_at"])

    op.create_table(
        "rec_record",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("type", sa.Enum("travel", "ocr", "currency", "product", "face", name="rec_type"), nullable=False),
        sa.Column("input_url", sa.String(512), nullable=True),
        sa.Column("input_type", sa.Enum("image", "video_frame", "video", name="rec_input_type"), nullable=True, server_default="image"),
        sa.Column("result_text", sa.Text, nullable=True),
        sa.Column("result_json", sa.JSON, nullable=True),
        sa.Column("confidence", sa.DECIMAL(5, 4), nullable=True),
        sa.Column("cost_ms", sa.Integer, nullable=True),
        sa.Column("is_fallback", sa.Integer, nullable=False, server_default="0"),
        sa.Column("audio_url", sa.String(512), nullable=True),
        sa.Column("thumbnail", sa.String(512), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_user_type_time", "rec_record", ["user_id", "type", "created_at"])
    op.create_index("idx_type_time", "rec_record", ["type", "created_at"])

    op.create_table(
        "fb_feedback",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("contact", sa.String(128), nullable=True),
        sa.Column("record_id", sa.BigInteger, nullable=True),
        sa.Column("status", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reply", sa.Text, nullable=True),
        sa.Column("replied_at", sa.DateTime, nullable=True),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column("extra", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    op.create_table(
        "tpl_prompt",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scene", sa.String(32), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("variables", sa.JSON, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_by", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_scene_active", "tpl_prompt", ["scene", "is_active", "version"])

    op.create_table(
        "log_api_call",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=True),
        sa.Column("endpoint", sa.String(128), nullable=False),
        sa.Column("method", sa.String(8), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=False, server_default="200"),
        sa.Column("cost_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ai_provider", sa.String(32), nullable=True),
        sa.Column("is_fallback", sa.Integer, nullable=False, server_default="0"),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("error_msg", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_endpoint_time", "log_api_call", ["endpoint", "created_at"])
    op.create_index("idx_user_time", "log_api_call", ["user_id", "created_at"])

    op.create_table(
        "cfg_verification",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(128), nullable=False),
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False, server_default="login"),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("is_deleted", sa.Integer, nullable=False, server_default="0"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index("idx_email_purpose", "cfg_verification", ["email", "purpose", "used"])
    op.create_index("idx_expires", "cfg_verification", ["expires_at"])


def downgrade() -> None:
    op.drop_table("cfg_verification")
    op.drop_table("log_api_call")
    op.drop_table("tpl_prompt")
    op.drop_table("fb_feedback")
    op.drop_table("rec_record")
    op.drop_table("sys_user")
