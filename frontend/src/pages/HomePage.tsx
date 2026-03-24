import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Film } from "lucide-react";
import { moviesApi } from "../services/api";
import MovieCard from "../components/movies/MovieCard";

export default function HomePage() {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  const { data: movies = [], isLoading } = useQuery({
    queryKey: ["movies", debouncedSearch],
    queryFn: () => moviesApi.list({ search: debouncedSearch || undefined }),
    staleTime: 30_000,
  });

  const handleSearch = (v: string) => {
    setSearch(v);
    clearTimeout((window as { _st?: ReturnType<typeof setTimeout> })._st);
    (window as { _st?: ReturnType<typeof setTimeout> })._st = setTimeout(() => setDebouncedSearch(v), 350);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Discover Movies</h1>
          <p className="mt-1 text-gray-400">Community-driven recommendations powered by AI</p>
        </div>
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="input pl-9"
            placeholder="Search movies…"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="card h-72 animate-pulse bg-gray-800" />
          ))}
        </div>
      ) : movies.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-20 text-center">
          <Film className="h-16 w-16 text-gray-700" />
          <p className="text-xl font-medium text-gray-400">No movies found</p>
          <p className="text-gray-500">Be the first to add one!</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {movies.map((m) => <MovieCard key={m.id} movie={m} />)}
        </div>
      )}
    </div>
  );
}
