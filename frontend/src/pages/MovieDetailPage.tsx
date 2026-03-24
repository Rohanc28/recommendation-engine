import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Star, Calendar, ArrowLeft, Sparkles } from "lucide-react";
import { moviesApi, reviewsApi, recommendationsApi } from "../services/api";
import ReviewCard from "../components/reviews/ReviewCard";
import ReviewForm from "../components/reviews/ReviewForm";
import SimilarityVote from "../components/movies/SimilarityVote";
import { useAuthStore } from "../store/authStore";

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-400">
        <span>{label}</span>
        <span>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-gray-800">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}

export default function MovieDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthStore();

  const { data: movie, isLoading: movieLoading } = useQuery({
    queryKey: ["movie", id],
    queryFn: () => moviesApi.get(id!),
    enabled: !!id,
  });

  const { data: reviews = [] } = useQuery({
    queryKey: ["reviews", id],
    queryFn: () => reviewsApi.list(id!),
    enabled: !!id,
  });

  const { data: recommendations = [], isLoading: recsLoading } = useQuery({
    queryKey: ["recommendations", id],
    queryFn: () => recommendationsApi.get(id!, 8),
    enabled: !!id,
    staleTime: 60_000,
  });

  const hasReviewed = reviews.some((r) => r.user_id === user?.id);

  if (movieLoading) {
    return <div className="card h-96 animate-pulse bg-gray-800" />;
  }
  if (!movie) {
    return <p className="text-gray-400">Movie not found.</p>;
  }

  return (
    <div className="space-y-8">
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-gray-100">
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>

      {/* Movie hero */}
      <div className="flex flex-col gap-6 sm:flex-row">
        {movie.poster_url ? (
          <img src={movie.poster_url} alt={movie.title}
            className="h-72 w-48 shrink-0 rounded-xl object-cover" />
        ) : (
          <div className="flex h-72 w-48 shrink-0 items-center justify-center rounded-xl bg-gray-800 text-6xl">
            🎬
          </div>
        )}
        <div className="flex-1 space-y-4">
          <div>
            <h1 className="text-3xl font-bold">{movie.title}</h1>
            {movie.year && (
              <p className="mt-1 flex items-center gap-1 text-gray-400">
                <Calendar className="h-4 w-4" /> {movie.year}
              </p>
            )}
          </div>

          {movie.description && (
            <p className="leading-relaxed text-gray-300">{movie.description}</p>
          )}

          <div className="flex flex-wrap gap-2">
            {movie.tags.map((t) => (
              <span key={t.id} className="rounded-full border border-brand-800 bg-brand-900/30 px-3 py-1 text-sm text-brand-300">
                {t.name}
              </span>
            ))}
          </div>

          <div className="flex items-center gap-4 text-sm">
            {movie.avg_rating != null && (
              <span className="flex items-center gap-1 text-yellow-400">
                <Star className="h-4 w-4 fill-current" />
                {movie.avg_rating.toFixed(1)} / 5
              </span>
            )}
            <span className="text-gray-400">{movie.review_count} review{movie.review_count !== 1 ? "s" : ""}</span>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold">
          <Sparkles className="h-5 w-5 text-brand-400" /> Similar Movies
        </h2>
        {recsLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="card h-48 animate-pulse bg-gray-800" />
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <p className="text-gray-500">No recommendations yet — add more movies!</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {recommendations.map((rec) => (
              <div key={rec.movie_id} className="card space-y-3">
                <Link to={`/movies/${rec.movie_id}`} className="block font-medium text-gray-200 hover:text-brand-400 transition-colors line-clamp-1">
                  {rec.title}
                </Link>

                {/* Hybrid score breakdown */}
                <div className="space-y-1.5">
                  <ScoreBar label="Semantic"   value={rec.embedding_score}      color="bg-blue-500" />
                  <ScoreBar label="Tags"        value={rec.tag_score}             color="bg-green-500" />
                  <ScoreBar label="Your Taste"  value={rec.user_pref_score}       color="bg-purple-500" />
                  <ScoreBar label="Community"   value={rec.community_vote_score}  color="bg-yellow-500" />
                </div>

                <div className="flex items-center justify-between border-t border-gray-800 pt-2">
                  <span className="text-xs text-gray-500">Match score</span>
                  <span className="font-semibold text-brand-400">
                    {(rec.final_score * 100).toFixed(0)}%
                  </span>
                </div>

                {user && (
                  <SimilarityVote
                    sourceMovieId={id!}
                    targetMovieId={rec.movie_id}
                    targetTitle={rec.title}
                    voteCounts={rec.vote_counts as { close: number; somewhat: number; different: number }}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Reviews */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Reviews ({reviews.length})</h2>
        {user && !hasReviewed && <ReviewForm movieId={id!} />}
        {reviews.length === 0 ? (
          <p className="text-gray-500">No reviews yet. Be the first!</p>
        ) : (
          <div className="space-y-3">
            {reviews.map((r) => <ReviewCard key={r.id} review={r} movieId={id!} />)}
          </div>
        )}
      </section>
    </div>
  );
}
