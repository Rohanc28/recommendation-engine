"""Initial schema with pgvector

Revision ID: 001
Revises:
Create Date: 2026-03-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("slug", sa.String(60), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tags_name", "tags", ["name"])
    op.create_index("ix_tags_slug", "tags", ["slug"])

    op.create_table(
        "movies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("poster_url", sa.String(500), nullable=True),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_movies_title", "movies", ["title"])
    # IVFFlat index for approximate nearest-neighbour search on embeddings
    op.execute("CREATE INDEX ix_movies_embedding ON movies USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")

    op.create_table(
        "movie_tags",
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
        sa.UniqueConstraint("movie_id", "user_id", name="uq_review_movie_user"),
    )
    op.create_index("ix_reviews_movie_id", "reviews", ["movie_id"])
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])

    op.create_table(
        "similarity_votes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("movie_id_a", postgresql.UUID(as_uuid=True), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id_b", postgresql.UUID(as_uuid=True), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vote_type", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("vote_type IN ('close', 'somewhat', 'different')", name="vote_type_valid"),
        sa.UniqueConstraint("movie_id_a", "movie_id_b", "user_id", name="uq_vote_pair_user"),
    )
    op.create_index("ix_votes_movie_id_a", "similarity_votes", ["movie_id_a"])
    op.create_index("ix_votes_movie_id_b", "similarity_votes", ["movie_id_b"])

    op.create_table(
        "user_movie_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interaction_type", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "interaction_type IN ('viewed', 'reviewed', 'voted', 'added')",
            name="interaction_type_valid",
        ),
    )
    op.create_index("ix_interactions_user_id", "user_movie_interactions", ["user_id"])
    op.create_index("ix_interactions_movie_id", "user_movie_interactions", ["movie_id"])


def downgrade() -> None:
    op.drop_table("user_movie_interactions")
    op.drop_table("similarity_votes")
    op.drop_table("reviews")
    op.drop_table("movie_tags")
    op.drop_table("movies")
    op.drop_table("tags")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
