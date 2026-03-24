import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.db_types import PortableUUID


class SimilarityVote(Base):
    __tablename__ = "similarity_votes"
    __table_args__ = (
        CheckConstraint("vote_type IN ('close', 'somewhat', 'different')", name="vote_type_valid"),
        UniqueConstraint("movie_id_a", "movie_id_b", "user_id", name="uq_vote_pair_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    movie_id_a: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    movie_id_b: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vote_type: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    movie_a = relationship("Movie", foreign_keys=[movie_id_a], back_populates="votes_as_a", lazy="select")
    movie_b = relationship("Movie", foreign_keys=[movie_id_b], back_populates="votes_as_b", lazy="select")
    user = relationship("User", back_populates="similarity_votes", lazy="select")

    @property
    def score(self) -> float:
        return {"close": 1.0, "somewhat": 0.5, "different": 0.0}.get(self.vote_type, 0.0)
