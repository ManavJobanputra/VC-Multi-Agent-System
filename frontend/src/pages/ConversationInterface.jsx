import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import {
  Send, Mic, MicOff, ChevronLeft, PhoneOff,
  User, Briefcase, BarChart3, Info, Loader2,
  Download, TrendingUp, AlertTriangle,
  ShieldAlert, Lightbulb, GitMerge, Star, Users2,
} from 'lucide-react';
import { generatePDFReport } from '@/utils/reportGenerator';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function ConversationInterface({ pitch, persona, onBack, sessionId: initialSessionId, authToken }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [inputHeight, setInputHeight] = useState(52);
  const [conversationEnded, setConversationEnded] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [generatingAnalysis, setGeneratingAnalysis] = useState(false);
  const [sessionId, setSessionId] = useState(initialSessionId || null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recordingTimerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleTextareaChange = (e) => {
    const textarea = e.target;
    setInputValue(textarea.value);

    textarea.style.height = '52px';
    const scrollHeight = textarea.scrollHeight;
    const newHeight = Math.min(Math.max(scrollHeight, 52), 180);
    setInputHeight(newHeight);
    textarea.style.height = `${newHeight}px`;
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading || isRecording) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    processResponse(userMessage);
  };

  const processResponse = async (text) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({
          message: text,
          history: messages,
          pitch_context: pitch,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);

        if (data.session_id && !sessionId) {
          setSessionId(data.session_id);
        }

        if (data.conversation_ended) {
          setConversationEnded(true);
        }
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: "Sorry, something went wrong with the server response." },
        ]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "I'm having trouble connecting right now. Please check your internet." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEndCall = async () => {
    if (!window.confirm("End this session? Your partner will write the final memo from what's been said so far.")) {
      return;
    }

    setGeneratingAnalysis(true);
    try {
      const response = await fetch(`${API_BASE}/generate_analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({
          pitch_context: pitch,
          conversation_history: messages,
          session_id: sessionId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
        setConversationEnded(true);
      } else {
        alert("Failed to generate the memo. Server responded with an error.");
      }
    } catch (error) {
      console.error('Analysis error:', error);
      alert("Could not generate the memo due to a connection issue.");
    } finally {
      setGeneratingAnalysis(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.onstart = () => {
        setIsRecording(true);
        setRecordingTime(0);
        recordingTimerRef.current = setInterval(() => {
          setRecordingTime((t) => t + 1);
        }, 1000);
      };

      mediaRecorder.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        clearInterval(recordingTimerRef.current);
        setIsLoading(true);
        setTimeout(() => {
          setIsLoading(false);
        }, 1800);

        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
    } catch (err) {
      console.error('Microphone error:', err);
      alert('Could not access microphone. Please allow microphone permission.');
    }
  };

  const handleRecordingStop = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-paper text-ink font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-4 sm:px-6 py-3.5 border-b border-border bg-paper/95 backdrop-blur-lg flex-shrink-0 z-10">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="rounded-full"
          >
            <ChevronLeft className="h-5 w-5 text-ink/70" />
          </Button>

          <div>
            <h1 className="font-display text-base text-ink tracking-tight">
              {persona?.name || 'Investor'}
            </h1>
            <p className="text-xs text-ink-soft font-medium">Live Pitch Session</p>
          </div>
        </div>

        <div className="flex items-center gap-4 sm:gap-6">
          <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-sage">
            <div className="w-2 h-2 rounded-full bg-sage animate-pulse" />
            Connected
          </div>

          {!conversationEnded && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEndCall}
              disabled={generatingAnalysis || isLoading}
              className="text-maroon hover:text-maroon hover:bg-maroon/10 gap-1.5"
            >
              <PhoneOff className="h-4 w-4" />
              Close Session
            </Button>
          )}
        </div>
      </header>

      {conversationEnded && analysis ? (
        <AnalysisResults analysis={analysis} pitch={pitch} onBack={onBack} />
      ) : (
        <div className="flex flex-1 overflow-hidden max-w-[1600px] mx-auto w-full">
          {/* Main Chat */}
          <main className="flex-1 flex flex-col relative">
            <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-8 space-y-7 pb-40 lg:pb-48 custom-scrollbar">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <div className="w-14 h-14 rounded-full bg-accent flex items-center justify-center mb-5">
                    <Send className="h-6 w-6 text-coral" />
                  </div>
                  <h2 className="font-display text-2xl text-ink">Ready when you are</h2>
                  <p className="text-base text-ink-soft mt-3 max-w-lg leading-relaxed">
                    Start your pitch, ask a question, or dive straight into discussion with {persona?.name || 'the investor'}.
                  </p>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div key={idx} className={msg.role === 'user' ? 'flex justify-end' : ''}>
                  {msg.role === 'assistant' ? (
                    <div className="max-w-[85%] sm:max-w-[75%] md:max-w-[68%] border-l-2 border-coral pl-4">
                      <p className="text-[11px] font-mono uppercase tracking-widest text-coral mb-1.5">
                        {persona?.name || 'Investor'}
                      </p>
                      <p className="text-[15.5px] leading-7 whitespace-pre-wrap break-words text-ink">
                        {msg.content}
                      </p>
                    </div>
                  ) : (
                    <div className="max-w-[85%] sm:max-w-[75%] md:max-w-[68%] bg-card border border-border rounded-2xl rounded-br-sm px-5 py-3.5">
                      <p className="text-[15.5px] leading-7 whitespace-pre-wrap break-words text-ink">
                        {msg.content}
                      </p>
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="border-l-2 border-coral/40 pl-4 flex items-center gap-2.5">
                  <Loader2 className="h-4 w-4 animate-spin text-coral" />
                  <span className="text-sm text-ink-soft">{persona?.name || 'Investor'} is responding…</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Fixed Input Bar */}
            <div className="sticky bottom-0 px-4 sm:px-6 lg:px-8 pb-6 pt-4 bg-gradient-to-t from-paper via-paper/95 to-transparent">
              <form
                onSubmit={handleChatSubmit}
                className="mx-auto max-w-4xl flex items-end gap-3 bg-card border border-border shadow-sm rounded-2xl px-4 py-3 focus-within:border-coral/50 focus-within:ring-4 focus-within:ring-coral/10 transition-all"
              >
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={isRecording ? handleRecordingStop : startRecording}
                  disabled={isLoading}
                  className={`h-11 w-11 rounded-xl flex-shrink-0 ${
                    isRecording
                      ? 'bg-maroon hover:bg-maroon/90 text-white animate-pulse'
                      : 'hover:bg-accent text-coral'
                  }`}
                >
                  {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
                </Button>

                <textarea
                  ref={textareaRef}
                  value={isRecording ? `Recording • ${recordingTime}s` : inputValue}
                  onChange={handleTextareaChange}
                  disabled={isRecording || isLoading}
                  placeholder="Your message..."
                  rows={1}
                  className="flex-1 min-h-[44px] max-h-[180px] bg-transparent border-none resize-none focus-visible:ring-0 focus-visible:ring-offset-0 outline-none text-[15.5px] leading-6 placeholder:text-ink-soft/70 py-2.5"
                  style={{ height: inputHeight ? `${inputHeight}px` : undefined }}
                />

                <Button
                  type="submit"
                  disabled={!inputValue.trim() || isLoading || isRecording}
                  size="icon"
                  className="h-11 w-11 rounded-xl flex-shrink-0"
                >
                  <Send className="h-4.5 w-4.5" />
                </Button>
              </form>
            </div>
          </main>

          {/* Sidebar */}
          <aside className="hidden lg:flex w-72 flex-col bg-paper-dim border-l border-border overflow-y-auto">
            <div className="p-6 space-y-8">
              <div className="space-y-5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-ink-soft flex items-center gap-2">
                  <Info className="h-4 w-4" /> Session Context
                </h3>

                <div className="space-y-5">
                  <div className="flex items-start gap-3">
                    <User className="h-4.5 w-4.5 text-coral mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-ink-soft font-medium">Partner</p>
                      <p className="text-sm font-semibold text-ink">
                        {persona?.name || 'Investor'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Briefcase className="h-4.5 w-4.5 text-coral mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-ink-soft font-medium">Company</p>
                      <p className="text-sm font-semibold text-ink">
                        {pitch?.companyName || pitch?.company_name || 'Not specified'}
                      </p>
                      {pitch?.industry && (
                        <p className="text-xs text-ink-soft mt-0.5">{pitch.industry}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <BarChart3 className="h-4.5 w-4.5 text-coral mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-ink-soft font-medium">Stage</p>
                      <p className="text-sm font-semibold text-ink">
                        {pitch?.currentStage || pitch?.stage || 'Not specified'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-5 border-t border-border">
                <p className="text-xs text-ink-soft leading-relaxed">
                  Session data is stored only to run this evaluation and is not shared outside this session.
                </p>
              </div>

              <div className="pt-6 text-xs text-ink-soft/70 text-center border-t border-border">
                VC Pitch Analyzer
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

// Tailwind statically scans for literal class strings, so color variants
// must be spelled out in full here rather than interpolated at runtime
// (e.g. `text-${tone}` never generates any CSS).
const TONE_CLASSES = {
  sage: { text: 'text-sage', border: 'border-sage', borderL: 'border-l-sage', bg: 'bg-sage' },
  gold: { text: 'text-gold', border: 'border-gold', borderL: 'border-l-gold', bg: 'bg-gold' },
  maroon: { text: 'text-maroon', border: 'border-maroon', borderL: 'border-l-maroon', bg: 'bg-maroon' },
  coral: { text: 'text-coral', border: 'border-coral', borderL: 'border-l-coral', bg: 'bg-coral' },
  'ink-soft': { text: 'text-ink-soft', border: 'border-ink-soft', borderL: 'border-l-ink-soft', bg: 'bg-ink-soft' },
};

function verdictFromScore(score) {
  if (score === undefined || score === null) return { label: 'Pending', tone: 'ink-soft' };
  if (score >= 7) return { label: 'Invest', tone: 'sage' };
  if (score >= 4) return { label: 'Watch', tone: 'gold' };
  return { label: 'Pass', tone: 'maroon' };
}

const SEVERITY_TONE = { High: 'maroon', Medium: 'gold', Low: 'sage' };

function severityOf(value) {
  if (value && typeof value === 'object') return value.severity || 'Medium';
  const v = String(value || '').toLowerCase();
  return v.includes('high') ? 'High' : v.includes('low') ? 'Low' : 'Medium';
}

function AnalysisResults({ analysis, pitch, onBack }) {
  const analysisData = analysis?.analysis || {};
  const score = analysisData.investment_score;
  const recommendation = analysisData.recommendation;
  const DECISION_TONE = { Pass: 'maroon', Watch: 'gold', Follow: 'sage', Lead: 'sage' };
  const verdict = recommendation?.decision && DECISION_TONE[recommendation.decision]
    ? { label: recommendation.decision, tone: DECISION_TONE[recommendation.decision] }
    : verdictFromScore(score);

  const contradictions = analysisData.contradictions || [];
  const agentAssessment = analysisData.agent_assessment || {};
  const answerQuality = analysisData.answer_quality || [];

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8 lg:p-10 space-y-12 max-w-5xl mx-auto w-full relative">
      <div className="margin-marks margin-marks-left" data-label="Investment Memo" />
      <div className="margin-marks margin-marks-right" data-label="Step 03 of 03" />

      {/* Header */}
      <div className="space-y-2">
        <p className="text-xs font-mono uppercase tracking-widest text-coral">Investment Memo</p>
        <h1 className="font-display text-4xl text-ink tracking-tight">
          {pitch?.companyName || pitch?.company_name || 'Your Pitch'}
        </h1>
        <p className="text-ink-soft">
          {pitch?.industry || 'Startup'} · {pitch?.stage || pitch?.currentStage || 'Stage not specified'}
        </p>
      </div>

      {/* Score - the one bold moment */}
      {score !== undefined && (
        <div className="score-in flex items-end gap-8 border-y border-border py-8">
          <div>
            <p className="font-display text-8xl text-ink leading-none">{score}</p>
            <p className="text-sm text-ink-soft mt-2">out of 10</p>
          </div>
          <div className="pb-3">
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-mono uppercase tracking-widest border ${TONE_CLASSES[verdict.tone].text} ${TONE_CLASSES[verdict.tone].border}`}>
              {verdict.label}
            </span>
            <p className="text-ink text-lg leading-relaxed mt-4 max-w-lg font-display italic">
              {analysisData.overall_verdict || 'Processing evaluation...'}
            </p>
          </div>
        </div>
      )}

      {/* Investment Thesis - the executive summary a partner reads aloud */}
      {analysisData.investment_thesis && (
        <div className="bg-paper-dim border-l-4 border-l-coral rounded-r-lg p-6">
          <p className="text-xs font-mono uppercase tracking-widest text-coral mb-3">Investment Thesis</p>
          <p className="text-ink text-lg leading-relaxed font-display">{analysisData.investment_thesis}</p>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Strengths" value={analysisData.pros?.length || 0} icon={TrendingUp} tone="sage" />
        <StatCard label="Concerns" value={analysisData.cons?.length || 0} icon={AlertTriangle} tone="maroon" />
        <StatCard label="Contradictions" value={contradictions.length} icon={GitMerge} tone="gold" />
        <StatCard label="Risk Areas" value={analysisData.risk_assessment ? Object.keys(analysisData.risk_assessment).length : 0} icon={ShieldAlert} tone="coral" />
      </div>

      {/* Numbered memo sections - a real investment memo IS a fixed sequence */}
      {contradictions.length > 0 && (
        <div className="space-y-5">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-coral">1</span>
            <h2 className="font-display text-2xl text-ink">Contradictions Raised &amp; Resolved</h2>
          </div>
          <p className="text-sm text-ink-soft -mt-2">
            The single most important signal from a live diligence session - not what was said, but what was
            questioned and whether the founder could reconcile it.
          </p>
          <div className="space-y-3">
            {contradictions.map((c, idx) => (
              <div
                key={idx}
                className={`p-5 rounded-lg bg-card border border-border border-l-4 ${c.resolved ? TONE_CLASSES.sage.borderL : TONE_CLASSES.maroon.borderL}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-ink">{c.topic}</h3>
                  <span className={`text-[10px] font-mono uppercase tracking-widest ${c.resolved ? TONE_CLASSES.sage.text : TONE_CLASSES.maroon.text}`}>
                    {c.resolved ? 'Resolved' : 'Unresolved'}
                  </span>
                </div>
                <p className="text-sm text-ink-soft leading-relaxed mb-2">
                  <span className="text-ink/70 font-medium">Raised: </span>{c.concern_raised}
                </p>
                <p className="text-sm text-ink-soft leading-relaxed">
                  <span className="text-ink/70 font-medium">{c.resolved ? 'Resolution: ' : 'Status: '}</span>{c.resolution}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <MemoSection number="2" title="Key Strengths" items={analysisData.pros} tone="sage" />
      <MemoSection number="3" title="Major Concerns" items={analysisData.cons} tone="maroon" />
      <MemoSection number="4" title="What's Working" items={analysisData.good_parts} tone="sage" />
      <MemoSection number="5" title="Needs Improvement" items={analysisData.bad_parts} tone="gold" />

      {/* Risk Assessment - severity + the evidence it's grounded in + confidence */}
      {analysisData.risk_assessment && (
        <div className="space-y-5">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-coral">6</span>
            <h2 className="font-display text-2xl text-ink">Risk Assessment</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(analysisData.risk_assessment).map(([key, value]) => {
              const severity = severityOf(value);
              const tone = SEVERITY_TONE[severity];
              const reasoning = value && typeof value === 'object' ? value.reasoning : String(value);
              const confidence = value && typeof value === 'object' ? value.confidence : null;

              return (
                <div key={key} className={`p-5 rounded-lg border border-border bg-card border-l-4 ${TONE_CLASSES[tone].borderL}`}>
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-ink capitalize">{key.replace(/_/g, ' ')}</h3>
                    <span className={`text-[10px] font-mono uppercase tracking-widest ${TONE_CLASSES[tone].text}`}>
                      {severity}
                    </span>
                  </div>
                  <p className="text-sm text-ink-soft leading-relaxed mb-3">{reasoning}</p>
                  {confidence !== null && <ConfidenceBar value={confidence} tone={tone} />}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Specialist agent scores - where the panel disagrees */}
      {Object.keys(agentAssessment).length > 0 && (
        <div className="space-y-5">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-coral">7</span>
            <h2 className="font-display text-2xl text-ink">Specialist Panel Read</h2>
          </div>
          <p className="text-sm text-ink-soft -mt-2 flex items-center gap-1.5">
            <Users2 className="w-3.5 h-3.5" /> One merged verdict hides where the panel actually disagreed.
          </p>
          <div className="space-y-3">
            {Object.entries(agentAssessment).map(([key, agent]) => (
              <div key={key} className="p-4 rounded-lg bg-card border border-border">
                <div className="flex items-center justify-between mb-1.5">
                  <h3 className="font-medium text-ink text-sm capitalize">{key.replace(/_/g, ' ')}</h3>
                  <span className="font-display text-xl text-ink">{agent.score}<span className="text-xs text-ink-soft">/10</span></span>
                </div>
                <p className="text-sm text-ink-soft leading-relaxed mb-2">{agent.summary}</p>
                {agent.confidence !== undefined && <ConfidenceBar value={agent.confidence} tone="coral" />}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Answer-by-answer quality */}
      {answerQuality.length > 0 && (
        <div className="space-y-5">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-coral">8</span>
            <h2 className="font-display text-2xl text-ink">Answer-by-Answer Quality</h2>
          </div>
          <div className="space-y-2">
            {answerQuality.map((qa, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-card border border-border">
                <div className="flex items-start justify-between gap-4 mb-1">
                  <p className="text-sm text-ink font-medium leading-relaxed">{qa.question}</p>
                  <div className="flex gap-0.5 flex-shrink-0 pt-0.5">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Star
                        key={n}
                        className={`w-3.5 h-3.5 ${n <= (qa.rating || 0) ? 'text-coral fill-coral' : 'text-border fill-border'}`}
                      />
                    ))}
                  </div>
                </div>
                <p className="text-sm text-ink-soft leading-relaxed">{qa.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendation - the reasoning a partner would actually want */}
      {recommendation && (
        <div className="space-y-5">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-sm text-coral">9</span>
            <h2 className="font-display text-2xl text-ink">Recommendation</h2>
          </div>
          <div className="flex items-center gap-4 mb-2">
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-mono uppercase tracking-widest border ${TONE_CLASSES[verdict.tone].text} ${TONE_CLASSES[verdict.tone].border}`}>
              {recommendation.decision}
            </span>
            {recommendation.confidence !== undefined && (
              <span className="text-xs text-ink-soft">Confidence: {recommendation.confidence}%</span>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <RecommendationList title="Reasons to Invest" items={recommendation.reasons_to_invest} tone="sage" />
            <RecommendationList title="Reasons Not to Invest" items={recommendation.reasons_not_to_invest} tone="maroon" />
          </div>
          <RecommendationList title="Open Questions" items={recommendation.open_questions} tone="gold" fullWidth />
        </div>
      )}

      <MemoSection number="10" title="Next Steps" items={analysisData.recommendations} tone="coral" />

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3 pt-6 border-t border-border">
        <Button onClick={onBack} variant="outline" className="flex-1 h-12">
          Back to Dashboard
        </Button>
        <Button
          className="flex-1 h-12"
          onClick={() => generatePDFReport(analysisData, pitch)}
        >
          <Download className="w-4 h-4" />
          Download Full Memo
        </Button>
      </div>
    </div>
  );
}

function ConfidenceBar({ value, tone }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-ink-soft uppercase tracking-wide">Confidence</span>
        <span className="text-[10px] text-ink-soft font-mono">{value}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-paper-dim overflow-hidden">
        <div
          className={`h-full rounded-full ${TONE_CLASSES[tone].bg}`}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}

function RecommendationList({ title, items, tone, fullWidth }) {
  if (!items || items.length === 0) return null;
  return (
    <div className={fullWidth ? 'md:col-span-2' : ''}>
      <p className={`text-xs font-mono uppercase tracking-widest mb-2 ${TONE_CLASSES[tone].text}`}>{title}</p>
      <ul className="space-y-1.5">
        {items.map((item, idx) => (
          <li key={idx} className="text-sm text-ink-soft leading-relaxed pl-4 relative before:content-['—'] before:absolute before:left-0 before:text-ink-soft/50">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, tone }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <Icon className={`w-4 h-4 mb-2 ${TONE_CLASSES[tone].text}`} strokeWidth={1.75} />
      <div className="font-display text-3xl text-ink">{value}</div>
      <div className="text-[11px] text-ink-soft uppercase tracking-wide mt-1">{label}</div>
    </div>
  );
}

function MemoSection({ number, title, items, tone }) {
  if (!items) return null;
  return (
    <div className="space-y-5">
      <div className="flex items-baseline gap-3">
        <span className="font-mono text-sm text-coral">{number}</span>
        <h2 className="font-display text-2xl text-ink">{title}</h2>
      </div>
      <div className="space-y-3">
        {Array.isArray(items) && items.length > 0 ? (
          items.map((item, idx) => (
            <div key={idx} className={`p-4 rounded-lg bg-card border border-border border-l-4 ${TONE_CLASSES[tone].borderL}`}>
              <p className="text-ink/85 leading-relaxed text-sm">{item}</p>
            </div>
          ))
        ) : (
          <div className="p-4 rounded-lg border border-dashed border-border text-ink-soft italic text-sm">
            No data available in this category.
          </div>
        )}
      </div>
    </div>
  );
}

export { AnalysisResults };
export default ConversationInterface;
