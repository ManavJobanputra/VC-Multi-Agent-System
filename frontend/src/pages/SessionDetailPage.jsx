import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ChevronLeft } from 'lucide-react';
import { AnalysisResults } from './ConversationInterface';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function Transcript({ messages, personaName }) {
  if (!messages || messages.length === 0) {
    return <p className="text-sm text-ink-soft italic">No messages recorded for this session.</p>;
  }

  return (
    <div className="space-y-7">
      {messages.map((msg, idx) => (
        <div key={idx} className={msg.role === 'user' ? 'flex justify-end' : ''}>
          {msg.role === 'assistant' ? (
            <div className="max-w-[85%] sm:max-w-[75%] border-l-2 border-coral pl-4">
              <p className="text-[11px] font-mono uppercase tracking-widest text-coral mb-1.5">
                {personaName || 'Investor'}
              </p>
              <p className="text-[15px] leading-7 whitespace-pre-wrap break-words text-ink">{msg.content}</p>
            </div>
          ) : (
            <div className="max-w-[85%] sm:max-w-[75%] bg-card border border-border rounded-2xl rounded-br-sm px-5 py-3.5">
              <p className="text-[15px] leading-7 whitespace-pre-wrap break-words text-ink">{msg.content}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function SessionDetailPage({ token }) {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [error, setError] = useState(null);
  const [view, setView] = useState('memo'); // 'memo' | 'transcript'

  useEffect(() => {
    if (!token) {
      navigate('/signin');
      return;
    }
    fetch(`${API_BASE}/sessions/${sessionId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (res) => {
        if (res.status === 404) throw new Error("This session doesn't exist or isn't yours.");
        if (!res.ok) throw new Error('Could not load this session.');
        return res.json();
      })
      .then((data) => {
        setSession(data);
        setView(data.analysis ? 'memo' : 'transcript');
      })
      .catch((err) => setError(err.message));
  }, [sessionId, token, navigate]);

  if (error) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-ink mb-4">{error}</p>
          <Button variant="outline" onClick={() => navigate('/sessions')}>Back to Sessions</Button>
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <p className="text-sm text-ink-soft">Loading…</p>
      </div>
    );
  }

  if (view === 'memo' && session.analysis) {
    return (
      <div className="min-h-screen bg-paper phase-in flex flex-col">
        <div className="border-b border-border">
          <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
            <Button variant="ghost" size="sm" onClick={() => navigate('/sessions')} className="gap-1.5">
              <ChevronLeft className="h-4 w-4" /> All Sessions
            </Button>
            <Button variant="outline" size="sm" onClick={() => setView('transcript')}>
              View Transcript
            </Button>
          </div>
        </div>
        <AnalysisResults
          analysis={{ analysis: session.analysis }}
          pitch={session.pitch_data}
          onBack={() => setView('transcript')}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper phase-in">
      <div className="border-b border-border">
        <div className="max-w-3xl mx-auto px-6 py-5 flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => navigate('/sessions')} className="gap-1.5">
            <ChevronLeft className="h-4 w-4" /> All Sessions
          </Button>
          {session.analysis && (
            <Button variant="outline" size="sm" onClick={() => setView('memo')}>
              View Memo
            </Button>
          )}
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10">
        <p className="text-xs font-mono uppercase tracking-widest text-coral mb-2">Transcript</p>
        <h1 className="font-display text-3xl text-ink mb-1">{session.company_name || 'Untitled Pitch'}</h1>
        <p className="text-ink-soft mb-10">
          {session.industry || 'Industry n/a'} · {session.stage || 'Stage n/a'} · {session.persona_name || 'No partner'}
        </p>
        <Transcript messages={session.messages} personaName={session.persona_name} />
      </div>
    </div>
  );
}

export default SessionDetailPage;
