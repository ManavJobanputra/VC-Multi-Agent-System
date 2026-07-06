import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  ArrowRight, MessageSquare, FileCheck, TrendingUp, ShieldAlert,
  Users, Rocket, Sparkles, Landmark,
} from 'lucide-react';

const STATS = [
  { value: '6', label: 'Specialist agents' },
  { value: '2', label: 'Investor personas' },
  { value: 'Live', label: 'Cross-examination' },
];

const STEPS = [
  {
    index: '01',
    title: 'Submit your pitch',
    detail: 'Company basics, business model, market, and traction — with an optional deck for deeper context.',
  },
  {
    index: '02',
    title: 'Face live questioning',
    detail: 'Your chosen partner cross-examines you in real time, following up until the answers hold up.',
  },
  {
    index: '03',
    title: 'Get your investment memo',
    detail: 'A structured verdict — strengths, risks, and a recommendation — the way a real partner would write it.',
  },
];

const AGENTS = [
  { icon: TrendingUp, name: 'Financial Analysis', detail: 'Revenue model, burn, and runway' },
  { icon: Landmark, name: 'Market Research', detail: 'TAM, competitors, and pricing' },
  { icon: ShieldAlert, name: 'Risk Assessment', detail: 'Technical, market, and regulatory risk' },
  { icon: Users, name: 'Team Assessment', detail: 'Founder-market fit and gaps' },
  { icon: Rocket, name: 'Execution Feasibility', detail: 'Milestones vs. capital and timeline' },
  { icon: Sparkles, name: 'Marcus', detail: 'Synthesizes every finding into one verdict' },
];

function LandingPage({ onStart, isSignedIn, onLogout }) {
  return (
    <div className="min-h-screen bg-paper phase-in relative">
      <div className="margin-marks margin-marks-left" data-label="VC Pitch Analyzer" />
      <div className="margin-marks margin-marks-right" data-label="Diligence Room" />

      {/* Header */}
      <div className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-coral flex items-center justify-center font-display text-xs text-white">
              VM
            </div>
            <div>
              <h1 className="font-display text-xl text-ink tracking-tight">VC Pitch Analyzer</h1>
              <p className="text-xs font-mono uppercase tracking-widest text-ink-soft">Diligence Room</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {isSignedIn && (
              <>
                <Link to="/dashboard" className="text-sm text-ink-soft hover:text-ink underline underline-offset-4">
                  Dashboard
                </Link>
                <button
                  type="button"
                  onClick={onLogout}
                  className="text-sm text-ink-soft hover:text-ink underline underline-offset-4"
                >
                  Log Out
                </button>
              </>
            )}
            <Button onClick={onStart} variant="outline">
              Begin Session
            </Button>
          </div>
        </div>
      </div>

      {/* Hero */}
      <div className="max-w-6xl mx-auto px-6 pt-20 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-16 items-start">
          <div>
            <p className="text-xs font-mono uppercase tracking-widest text-coral mb-4">
              Rehearse the room before you're in it
            </p>
            <h2 className="font-display text-5xl sm:text-6xl text-ink leading-[1.05] mb-6">
              Pitch a real investor, before you pitch a real investor.
            </h2>
            <p className="text-lg text-ink-soft leading-relaxed max-w-xl mb-8">
              Submit your startup, choose the partner across the table, and get cross-examined
              live — the same way a founder gets grilled in an actual seed or Series A meeting.
              Walk away with a written investment memo, not a participation trophy.
            </p>
            <div className="flex items-center gap-4 mb-16">
              <Button onClick={onStart} size="lg" className="text-base font-medium">
                Begin Diligence
                <ArrowRight className="w-4 h-4" />
              </Button>
              <p className="text-sm text-ink-soft">No sign-up. Takes about 5 minutes.</p>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-6 max-w-xl border-t border-border pt-8">
              {STATS.map((stat) => (
                <div key={stat.label}>
                  <p className="font-display text-3xl text-coral">{stat.value}</p>
                  <p className="text-xs text-ink-soft mt-1 uppercase tracking-wide">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Sample memo preview */}
          <div className="hidden lg:block bg-card border border-border rounded-xl p-7 lg:mt-10">
            <p className="text-xs font-mono uppercase tracking-widest text-coral mb-5">Sample Memo</p>
            <div className="flex items-end gap-5 border-b border-border pb-6 mb-6">
              <p className="font-display text-6xl text-ink leading-none">7.8</p>
              <div className="pb-1">
                <span className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-mono uppercase tracking-widest border text-sage border-sage">
                  Invest
                </span>
                <p className="text-sm text-ink-soft mt-2 max-w-[16rem] leading-relaxed">
                  Strong founder-market fit, thin data on unit economics.
                </p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex gap-2.5 text-sm">
                <span className="text-sage mt-0.5">＋</span>
                <p className="text-ink-soft">Technical co-founders with direct domain experience</p>
              </div>
              <div className="flex gap-2.5 text-sm">
                <span className="text-maroon mt-0.5">－</span>
                <p className="text-ink-soft">No burn rate or CAC disclosed under questioning</p>
              </div>
              <div className="flex gap-2.5 text-sm">
                <span className="text-gold mt-0.5">▲</span>
                <p className="text-ink-soft">Team risk: medium — no dedicated sales hire yet</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* How it works */}
      <div className="border-t border-border bg-paper-dim">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <h3 className="font-display text-3xl text-ink mb-10">How a session runs</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((step) => (
              <div key={step.index}>
                <p className="font-mono text-sm text-coral mb-3">{step.index}</p>
                <h4 className="font-display text-xl text-ink mb-2">{step.title}</h4>
                <p className="text-sm text-ink-soft leading-relaxed">{step.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Agent roster */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="max-w-2xl mb-10">
          <h3 className="font-display text-3xl text-ink mb-3">Six specialists read every pitch</h3>
          <p className="text-ink-soft leading-relaxed">
            Behind the conversation, a full evaluation panel works your pitch from every angle
            before Marcus writes the final memo.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {AGENTS.map((agent) => (
            <div key={agent.name} className="bg-card border border-border rounded-lg p-5">
              <agent.icon className="w-5 h-5 text-coral mb-3" strokeWidth={1.75} />
              <p className="font-medium text-ink text-sm mb-1">{agent.name}</p>
              <p className="text-xs text-ink-soft leading-relaxed">{agent.detail}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Final CTA */}
      <div className="border-t border-border">
        <div className="max-w-6xl mx-auto px-6 py-16 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <MessageSquare className="w-8 h-8 text-coral flex-shrink-0 mt-1" strokeWidth={1.5} />
            <div>
              <h3 className="font-display text-2xl text-ink mb-1">Ready to be questioned?</h3>
              <p className="text-ink-soft text-sm">Choose your partner and submit your pitch.</p>
            </div>
          </div>
          <Button onClick={onStart} size="lg" className="text-base font-medium flex-shrink-0">
            Begin Diligence
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between text-xs text-ink-soft">
          <div className="flex items-center gap-1.5">
            <FileCheck className="w-3.5 h-3.5" />
            VC Pitch Analyzer
          </div>
          <p>Session data is used only to run your evaluation.</p>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
