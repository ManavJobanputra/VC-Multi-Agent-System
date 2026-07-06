import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Mail } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function SignInPage({ onAuthenticated }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/signup';
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Something went wrong.');
      }
      onAuthenticated(data.token, data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4 phase-in">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-card border border-border rounded-xl p-8">
        <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center mb-5">
          <Mail className="w-4.5 h-4.5 text-coral" />
        </div>
        <h1 className="font-display text-2xl text-ink mb-1">
          {mode === 'login' ? 'Log in' : 'Create your account'}
        </h1>
        <p className="text-sm text-ink-soft mb-6">
          {mode === 'login'
            ? "Don't have an account yet? Your first session is free."
            : 'Your first session is free once you sign up.'}
        </p>

        <div className="space-y-4 mb-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'signup' ? 'At least 8 characters' : '••••••••'}
            />
          </div>
        </div>

        {error && <p className="text-sm text-maroon mb-4">{error}</p>}

        <Button type="submit" disabled={!email || !password || loading} className="w-full mb-4">
          {loading ? 'Please wait…' : mode === 'login' ? 'Log In' : 'Sign Up'}
        </Button>

        <button
          type="button"
          onClick={() => {
            setMode(mode === 'login' ? 'signup' : 'login');
            setError(null);
          }}
          className="w-full text-center text-sm text-ink-soft hover:text-ink underline underline-offset-4"
        >
          {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
        </button>
      </form>
    </div>
  );
}

export default SignInPage;
