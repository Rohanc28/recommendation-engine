import axios, { AxiosInstance } from "axios";
import type {
  AuthTokens, Movie, MovieListItem, Review, RecommendationItem, Tag
} from "../types";

// VITE_API_URL is injected at build time by Vercel / local .env
// Falls back to /api for local dev (proxied by Vite → localhost:8000)
const BASE = (import.meta.env.VITE_API_URL ?? "") + "/api";

function createClient(): AxiosInstance {
  const client = axios.create({ baseURL: BASE });

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  // Transparent JWT refresh on 401
  client.interceptors.response.use(
    (r) => r,
    async (err) => {
      const original = err.config;
      if (err.response?.status === 401 && !original._retry) {
        original._retry = true;
        const refresh = localStorage.getItem("refresh_token");
        if (refresh) {
          try {
            const { data } = await axios.post<AuthTokens>(`${BASE}/auth/refresh`, {
              refresh_token: refresh,
            });
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            original.headers.Authorization = `Bearer ${data.access_token}`;
            return client(original);
          } catch {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            window.location.href = "/login";
          }
        }
      }
      return Promise.reject(err);
    }
  );

  return client;
}

const http = createClient();

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (d: { username: string; email: string; password: string }) =>
    http.post<AuthTokens>("/auth/register", d).then((r) => r.data),
  login: (d: { email: string; password: string }) =>
    http.post<AuthTokens>("/auth/login", d).then((r) => r.data),
  me: () => http.get("/auth/me").then((r) => r.data),
};

// ── Movies ────────────────────────────────────────────────────────────────────
export const moviesApi = {
  list: (params?: { search?: string; tag?: string; page?: number }) =>
    http.get<MovieListItem[]>("/movies", { params }).then((r) => r.data),
  get: (id: string) =>
    http.get<Movie>(`/movies/${id}`).then((r) => r.data),
  create: (d: {
    title: string; description?: string; year?: number;
    poster_url?: string; tags: string[];
  }) => http.post<Movie>("/movies", d).then((r) => r.data),
  update: (id: string, d: Partial<{
    title: string; description: string; year: number; poster_url: string; tags: string[];
  }>) => http.patch<Movie>(`/movies/${id}`, d).then((r) => r.data),
  delete: (id: string) => http.delete(`/movies/${id}`),
};

// ── Reviews ───────────────────────────────────────────────────────────────────
export const reviewsApi = {
  list: (movieId: string) =>
    http.get<Review[]>(`/movies/${movieId}/reviews`).then((r) => r.data),
  create: (movieId: string, d: { content: string; rating: number }) =>
    http.post<Review>(`/movies/${movieId}/reviews`, d).then((r) => r.data),
  delete: (movieId: string, reviewId: string) =>
    http.delete(`/movies/${movieId}/reviews/${reviewId}`),
};

// ── Recommendations ───────────────────────────────────────────────────────────
export const recommendationsApi = {
  get: (movieId: string, limit = 10) =>
    http.get<RecommendationItem[]>(`/recommendations/${movieId}`, { params: { limit } })
      .then((r) => r.data),
};

// ── Votes ─────────────────────────────────────────────────────────────────────
export const votesApi = {
  cast: (movieId: string, movieIdB: string, voteType: string) =>
    http.post(`/movies/${movieId}/votes`, { movie_id_b: movieIdB, vote_type: voteType })
      .then((r) => r.data),
};

// ── Tags ──────────────────────────────────────────────────────────────────────
export const tagsApi = {
  search: (q: string) =>
    http.get<(Tag & { movie_count: number })[]>("/tags", { params: { q } })
      .then((r) => r.data),
};
