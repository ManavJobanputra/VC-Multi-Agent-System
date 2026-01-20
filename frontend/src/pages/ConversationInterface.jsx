import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import {
  Send, Mic, MicOff, ChevronLeft, PhoneOff,
  User, Briefcase, BarChart3, Info, Loader2,
  Lock, Database, CheckCircle2, Download
} from 'lucide-react';
import { generatePDFReport } from '@/utils/reportGenerator';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function ConversationInterface({ pitch, persona, onBack, sessionId: initialSessionId }) {
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
        headers: { 'Content-Type': 'application/json' },
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

        // Store session ID for this conversation
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
    if (!window.confirm("Are you sure you want to end this session? Analysis will be generated.")) {
      return;
    }

    setGeneratingAnalysis(true);
    try {
      const response = await fetch(`${API_BASE}/generate_analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pitch_context: pitch,
          conversation_history: messages,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
        setConversationEnded(true);
      } else {
        alert("Failed to generate analysis. Server responded with error.");
      }
    } catch (error) {
      console.error('Analysis error:', error);
      alert("Could not generate analysis due to a connection issue.");
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
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
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
    <div className="flex flex-col h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-4 sm:px-6 py-3.5 border-b border-slate-200/60 bg-white/85 backdrop-blur-lg flex-shrink-0 z-10">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="rounded-full hover:bg-slate-100"
          >
            <ChevronLeft className="h-5 w-5 text-slate-700" />
          </Button>

          <div>
            <h1 className="text-base font-semibold tracking-tight">
              {persona?.name || 'Investor'}
            </h1>
            <p className="text-xs text-slate-500 font-medium">Live Pitch Session</p>
          </div>
        </div>

        <div className="flex items-center gap-4 sm:gap-6">
          <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-emerald-600">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            Connected
          </div>

          {!conversationEnded && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEndCall}
              disabled={generatingAnalysis || isLoading}
              className={`
                text-red-600 hover:text-red-700 hover:bg-red-50/80
                gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                transition-colors
                disabled:opacity-50 disabled:pointer-events-none
              `}
            >
              <PhoneOff className="h-4 w-4" />
              End Call
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
            <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-40 lg:pb-48 custom-scrollbar">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center opacity-80">
                  <div className="p-6 rounded-3xl bg-indigo-100/60 mb-6 shadow-sm">
                    <Send className="h-10 w-10 text-indigo-600" />
                  </div>
                  <h2 className="text-2xl font-medium text-slate-800">Ready when you are</h2>
                  <p className="text-base text-slate-600 mt-3 max-w-lg leading-relaxed">
                    Start your pitch, ask a question, or dive straight into discussion with {persona?.name || 'the investor'}.
                  </p>
                </div>
              )}

              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`
                      max-w-[85%] sm:max-w-[75%] md:max-w-[68%]
                      px-6 py-4 rounded-2xl shadow-sm
                      ${msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-none shadow-indigo-500/30'
                        : 'bg-white border border-slate-200/70 rounded-bl-none shadow-slate-200/30'
                      }
                    `}
                  >
                    <p className="text-[15.5px] leading-7 whitespace-pre-wrap break-words">
                      {msg.content}
                    </p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-200/70 px-6 py-4 rounded-2xl rounded-bl-none shadow-sm flex items-center gap-3 animate-pulse">
                    <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
                    <span className="text-sm text-slate-600">Thinking...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Fixed Input Bar – now with more structure */}
            <div className="sticky bottom-0 px-4 sm:px-6 lg:px-8 pb-6 pt-4 bg-gradient-to-t from-white via-white/95 to-transparent">
              <form
                onSubmit={handleChatSubmit}
                className={`
                  mx-auto max-w-4xl
                  flex items-end gap-3 sm:gap-4
                  bg-white/95 backdrop-blur-xl
                  border border-slate-300/70 shadow-xl shadow-slate-200/20
                  rounded-3xl px-5 py-3.5
                  focus-within:border-indigo-400/60 focus-within:ring-4 focus-within:ring-indigo-100/40
                  transition-all duration-200
                `}
              >
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={isRecording ? handleRecordingStop : startRecording}
                  disabled={isLoading}
                  className={`
                    h-12 w-12 rounded-2xl flex-shrink-0 transition-all
                    ${isRecording
                      ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                      : 'hover:bg-indigo-50/70 text-indigo-600'
                    }
                  `}
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
                  className={`
                    flex-1 min-h-[48px] max-h-[180px]
                    bg-transparent border-none resize-none
                    focus-visible:ring-0 focus-visible:ring-offset-0
                    text-[15.5px] leading-6 placeholder:text-slate-500/70
                    py-3 pr-3
                    scrollbar-thin scrollbar-thumb-slate-300/60
                  `}
                  style={{ height: inputHeight ? `${inputHeight}px` : undefined }}
                />

                <Button
                  type="submit"
                  disabled={!inputValue.trim() || isLoading || isRecording}
                  className={`
                    h-12 px-6 min-w-[100px]
                    bg-gradient-to-r from-indigo-600 to-indigo-500
                    hover:from-indigo-700 hover:to-indigo-600
                    rounded-2xl text-white shadow-lg shadow-indigo-500/30
                    disabled:opacity-50 disabled:cursor-not-allowed
                    transition-all duration-200
                    flex items-center justify-center gap-2
                  `}
                >
                  <Send className="h-4.5 w-4.5" />
                  <span className="hidden sm:inline text-sm font-medium">Send</span>
                </Button>
              </form>
            </div>
          </main>

          {/* Sidebar */}
          <aside className="hidden lg:flex w-72 flex-col bg-white/75 backdrop-blur-md border-l border-slate-200/60 overflow-y-auto">
            <div className="p-6 space-y-8">
              <div className="space-y-5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                  <Info className="h-4 w-4" /> Session Context
                </h3>

                <div className="space-y-5">
                  <div className="flex items-start gap-3">
                    <User className="h-5 w-5 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Persona</p>
                      <p className="text-sm font-semibold text-slate-900">
                        {persona?.name || 'Investor'}
                      </p>
                      {persona?.role && (
                        <p className="text-xs text-slate-600 mt-0.5">{persona.role}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Briefcase className="h-5 w-5 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Company</p>
                      <p className="text-sm font-semibold text-slate-900">
                        {pitch?.company_name || 'Not specified'}
                      </p>
                      {pitch?.industry && (
                        <p className="text-xs text-slate-600 mt-0.5">{pitch.industry}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <BarChart3 className="h-5 w-5 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-slate-500 font-medium">Stage</p>
                      <p className="text-sm font-semibold text-slate-900">
                        {pitch?.stage || 'Not specified'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-5 border-t border-slate-200/60 space-y-5">
                <div className="flex items-center gap-2.5 text-sm font-medium text-emerald-700">
                  <Lock className="h-4 w-4" />
                  Session Secure
                </div>

                <div className="flex items-center gap-2.5 text-sm font-medium text-emerald-700">
                  <CheckCircle2 className="h-4 w-4" />
                  End-to-end encrypted
                </div>

                <div className="flex items-center gap-2.5 text-xs text-slate-600">
                  <Database className="h-4 w-4" />
                  Real-time investor profile sync
                </div>

                {pitch?.valuation && (
                  <div className="text-xs text-slate-600">
                    Last known valuation:{' '}
                    <span className="font-medium text-slate-800">{pitch.valuation}</span>
                  </div>
                )}

                {pitch?.location && (
                  <div className="text-xs text-slate-600">
                    Location:{' '}
                    <span className="font-medium text-slate-800">{pitch.location}</span>
                  </div>
                )}
              </div>

              <div className="pt-6 text-xs text-slate-500 text-center border-t border-slate-200/40">
                Powered by YourPitch AI • Data protected • © 2026
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

function AnalysisResults({ analysis, pitch, onBack }) {
  const analysisData = analysis?.analysis || {};
  
  console.log('AnalysisResults - Full analysis:', analysis);
  console.log('AnalysisResults - Extracted analysisData:', analysisData);
  console.log('AnalysisResults - Pitch data:', pitch);

  return (
    <div className="flex-1 overflow-y-auto p-6 sm:p-8 lg:p-10 space-y-10 max-w-5xl mx-auto w-full">
      {/* Header Section */}
      <div className="space-y-4 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
          <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></span>
          Analysis Complete
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 tracking-tight">
          Investment Analysis Report
        </h1>
        <p className="text-lg text-slate-600">
          {pitch?.companyName || pitch?.company_name} — {pitch?.industry || 'Startup'} • {pitch?.stage || pitch?.currentStage}
        </p>
      </div>

      {/* Investment Score - Hero Section */}
      {analysisData.investment_score && (
        <div className="bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-8 sm:p-10 rounded-3xl shadow-2xl text-white relative overflow-hidden">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 left-0 w-64 h-64 bg-white rounded-full -translate-x-1/2 -translate-y-1/2"></div>
            <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full translate-x-1/3 translate-y-1/3"></div>
          </div>
          
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-8">
            <div className="space-y-3">
              <p className="text-sm font-semibold uppercase tracking-wider text-indigo-100">
                Overall Investment Verdict
              </p>
              <p className="text-2xl sm:text-3xl font-bold leading-tight">
                {analysisData.overall_verdict || 'Processing evaluation...'}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-7xl sm:text-8xl font-black">
                  {analysisData.investment_score}
                </div>
                <div className="text-lg font-semibold text-indigo-100">out of 10</div>
              </div>
              {/* Score Indicator */}
              <div className="flex flex-col gap-1">
                {[...Array(10)].map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-3 rounded-full ${
                      i < analysisData.investment_score ? 'bg-white' : 'bg-white/30'
                    }`}
                  ></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Strengths"
          value={analysisData.pros?.length || 0}
          color="green"
          icon="✨"
        />
        <StatCard
          label="Concerns"
          value={analysisData.cons?.length || 0}
          color="red"
          icon="⚠️"
        />
        <StatCard
          label="Recommendations"
          value={analysisData.recommendations?.length || 0}
          color="purple"
          icon="💡"
        />
        <StatCard
          label="Risk Areas"
          value={analysisData.risk_assessment ? Object.keys(analysisData.risk_assessment).length : 0}
          color="orange"
          icon="🛡️"
        />
      </div>

      {/* Main Analysis Sections */}
      {analysisData.pros && (
        <AnalysisSection title="✨ Key Strengths" items={analysisData.pros} color="green" icon="✨" />
      )}
      
      {analysisData.cons && (
        <AnalysisSection title="⚠️ Major Concerns" items={analysisData.cons} color="red" icon="⚠️" />
      )}
      
      {analysisData.good_parts && (
        <AnalysisSection title="👍 What's Being Done Well" items={analysisData.good_parts} color="blue" icon="👍" />
      )}
      
      {analysisData.bad_parts && (
        <AnalysisSection title="🔧 Areas Needing Improvement" items={analysisData.bad_parts} color="orange" icon="🔧" />
      )}

      {/* Risk Assessment - Visual Cards */}
      {analysisData.risk_assessment && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-900 rounded-lg flex items-center justify-center">
              <span className="text-xl">🛡️</span>
            </div>
            <h2 className="text-3xl font-bold text-slate-900">Risk Assessment</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {Object.entries(analysisData.risk_assessment).map(([key, value]) => {
              const severity = value.toLowerCase().includes('high') ? 'high' : 
                             value.toLowerCase().includes('medium') ? 'medium' : 'low';
              const severityColors = {
                high: 'border-red-300 bg-red-50',
                medium: 'border-orange-300 bg-orange-50',
                low: 'border-green-300 bg-green-50'
              };
              
              return (
                <div
                  key={key}
                  className={`p-6 rounded-2xl border-2 ${severityColors[severity]} shadow-sm hover:shadow-md transition-shadow`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-bold text-slate-900 capitalize text-lg">
                      {key.replace(/_/g, ' ')}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                      severity === 'high' ? 'bg-red-200 text-red-900' :
                      severity === 'medium' ? 'bg-orange-200 text-orange-900' :
                      'bg-green-200 text-green-900'
                    }`}>
                      {severity}
                    </span>
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{value}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {analysisData.recommendations && (
        <AnalysisSection 
          title="💡 Strategic Recommendations" 
          items={analysisData.recommendations} 
          color="purple" 
          icon="💡"
        />
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 pt-8 border-t-2 border-slate-200">
        <Button
          onClick={onBack}
          variant="outline"
          className="flex-1 py-6 text-base border-slate-300 hover:bg-slate-100 font-semibold"
        >
          ← Back to Dashboard
        </Button>
        <Button 
          className="flex-1 py-6 text-base bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 font-semibold shadow-lg flex items-center justify-center gap-2"
          onClick={() => {
            console.log('Download button clicked');
            console.log('analysisData:', analysisData);
            console.log('pitch:', pitch);
            generatePDFReport(analysisData, pitch);
          }}
        >
          <Download className="w-5 h-5" />
          Download Detailed PDF Report
        </Button>
      </div>
    </div>
  );
}

function StatCard({ label, value, color, icon }) {
  const colorMap = {
    green: 'from-green-50 to-green-100 border-green-300 text-green-700',
    red: 'from-red-50 to-red-100 border-red-300 text-red-700',
    purple: 'from-purple-50 to-purple-100 border-purple-300 text-purple-700',
    orange: 'from-orange-50 to-orange-100 border-orange-300 text-orange-700',
  };

  return (
    <div className={`bg-gradient-to-br ${colorMap[color]} border-2 rounded-2xl p-4 text-center shadow-sm`}>
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-xs font-semibold uppercase mt-1">{label}</div>
    </div>
  );
}

function AnalysisSection({ title, items, color }) {
  const colorMap = {
    green: 'border-green-300 bg-gradient-to-br from-green-50 to-green-100',
    red: 'border-red-300 bg-gradient-to-br from-red-50 to-red-100',
    blue: 'border-blue-300 bg-gradient-to-br from-blue-50 to-blue-100',
    orange: 'border-orange-300 bg-gradient-to-br from-orange-50 to-orange-100',
    purple: 'border-purple-300 bg-gradient-to-br from-purple-50 to-purple-100',
  };

  const iconMap = {
    green: '✨',
    red: '⚠️',
    blue: '👍',
    orange: '🔧',
    purple: '💡',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-slate-900 rounded-lg flex items-center justify-center">
          <span className="text-xl">{iconMap[color]}</span>
        </div>
        <h2 className="text-3xl font-bold text-slate-900">{title}</h2>
      </div>
      <div className="space-y-4">
        {Array.isArray(items) && items.length > 0 ? (
          items.map((item, idx) => (
            <div
              key={idx}
              className={`p-6 rounded-2xl border-2 ${colorMap[color] || 'border-slate-200 bg-white'} shadow-sm hover:shadow-md transition-all`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-7 h-7 bg-white rounded-full flex items-center justify-center font-bold text-sm text-slate-700 shadow-sm">
                  {idx + 1}
                </div>
                <p className="text-slate-800 leading-relaxed flex-1">{item}</p>
              </div>
            </div>
          ))
        ) : (
          <div className="p-6 rounded-2xl border-2 border-slate-200 bg-slate-50 text-slate-500 italic text-center">
            No data available in this category
          </div>
        )}
      </div>
    </div>
  );
}

export default ConversationInterface;