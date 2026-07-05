import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Mail, CheckCircle2 } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function SignInPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/request-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Could not send the link.');
      }
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4 phase-in">
      <div className="w-full max-w-sm bg-card border border-border rounded-xl p-8">
        {sent ? (
          <>
            <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center mb-5">
              <CheckCircle2 className="w-4.5 h-4.5 text-sage" />
            </div>
            <h1 className="font-display text-2xl text-ink mb-1">Check your inbox</h1>
            <p className="text-sm text-ink-soft leading-relaxed">
              We sent a sign-in link to <span className="text-ink font-medium">{email}</span>.
              Click it to continue — it expires in 15 minutes.
            </p>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center mb-5">
              <Mail className="w-4.5 h-4.5 text-coral" />
            </div>
            <h1 className="font-display text-2xl text-ink mb-1">Sign in to begin</h1>
            <p className="text-sm text-ink-soft mb-6">
              Your first session is free. No password — we'll email you a link.
            </p>

            <div className="space-y-2 mb-4">
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

            {error && <p className="text-sm text-maroon mb-4">{error}</p>}

            <Button type="submit" disabled={!email || loading} className="w-full">
              {loading ? 'Sending…' : 'Send sign-in link'}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}

export default SignInPage;
