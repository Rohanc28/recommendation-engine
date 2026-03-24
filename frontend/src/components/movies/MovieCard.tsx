import { Link } from "react-router-dom";
import { Star, MessageSquare, Calendar } from "lucide-react";
import type { MovieListItem } from "../../types";

interface Props {
  movie: MovieListItem;
}

export default function MovieCard({ movie }: Props) {
  return (
    <Link
      to={`/movies/${movie.id}`}
      className="card group flex flex-col gap-3 hover:border-brand-700 transition-colors"
    >
      {movie.poster_url ? (
        <img
          src={movie.poster_url}
          alt={movie.title}
          className="h-48 w-full rounded-lg object-cover"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />
      ) : (
        <div className="flex h-48 w-full items-center justify-center rounded-lg bg-gray-800 text-4xl">
          🎬
        </div>
      )}

      <div className="flex-1 space-y-2">
        <h3 className="font-semibold text-gray-100 group-hover:text-brand-400 transition-colors line-clamp-1">
          {movie.title}
        </h3>

        {movie.description && (
          <p className="text-sm text-gray-400 line-clamp-2">{movie.description}</p>
        )}

        <div className="flex flex-wrap gap-1">
          {movie.tags.slice(0, 3).map((t) => (
            <span key={t.id} className="rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-400">
              {t.name}
            </span>
          ))}
          {movie.tags.length > 3 && (
            <span className="rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-500">
              +{movie.tags.length - 3}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 text-xs text-gray-500">
          {movie.year && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" /> {movie.year}
            </span>
          )}
          {movie.avg_rating != null && (
            <span className="flex items-center gap-1 text-yellow-400">
              <Star className="h-3 w-3 fill-current" />
              {movie.avg_rating.toFixed(1)}
            </span>
          )}
          <span className="flex items-center gap-1">
            <MessageSquare className="h-3 w-3" /> {movie.review_count}
          </span>
        </div>
      </div>
    </Link>
  );
}
