from app.models.user import User
from app.models.tag import Tag
from app.models.movie import Movie, movie_tags
from app.models.review import Review
from app.models.similarity_vote import SimilarityVote
from app.models.user_interaction import UserMovieInteraction

__all__ = [
    "User",
    "Tag",
    "Movie",
    "movie_tags",
    "Review",
    "SimilarityVote",
    "UserMovieInteraction",
]
