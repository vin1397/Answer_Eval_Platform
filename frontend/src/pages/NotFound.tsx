import { Link } from "react-router-dom";
import { AlertTriangle } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-surface dark:bg-dark-surface px-4 text-center">
      <div className="neo-card flex h-16 w-16 items-center justify-center text-primary">
        <AlertTriangle size={28} />
      </div>
      <h1 className="text-3xl font-extrabold">404 — Page Not Found</h1>
      <p className="text-sm text-ink/60">The page you're looking for doesn't exist.</p>
      <Link to="/">
        <button className="neo-btn bg-primary text-white">Back to Home</button>
      </Link>
    </div>
  );
}
