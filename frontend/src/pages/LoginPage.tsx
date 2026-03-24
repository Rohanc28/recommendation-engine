import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Film } from "lucide-react";
import { authApi } from "../services/api";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await authApi.login({ email, password });
      setAuth(data.user, data.access_token, data.refresh_token);
      navigate("/");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e?.response?.data?.detail ?? "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[80vh] items-center justify-center">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <Film className="mx-auto h-10 w-10 text-brand-400" />
          <h1 className="mt-2 text-2xl font-bold">Sign in to CineMatch</h1>
          <p className="mt-1 text-sm text-gray-400">Discover movies you'll love</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4">
          <div>
            <label className="mb-1 block text-sm text-gray-300">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="input" placeholder="you@example.com" required />
          </div>
          <div>
            <label className="mb-1 block text-sm text-gray-300">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="input" placeholder="••••••••" required />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500">
          Don't have an account?{" "}
          <Link to="/register" className="text-brand-400 hover:text-brand-300">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
