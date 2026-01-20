import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { FileText, Search, Brain, Database, Users, DollarSign, Target, Sparkles, Loader2 } from 'lucide-react';

function LoadingScreen({ agentProgress }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(6);

  const steps = [
    { icon: FileText, title: 'Ingesting pitch + deck', detail: 'Receiving pitch text and optional PDF/PPT deck' },
    { icon: Search, title: 'Parsing & vision pass', detail: 'Extracting text and slide visuals for context' },
    { icon: Database, title: 'Indexing in Qdrant', detail: 'Embedding content for retrieval-augmented analysis' },
    { icon: Brain, title: 'Researching the market', detail: 'Generating questions, searching web, scraping sources' },
    { icon: Users, title: 'Team & risk review', detail: 'Assessing team strength and key execution risks' },
    { icon: DollarSign, title: 'Financial checks', detail: 'Reviewing traction, funding ask, and runway signals' },
    { icon: Target, title: 'Competitive landscape', detail: 'Mapping competitors and differentiation' },
    { icon: Sparkles, title: 'Compiling insights', detail: 'Blending all agents into the final recommendation' },
  ];

  useEffect(() => {
    if (agentProgress && Object.keys(agentProgress).length > 0) {
      // Map agent names to step indices
      const agentStepMap = {
        financial_analysis_agent: 5,
        market_analysis_agent: 3,
        risk_assessment_agent: 4,
        team_assessment_agent: 4,
        marcus_agent: 7,
      };

      // Find the highest completed step from agentProgress
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
      // Fallback: auto-advance if no real progress available
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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-slate-900">Analyzing Your Pitch</h1>
          <p className="text-slate-600">Our AI agents are reviewing your startup in real-time</p>
        </div>

        {/* Main Card */}
        <Card className="shadow-lg border-slate-200 bg-white">
          <CardContent className="pt-8 pb-8 px-8">
            <div className="space-y-8">
              {/* Animated Icon */}
              <div className="flex justify-center">
                <div className="relative flex items-center justify-center h-24 w-24">
                  <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
                    <CurrentIcon className="w-10 h-10 text-white" />
                  </div>
                  <div className="absolute w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full opacity-20 animate-ping"></div>
                </div>
              </div>

              {/* Current Step Info */}
              <div className="text-center space-y-2">
                <h2 className="text-xl font-semibold text-slate-900">{steps[currentStep].title}</h2>
                <p className="text-sm text-slate-600">{steps[currentStep].detail}</p>
              </div>

              {/* Progress Bar */}
              <div className="space-y-3">
                <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-600 transition-all duration-300 ease-out"
                    style={{ width: `${computedProgress}%` }}
                  ></div>
                </div>
                <p className="text-xs font-medium text-slate-500 text-center">{computedProgress}% complete</p>
              </div>

              {/* Steps Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {steps.map((step, index) => {
                  const isCompleted = index < currentStep;
                  const isActive = index === currentStep;
                  const StepIcon = step.icon;
                  
                  return (
                    <div key={index} className={`p-3 rounded-lg text-center transition-all ${
                      isCompleted 
                        ? 'bg-green-50 border border-green-200' 
                        : isActive 
                        ? 'bg-indigo-50 border-2 border-indigo-400' 
                        : 'bg-slate-50 border border-slate-200'
                    }`}>
                      <StepIcon className={`w-5 h-5 mx-auto mb-1 ${
                        isCompleted 
                          ? 'text-green-600' 
                          : isActive 
                          ? 'text-indigo-600' 
                          : 'text-slate-400'
                      }`} />
                      <p className={`text-xs font-medium ${
                        isCompleted 
                          ? 'text-green-700' 
                          : isActive 
                          ? 'text-indigo-700' 
                          : 'text-slate-600'
                      }`}>{step.title.split(' ')[0]}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer Message */}
        <p className="text-center text-sm text-slate-500">This usually takes 30-60 seconds</p>
      </div>
    </div>
  );
}

export default LoadingScreen;