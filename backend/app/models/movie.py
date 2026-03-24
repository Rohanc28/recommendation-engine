import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.db_types import PortableUUID, EmbeddingType


movie_tags = Table(
    "movie_tags",
    Base.metadata,
    Column("movie_id", PortableUUID(), ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id",   PortableUUID(), ForeignKey("tags.id",   ondelete="CASCADE"), primary_key=True),
)


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Stored as JSON text; EmbeddingType handles serialization transparently
    embedding: Mapped[list | None] = mapped_column(EmbeddingType, nullable=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    creator = relationship("User", back_populates="movies", lazy="select")
    tags = relationship("Tag", secondary=movie_tags, back_populates="movies", lazy="selectin")
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan", lazy="select")
    votes_as_a = relationship(
        "SimilarityVote", foreign_keys="SimilarityVote.movie_id_a",
        back_populates="movie_a", cascade="all, delete-orphan", lazy="select",
    )
    votes_as_b = relationship(
        "SimilarityVote", foreign_keys="SimilarityVote.movie_id_b",
        back_populates="movie_b", cascade="all, delete-orphan", lazy="select",
    )
    interactions = relationship(
        "UserMovieInteraction", back_populates="movie", cascade="all, delete-orphan", lazy="select"
    )
