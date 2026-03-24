# Recommendation Engine 

A full-stack movie recommendation platform that combines semantic AI embeddings, tag-based similarity, your personal watch history, and real-time crowd wisdom into a single hybrid score.

---

## How the Recommendation Engine Works

Example: When you ask "what's similar to Inception?", five things happen in sequence:

### 1. Semantic Embedding (50% of score)
Every movie is encoded into a 384-dimensional vector using **`all-MiniLM-L6-v2`** (sentence-transformers). The encoding input is:
```
"{title}. {overview}. {genre tags}"
```
Vectors are L2-normalised at index time, so similarity reduces to a pure dot product at query time — O(N) with numpy, no database extension needed.

### 2. Tag Jaccard Similarity (20%)
Each movie carries 3–5 genre/decade tags (e.g. `sci-fi`, `thriller`, `2010s`). The Jaccard coefficient between the source movie's tag set and each candidate is:
```
|A ∩ B| / |A ∪ B|
```
This catches cases where two movies are thematically close but lexically dissimilar (e.g. "dark fantasy" vs. "gothic horror").

### 3. User Preference Score (20%)
Built from your interaction history (views, ratings, votes). The engine collects all tags from movies you've interacted with into a personal taste profile, then scores each candidate by how well its tags overlap with that profile:
```
|user_tag_pool ∩ candidate_tags| / |candidate_tags|
```
First-time visitors score 0.0 here — the system degrades gracefully to pure semantic + tag matching for anonymous users.

### 4. Community Vote Score (10%)
After viewing a recommendation, users vote on how similar two movies actually feel to them: **Close / Somewhat / Different**. These map to `1.0 / 0.5 / 0.0`. The average across all voters for a given pair feeds directly into the final score, creating a self-correcting feedback loop where the crowd overrides the model when it's wrong.

### Final Formula
```
final_score = (embedding_sim × 0.50)
            + (tag_jaccard   × 0.20)
            + (user_pref     × 0.20)
            + (community_avg × 0.10)
```
Every score component is returned alongside the result — you can see exactly why a movie was recommended.

### Why This Beats Pure Embeddings
- **Embeddings alone** hallucinate similarity (two war films set in different eras look similar to the model but feel very different to viewers).
- **Tags alone** miss nuance (a film noir and a neo-noir share tags but feel different).
- **Community votes** self-correct both: if enough users mark a pair as "different", its vote score tanks and it falls off the list regardless of what the model thinks.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **API** | FastAPI + uvicorn | Async-native, auto OpenAPI docs, Pydantic validation |
| **ORM** | SQLAlchemy 2.0 async | Type-safe, async sessions, works with both SQLite and PostgreSQL |
| **Database (demo)** | SQLite + aiosqlite | Zero-config, single file, WAL mode for concurrent reads |
| **Database (prod)** | PostgreSQL + asyncpg | Drop-in swap — just change `DATABASE_URL` |
| **Embeddings** | sentence-transformers `all-MiniLM-L6-v2` | 384-dim, CPU-only, ~80 MB, ~2200 movies/batch in seconds |
| **Similarity** | numpy dot product | Replaces pgvector — works on any host, same math |
| **Auth** | JWT (python-jose) + bcrypt | Stateless tokens, refresh flow, no passlib dependency |
| **Frontend** | React 18 + TypeScript + Vite | Fast HMR, type safety end-to-end |
| **State** | Zustand + TanStack Query | Minimal auth store, server-state caching with stale-while-revalidate |
| **Styling** | Tailwind CSS | Utility-first, dark theme, no CSS files to maintain |
| **Deployment** | Cloud Run (backend) + Vercel (frontend) | Both have generous free tiers, no always-on cost |
| **Demo cache** | In-process Python dict | Avoids Redis/external state on single-instance Cloud Run |

---

## Project Structure

```
movie-recommender/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   │   ├── movie.py     # Movie + movie_tags junction table
│   │   │   ├── user.py
│   │   │   ├── review.py    # Star ratings (1–5)
│   │   │   ├── similarity_vote.py  # close/somewhat/different crowd votes
│   │   │   └── user_interaction.py # view/rate history for user prefs
│   │   ├── routers/         # FastAPI route handlers
│   │   ├── services/
│   │   │   ├── recommendation.py   # Hybrid scoring engine
│   │   │   ├── embedding.py        # sentence-transformers singleton
│   │   │   └── demo_cache.py       # In-memory TTL cache
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── db_types.py      # PortableUUID + EmbeddingType custom columns
│   │   ├── database.py      # Async engine, WAL pragmas, init_db()
│   │   └── config.py        # Settings via pydantic-settings / .env
│   ├── seed.py              # Batch-seed 2,200+ movies from CSV
│   ├── fetch_posters.py     # Fetch poster URLs from Wikipedia (no API key)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/           # HomePage, MovieDetailPage, AddMoviePage, Auth
│       ├── components/      # MovieCard, ReviewForm, SimilarityVote, TagInput
│       ├── services/api.ts  # Axios client, all API calls
│       └── store/authStore.ts  # Zustand JWT store
└── data/
    └── IMDB-Movie-Dataset(2023-1951).csv   # 2,200+ movies
```

---

## Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — defaults work out of the box for local dev

# Seed the database (downloads embedding model on first run, ~200 MB)
python seed.py

# (Optional) Fetch movie poster URLs from Wikipedia
python fetch_posters.py

# Start the API server
uvicorn app.main:app --reload
```

API is live at `http://localhost:8000`
Swagger docs at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install

# Point at local backend
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
```

Frontend is live at `http://localhost:5173`

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Get JWT access + refresh tokens |
| `POST` | `/api/auth/refresh` | Rotate access token |
| `GET` | `/api/movies` | List / search movies |
| `POST` | `/api/movies` | Add a movie |
| `GET` | `/api/movies/{id}` | Movie detail |
| `GET` | `/api/movies/{id}/recommendations` | Hybrid recommendations |
| `POST` | `/api/reviews` | Submit star rating + text review |
| `POST` | `/api/votes` | Cast community similarity vote |
| `GET` | `/api/tags` | All genre/decade tags |
| `GET` | `/health` | Server status + cache stats |

---

## Deployment

### Backend — Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/cinematch-backend backend/

# Deploy (free tier: 1 vCPU, 1 GB RAM, min 1 instance to avoid cold starts)
gcloud run deploy cinematch-backend \
  --image gcr.io/YOUR_PROJECT/cinematch-backend \
  --platform managed --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi --cpu 1 \
  --min-instances 1 \
  --set-env-vars "DEMO_MODE=true,SECRET_KEY=your-secret-here"
```

Or use the included script: `bash deploy-cloudrun.sh`

### Frontend — Vercel

```bash
cd frontend
vercel deploy

# Set environment variable in Vercel dashboard:
# VITE_API_URL = https://your-backend-url.run.app
```

---

## Environment Variables

### Backend (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./cinematch.db` | Swap to `postgresql+asyncpg://...` for production |
| `SECRET_KEY` | *(change this)* | JWT signing key — min 32 chars |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT access token lifetime |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | JSON array of allowed origins |
| `DEMO_MODE` | `false` | Enables in-memory rec + embedding cache |
| `DEMO_REC_CACHE_TTL` | `300` | Seconds before cached recommendations expire |

### Frontend (`.env.local`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL (empty string = same origin) |

---

## Seeding & Poster Data

```bash
# Seed all movies from the CSV (batch encodes all embeddings in one pass)
python seed.py

# Fetch poster images from Wikipedia (no API key required)
python fetch_posters.py

# Only process first N movies (for testing)
python fetch_posters.py --limit 50

# Re-fetch movies that already have a poster
python fetch_posters.py --overwrite
```

The seeder creates a demo user (`seeder@cinematch.demo` / `seedpass123`) that owns all seeded movies.

---

## Switching to PostgreSQL

1. Change `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/cinematch
   ```
2. For production-scale vector search, add the `pgvector` extension and swap numpy cosine similarity for `<=>` operator queries — the embedding column is already sized correctly (384 floats).
3. Run `python seed.py` to re-seed into the new database.

No code changes needed — `PortableUUID` and `EmbeddingType` are dialect-agnostic custom column types that work identically on both databases.
