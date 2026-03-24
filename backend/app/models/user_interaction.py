import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.db_types import PortableUUID


class UserMovieInteraction(Base):
    __tablename__ = "user_movie_interactions"
    __table_args__ = (
        CheckConstraint(
            "interaction_type IN ('viewed', 'reviewed', 'voted', 'added')",
            name="interaction_type_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movie_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="interactions", lazy="select")
    movie = relationship("Movie", back_populates="interactions", lazy="select")
