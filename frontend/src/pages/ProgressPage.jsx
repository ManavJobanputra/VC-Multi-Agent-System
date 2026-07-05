import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ChevronLeft, TrendingUp, TrendingDown, Minus, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const TREND_ICON = { Improving: TrendingUp, Declining: TrendingDown, Plateauing: Minus, Mixed: Minus };
const TREND_TONE = { Improving: 'text-sage', Declining: 'text-maroon', Plateauing: 'text-gold', Mixed: 'text-gold' };

const STATUS_ICON = { Addressed: CheckCircle2, 'Partially Addressed': AlertCircle, Ignored: XCircle };
const STATUS_TONE = { Addressed: 'text-sage', 'Partially Addressed': 'text-gold', Ignored: 'text-maroon' };

const SEVERITY_CLASSES = {
  High: { text: 'text-maroon', borderL: 'border-l-maroon' },
  Medium: { text: 'text-gold', borderL: 'border-l-gold' },
  Low: { text: 'text-sage', borderL: 'border-l-sage' },
};
const DEFAULT_SEVERITY = { text: 'text-ink-soft', borderL: 'border-l-ink-soft' };

function ProgressPage({ token }) {
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate('/signin');
      return;
    }
    fetch(`${API_BASE}/progress-report`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Could not load your progress report.');
        return res.json();
      })
      .then(setReport)
      .catch((err) => setError(err.message));
  }, [token, navigate]);

  return (
    <div className="min-h-screen bg-paper phase-in">
      <div className="border-b border-border">
        <div className="max-w-4xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate('/sessions')}>
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="font-display text-xl text-ink tracking-tight">Your Progress</h1>
              <p className="text-xs font-mono uppercase tracking-widest text-ink-soft">Across Every Session</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-10">
        {error && <p className="text-sm text-maroon">{error}</p>}
        {!report && !error && <p className="text-sm text-ink-soft">Analyzing your session history…</p>}

        {report?.status === 'insufficient_data' && (
          <div className="text-center py-20">
            <p className="text-ink font-display text-xl mb-2">Not enough sessions yet</p>
            <p className="text-sm text-ink-soft mb-6">{report.message}</p>
            <Button onClick={() => navigate('/personas')}>Start a Session</Button>
          </div>
        )}

        {report?.status === 'error' && (
          <p className="text-sm text-maroon">{report.message}</p>
        )}

        {report?.status === 'ok' && (
          <div className="space-y-12">
            <div className="space-y-2">
              <p className="text-xs font-mono uppercase tracking-widest text-coral">
                {report.sessions_analyzed} Sessions Analyzed
              </p>
              <div className="flex items-center gap-3">
                {(() => {
                  const Icon = TREND_ICON[report.score_trend] || Minus;
                  const tone = TREND_TONE[report.score_trend] || 'text-ink-soft';
                  return (
                    <span className={`inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-widest border rounded-full px-3 py-1 ${tone} border-current`}>
                      <Icon className="w-3.5 h-3.5" /> {report.score_trend}
                    </span>
                  );
                })()}
              </div>
              <p className="text-ink text-lg leading-relaxed font-display mt-3">{report.trajectory_summary}</p>
            </div>

            {/* Improvements */}
            <div className="space-y-5">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-sm text-coral">1</span>
                <h2 className="font-display text-2xl text-ink">What's Improved</h2>
              </div>
              {report.improvements?.length > 0 ? (
                <div className="space-y-3">
                  {report.improvements.map((item, idx) => (
                    <div key={idx} className="p-5 rounded-lg bg-card border border-border border-l-4 border-l-sage">
                      <h3 className="font-semibold text-ink mb-1">{item.area}</h3>
                      <p className="text-sm text-ink-soft leading-relaxed mb-2">{item.evidence}</p>
                      <p className="text-[10px] font-mono uppercase tracking-widest text-ink-soft">
                        Sessions {item.sessions_involved?.join(', ')}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink-soft italic">No clear improvement identified yet.</p>
              )}
            </div>

            {/* Feedback Incorporation */}
            <div className="space-y-5">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-sm text-coral">2</span>
                <h2 className="font-display text-2xl text-ink">Did You Act On Past Feedback?</h2>
              </div>
              {report.feedback_incorporation?.length > 0 ? (
                <div className="space-y-3">
                  {report.feedback_incorporation.map((item, idx) => {
                    const Icon = STATUS_ICON[item.status] || AlertCircle;
                    const tone = STATUS_TONE[item.status] || 'text-ink-soft';
                    return (
                      <div key={idx} className="p-5 rounded-lg bg-card border border-border">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <p className="text-sm text-ink font-medium leading-relaxed">{item.recommendation}</p>
                          <span className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-widest flex-shrink-0 ${tone}`}>
                            <Icon className="w-3.5 h-3.5" /> {item.status}
                          </span>
                        </div>
                        <p className="text-sm text-ink-soft leading-relaxed">{item.evidence}</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-ink-soft italic">No prior recommendations to check yet.</p>
              )}
            </div>

            {/* Consistent Weaknesses */}
            <div className="space-y-5">
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-sm text-coral">3</span>
                <h2 className="font-display text-2xl text-ink">Consistent Weaknesses</h2>
              </div>
              {report.consistent_weaknesses?.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {report.consistent_weaknesses.map((item, idx) => {
                    const severity = SEVERITY_CLASSES[item.severity] || DEFAULT_SEVERITY;
                    return (
                      <div key={idx} className={`p-5 rounded-lg border border-border bg-card border-l-4 ${severity.borderL}`}>
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-ink">{item.weakness}</h3>
                          <span className={`text-[10px] font-mono uppercase tracking-widest flex-shrink-0 ${severity.text}`}>
                            {item.severity}
                          </span>
                        </div>
                        <p className="text-sm text-ink-soft leading-relaxed">{item.frequency}</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-ink-soft italic">No recurring weaknesses identified.</p>
              )}
            </div>

            {/* Consistent Strengths */}
            {report.consistent_strengths?.length > 0 && (
              <div className="space-y-5">
                <div className="flex items-baseline gap-3">
                  <span className="font-mono text-sm text-coral">4</span>
                  <h2 className="font-display text-2xl text-ink">Consistent Strengths</h2>
                </div>
                <div className="space-y-3">
                  {report.consistent_strengths.map((item, idx) => (
                    <div key={idx} className="p-4 rounded-lg bg-card border border-border border-l-4 border-l-sage">
                      <p className="text-ink/85 leading-relaxed text-sm">{item.strength}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Overall Assessment */}
            <div className="bg-paper-dim border-l-4 border-l-coral rounded-r-lg p-6">
              <p className="text-xs font-mono uppercase tracking-widest text-coral mb-3">Bottom Line</p>
              <p className="text-ink text-lg leading-relaxed font-display">{report.overall_assessment}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProgressPage;
