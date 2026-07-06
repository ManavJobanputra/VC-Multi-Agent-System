import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const SCORE_TONE = (score) => {
  if (score === null || score === undefined) return 'text-ink-soft';
  if (score >= 7) return 'text-sage';
  if (score >= 4) return 'text-gold';
  return 'text-maroon';
};

function SessionsPanel({ token }) {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/sessions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Could not load your sessions.');
        return res.json();
      })
      .then(setSessions)
      .catch((err) => setError(err.message));
  }, [token]);

  return (
    <div>
      <p className="text-xs font-mono uppercase tracking-widest text-coral mb-2">02 · Sessions</p>
      <h1 className="font-display text-3xl text-ink mb-8">Every Diligence Round</h1>

      {error && <p className="text-sm text-maroon">{error}</p>}
      {!sessions && !error && <p className="text-sm text-ink-soft">Loading…</p>}

      {sessions && sessions.length === 0 && (
        <div className="text-center py-20 bg-card border border-dashed border-border rounded-xl">
          <Inbox className="w-8 h-8 text-ink-soft mx-auto mb-4" strokeWidth={1.5} />
          <p className="text-ink font-display text-xl mb-1">No sessions yet</p>
          <p className="text-sm text-ink-soft mb-6">Submit a pitch to start your first diligence session.</p>
          <Button onClick={() => navigate('/personas')}>Begin Diligence</Button>
        </div>
      )}

      {sessions && sessions.length > 0 && (
        <div className="space-y-3">
          {sessions.map((s) => (
            <button
              key={s.session_id}
              onClick={() => navigate(`/sessions/${s.session_id}`)}
              className="w-full text-left bg-card border border-border rounded-lg p-5 flex items-center justify-between gap-4 hover:border-coral/40 transition-colors"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-display text-lg text-ink truncate">{s.company_name || 'Untitled Pitch'}</h3>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-ink-soft border border-border rounded-full px-2 py-0.5 flex-shrink-0">
                    {s.status}
                  </span>
                </div>
                <p className="text-xs text-ink-soft">
                  {s.industry || 'Industry n/a'} · {s.stage || 'Stage n/a'} · {s.persona_name || 'No partner'} ·{' '}
                  {new Date(s.created_at.replace(' ', 'T') + 'Z').toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                </p>
              </div>
              <div className="flex items-center gap-3 flex-shrink-0">
                {s.investment_score !== null && s.investment_score !== undefined && (
                  <span className={`font-display text-2xl ${SCORE_TONE(s.investment_score)}`}>{s.investment_score}</span>
                )}
                <ChevronRight className="w-4 h-4 text-ink-soft" />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default SessionsPanel;
export { SCORE_TONE };
