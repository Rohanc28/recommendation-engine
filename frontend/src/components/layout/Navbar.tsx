import { Link, useNavigate } from "react-router-dom";
import { Film, Plus, LogOut, User, Sparkles } from "lucide-react";
import { useAuthStore } from "../../store/authStore";

export default function Navbar() {
  const { user, clearAuth } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold text-brand-400">
          <Film className="h-6 w-6" />
          CineMatch
        </Link>

        <div className="flex items-center gap-2">
          {user ? (
            <>
              <Link to="/add-movie" className="btn-primary text-sm">
                <Plus className="h-4 w-4" />
                Add Movie
              </Link>
              <span className="hidden items-center gap-1.5 text-sm text-gray-400 sm:flex">
                <User className="h-4 w-4" />
                {user.username}
              </span>
              <button onClick={handleLogout} className="btn-ghost text-sm">
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost text-sm">Login</Link>
              <Link to="/register" className="btn-primary text-sm">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
