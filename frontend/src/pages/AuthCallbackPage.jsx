import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Loader2, XCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function AuthCallbackPage({ onAuthenticated }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setError('Missing sign-in token.');
      return;
    }

    fetch(`${API_BASE}/auth/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || 'This link is invalid or has expired.');
        }
        return res.json();
      })
      .then((data) => {
        onAuthenticated(data.token, data.user);
        navigate('/personas');
      })
      .catch((err) => setError(err.message));
  }, [searchParams, navigate, onAuthenticated]);

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4">
      <div className="text-center">
        {error ? (
          <>
            <XCircle className="w-8 h-8 text-maroon mx-auto mb-4" />
            <p className="text-ink mb-2">{error}</p>
            <Link to="/signin" className="text-sm text-coral underline underline-offset-4">
              Request a new link
            </Link>
          </>
        ) : (
          <>
            <Loader2 className="w-6 h-6 text-coral mx-auto mb-4 animate-spin" />
            <p className="text-ink-soft text-sm">Signing you in…</p>
          </>
        )}
      </div>
    </div>
  );
}

export default AuthCallbackPage;
