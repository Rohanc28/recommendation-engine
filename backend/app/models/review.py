import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, Integer, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.db_types import PortableUUID


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),
        UniqueConstraint("movie_id", "user_id", name="uq_review_movie_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    movie_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    movie = relationship("Movie", back_populates="reviews", lazy="select")
    user = relationship("User", back_populates="reviews", lazy="select")
