import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const TREND_ICON = { Improving: TrendingUp, Declining: TrendingDown, Plateauing: Minus, Mixed: Minus };
const TREND_TONE = { Improving: 'text-sage', Declining: 'text-maroon', Plateauing: 'text-gold', Mixed: 'text-gold' };

const SCORE_BAR_TONE = (score) => {
  if (score >= 7) return 'bg-sage';
  if (score >= 4) return 'bg-gold';
  return 'bg-maroon';
};

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

function OverviewPanel({ token, user, onTabChange }) {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState(null);
  const [trend, setTrend] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/sessions`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.json())
      .then(setSessions)
      .catch(() => setSessions([]));

    fetch(`${API_BASE}/progress-report`, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'ok') setTrend(data.score_trend);
      })
      .catch(() => {});
  }, [token]);

  const completed = (sessions || []).filter((s) => s.investment_score !== null && s.investment_score !== undefined);
  const chronological = [...completed].reverse(); // API returns newest-first
  const latest = completed[0];
  const activeSession = (sessions || []).find((s) => s.status === 'active');

  return (
    <div>
      <p className="text-xs font-mono uppercase tracking-widest text-coral mb-2">01 · Overview</p>
      <h1 className="font-display text-3xl text-ink mb-1">
        {greeting()}{user?.email ? `, ${user.email.split('@')[0]}` : ''}.
      </h1>
      <p className="text-ink-soft mb-10">Here's where things stand across your sessions.</p>

      {!sessions ? (
        <p className="text-sm text-ink-soft">Loading…</p>
      ) : sessions.length === 0 ? (
        <div className="text-center py-20 bg-card border border-dashed border-border rounded-xl">
          <p className="text-ink font-display text-xl mb-2">No sessions yet</p>
          <p className="text-sm text-ink-soft mb-6 max-w-sm mx-auto">
            Submit a pitch and get cross-examined by your first partner - your dashboard fills in from there.
          </p>
          <Button onClick={() => navigate('/personas')} className="gap-1.5">
            Begin Your First Session <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      ) : (
        <div className="space-y-10">
          {/* Signature moment: the latest score, mirroring the memo's own reveal */}
          <div className="score-in border-y border-border py-8 flex flex-wrap items-end gap-x-10 gap-y-6">
            <div>
              <p className="font-display text-8xl text-ink leading-none">
                {latest?.investment_score ?? '—'}
              </p>
              <p className="text-sm text-ink-soft mt-2">
                {latest ? `Latest score · ${latest.company_name || 'Untitled Pitch'}` : 'No completed sessions yet'}
              </p>
            </div>

            {trend && (
              <div className="pb-3">
                {(() => {
                  const Icon = TREND_ICON[trend] || Minus;
                  const tone = TREND_TONE[trend] || 'text-ink-soft';
                  return (
                    <span className={`inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-widest border rounded-full px-3 py-1 ${tone} border-current`}>
                      <Icon className="w-3.5 h-3.5" /> {trend}
                    </span>
                  );
                })()}
              </div>
            )}

            {chronological.length > 1 && (
              <div className="pb-3 flex items-end gap-1.5">
                {chronological.map((s) => (
                  <div
                    key={s.session_id}
                    className={`w-2.5 rounded-sm ${SCORE_BAR_TONE(s.investment_score)}`}
                    style={{ height: `${8 + s.investment_score * 4}px` }}
                    title={`${s.company_name}: ${s.investment_score}/10`}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Stat row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <div className="bg-card border border-border rounded-lg p-4">
              <p className="font-display text-3xl text-ink">{sessions.length}</p>
              <p className="text-[11px] text-ink-soft uppercase tracking-wide mt-1">Total Sessions</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-4">
              <p className="font-display text-3xl text-ink">{user?.credits ?? 0}</p>
              <p className="text-[11px] text-ink-soft uppercase tracking-wide mt-1">Credits Remaining</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 col-span-2 sm:col-span-1">
              <p className="font-display text-3xl text-ink">{user?.free_session_used ? 'Used' : 'Available'}</p>
              <p className="text-[11px] text-ink-soft uppercase tracking-wide mt-1">Free Session</p>
            </div>
          </div>

          {/* Continue active session */}
          {activeSession && (
            <button
              onClick={() => navigate(`/sessions/${activeSession.session_id}`)}
              className="w-full text-left bg-accent border border-coral/30 rounded-lg p-5 flex items-center justify-between gap-4 hover:border-coral/60 transition-colors"
            >
              <div>
                <p className="text-xs font-mono uppercase tracking-widest text-coral mb-1">In Progress</p>
                <p className="font-display text-lg text-ink">{activeSession.company_name || 'Untitled Pitch'}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-coral flex-shrink-0" />
            </button>
          )}

          {/* Quick actions */}
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => navigate('/personas')} className="gap-1.5">
              Start New Session <ArrowRight className="w-4 h-4" />
            </Button>
            <Button variant="outline" onClick={() => onTabChange('progress')}>
              View Full Progress Report
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default OverviewPanel;
