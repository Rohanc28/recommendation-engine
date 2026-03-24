import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Film } from "lucide-react";
import { moviesApi } from "../services/api";
import TagInput from "../components/tags/TagInput";
import { useAuthStore } from "../store/authStore";

export default function AddMoviePage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [form, setForm] = useState({
    title: "", description: "", year: "", poster_url: "",
  });
  const [tags, setTags] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isAuthenticated()) {
    navigate("/login");
    return null;
  }

  const set = (k: keyof typeof form) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (tags.length < 3) { setError("Add at least 3 tags"); return; }
    setError("");
    setLoading(true);
    try {
      const movie = await moviesApi.create({
        title: form.title,
        description: form.description || undefined,
        year: form.year ? parseInt(form.year, 10) : undefined,
        poster_url: form.poster_url || undefined,
        tags,
      });
      navigate(`/movies/${movie.id}`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail ?? "Failed to add movie");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Film className="h-7 w-7 text-brand-400" />
        <h1 className="text-2xl font-bold">Add a Movie</h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-5">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-300">Title *</label>
          <input value={form.title} onChange={set("title")} className="input" placeholder="Inception" required />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-300">Description</label>
          <textarea value={form.description} onChange={set("description")}
            className="input resize-none" rows={4}
            placeholder="A brief synopsis or your take on the film…" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">Year</label>
            <input type="number" value={form.year} onChange={set("year")}
              className="input" placeholder="2010" min={1888} max={2100} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">Poster URL <span className="text-gray-500 font-normal">(optional)</span></label>
            <input value={form.poster_url} onChange={set("poster_url")}
              className="input" placeholder="https://…" />
          </div>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-300">Tags * (3–5 required)</label>
          <TagInput value={tags} onChange={setTags} min={3} max={5} />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex gap-3">
          <button type="submit" disabled={loading || tags.length < 3} className="btn-primary">
            {loading ? "Adding…" : "Add Movie"}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
