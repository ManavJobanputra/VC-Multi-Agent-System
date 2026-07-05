import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, Search, Brain, Database, Users, DollarSign, Target, Sparkles } from 'lucide-react';

function LoadingScreen({ agentProgress }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(6);

  const steps = [
    { icon: FileText, title: 'Ingesting pitch + deck', detail: 'Receiving pitch text and optional PDF/PPT deck' },
    { icon: Search, title: 'Parsing & vision pass', detail: 'Extracting text and slide visuals for context' },
    { icon: Database, title: 'Indexing for retrieval', detail: 'Embedding content for retrieval-augmented analysis' },
    { icon: Brain, title: 'Researching the market', detail: 'Generating questions, searching the web, reading sources' },
    { icon: Users, title: 'Team & risk review', detail: 'Assessing team strength and key execution risks' },
    { icon: DollarSign, title: 'Financial checks', detail: 'Reviewing traction, funding ask, and runway signals' },
    { icon: Target, title: 'Competitive landscape', detail: 'Mapping competitors and differentiation' },
    { icon: Sparkles, title: 'Compiling the memo', detail: 'Blending every partner finding into the final verdict' },
  ];

  useEffect(() => {
    if (agentProgress && Object.keys(agentProgress).length > 0) {
      const agentStepMap = {
        financial_analysis_agent: 5,
        market_analysis_agent: 3,
        risk_assessment_agent: 4,
        team_assessment_agent: 4,
        marcus_agent: 7,
      };

      const completedSteps = Object.entries(agentProgress)
        .filter(([_, status]) => status === 'completed')
        .map(([name]) => agentStepMap[name] || 0)
        .sort((a, b) => b - a);

      if (completedSteps.length > 0) {
        const nextStep = Math.min(completedSteps[0] + 1, steps.length - 1);
        setCurrentStep(nextStep);
        setProgress(Math.round((nextStep / (steps.length - 1)) * 80 + 15));
      }
    } else {
      const timers = [];
      steps.forEach((_, index) => {
        if (index === 0) return;
        timers.push(setTimeout(() => setCurrentStep(index), index * 1200));
      });

      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 96) return prev;
          const bump = Math.random() > 0.6 ? 2 : 1;
          return Math.min(prev + bump, 96);
        });
      }, 220);

      return () => {
        timers.forEach(clearTimeout);
        clearInterval(progressInterval);
      };
    }
  }, [agentProgress, steps.length]);

  const CurrentIcon = steps[currentStep].icon;
  const computedProgress = Math.max(progress, Math.round((currentStep / (steps.length - 1)) * 80 + 10));

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4 phase-in">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="score-in inline-flex px-4 py-1.5 rounded-full border border-coral text-coral text-xs font-mono uppercase tracking-widest mb-2">
            Under Review
          </div>
          <h1 className="font-display text-3xl text-ink">Your Partner Is Reviewing</h1>
          <p className="text-ink-soft">Every agent in the room is working through your pitch, live.</p>
        </div>

        {/* Main Card */}
        <Card>
          <CardContent className="pt-2 pb-2">
            <div className="space-y-8">
              {/* Animated Icon */}
              <div className="flex justify-center">
                <div className="relative flex items-center justify-center h-24 w-24">
                  <div className="w-20 h-20 border-2 border-coral rounded-full flex items-center justify-center bg-accent animate-pulse">
                    <CurrentIcon className="w-9 h-9 text-coral" />
                  </div>
                  <div className="absolute w-20 h-20 border border-coral rounded-full opacity-30 animate-ping" />
                </div>
              </div>

              {/* Current Step Info */}
              <div className="text-center space-y-1.5">
                <h2 className="font-display text-xl text-ink">{steps[currentStep].title}</h2>
                <p className="text-sm text-ink/60">{steps[currentStep].detail}</p>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="w-full bg-ink/10 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full bg-coral transition-all duration-300 ease-out"
                    style={{ width: `${computedProgress}%` }}
                  />
                </div>
                <p className="text-xs font-mono text-ink/50 text-center">{computedProgress}% complete</p>
              </div>

              {/* Steps Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {steps.map((step, index) => {
                  const isCompleted = index < currentStep;
                  const isActive = index === currentStep;
                  const StepIcon = step.icon;

                  return (
                    <div key={index} className={`p-3 rounded-lg text-center border transition-all ${
                      isCompleted
                        ? 'bg-sage/10 border-sage/40'
                        : isActive
                          ? 'bg-coral/10 border-coral'
                          : 'bg-ink/[0.03] border-ink/10'
                    }`}>
                      <StepIcon className={`w-4 h-4 mx-auto mb-1 ${
                        isCompleted
                          ? 'text-sage'
                          : isActive
                            ? 'text-coral'
                            : 'text-ink/30'
                      }`} />
                      <p className={`text-[11px] font-medium ${
                        isCompleted
                          ? 'text-sage'
                          : isActive
                            ? 'text-ink'
                            : 'text-ink/40'
                      }`}>{step.title.split(' ')[0]}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-xs font-mono uppercase tracking-widest text-ink-soft">
          This usually takes 30–60 seconds
        </p>
      </div>
    </div>
  );
}

export default LoadingScreen;
