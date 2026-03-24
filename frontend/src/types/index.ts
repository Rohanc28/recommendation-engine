export interface Tag {
  id: string;
  name: string;
  slug: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Movie {
  id: string;
  title: string;
  description: string | null;
  year: number | null;
  poster_url: string | null;
  tags: Tag[];
  created_by: string | null;
  created_at: string;
  avg_rating: number | null;
  review_count: number;
}

export interface MovieListItem {
  id: string;
  title: string;
  description: string | null;
  year: number | null;
  poster_url: string | null;
  tags: Tag[];
  avg_rating: number | null;
  review_count: number;
}

export interface Review {
  id: string;
  movie_id: string;
  user_id: string;
  username: string;
  content: string;
  rating: number;
  created_at: string;
}

export interface VoteCounts {
  close: number;
  somewhat: number;
  different: number;
}

export interface RecommendationItem {
  movie_id: string;
  title: string;
  description: string | null;
  year: number | null;
  poster_url: string | null;
  tags: Tag[];
  avg_rating: number | null;
  final_score: number;
  embedding_score: number;
  tag_score: number;
  user_pref_score: number;
  community_vote_score: number;
  vote_counts: VoteCounts;
}

export type VoteType = "close" | "somewhat" | "different";
