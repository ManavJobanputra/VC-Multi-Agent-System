import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

const PERSONAS = [
  {
    id: 'aarav-mehta',
    initials: 'AM',
    name: 'Aarav Mehta',
    title: 'General Partner — Seed to Series A',
    description: 'Pattern-driven, clarity-obsessed investor who backs founders with deep thinking and asymmetric upside plays.',
    traits: ['Skeptical', 'Direct', 'Clarity-Focused', 'Data-Driven', 'AI/ML Expert'],
    style: 'Calm, measured questioning. Drills into assumptions. Asks "Why now?" and "What if this fails?"',
  },
  {
    id: 'vikram-khanna',
    initials: 'VK',
    name: 'Vikram Khanna',
    title: 'Managing Partner — Aggressive Early-Stage',
    description: 'Blunt and zero patience for polish. Believes tough questions reveal reality. If he argues with you, he’s interested.',
    traits: ['Brutally Honest', 'Direct', 'Aggressive', 'Reality-Testing', 'Fast-Paced'],
    style: 'Blunt and sarcastic. Interrupts frequently. "This doesn’t make sense" and "Convince me I’m wrong."',
  },
  {
    id: 'template',
    initials: '?',
    name: 'Coming Soon',
    title: 'Additional Partners',
    description: 'More investor personas will join the room to represent a wider range of investment philosophies.',
    traits: ['In Development'],
    style: 'New personas are added as founder profiles to the personas/ directory.',
    disabled: true,
  },
];

function PersonaSelect({ onPersonaSelect }) {
  const [selectedId, setSelectedId] = useState(null);

  const handleContinue = () => {
    if (selectedId && selectedId !== 'template') {
      const persona = PERSONAS.find((p) => p.id === selectedId);
      onPersonaSelect(persona);
    }
  };

  return (
    <div className="min-h-screen bg-paper phase-in relative">
      <div className="margin-marks margin-marks-left" data-label="VC Pitch Analyzer" />
      <div className="margin-marks margin-marks-right" data-label="Step 01 of 03" />

      {/* Header */}
      <div className="border-b border-border sticky top-0 z-10 bg-paper/95 backdrop-blur">
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
          <p className="hidden sm:block text-xs font-mono uppercase tracking-widest text-ink-soft">
            Step 01 · Partner Selection
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="mb-12 max-w-2xl">
          <h2 className="font-display text-4xl sm:text-5xl text-ink leading-[1.1]">
            Choose who's across the table.
          </h2>
          <p className="text-ink-soft mt-4 leading-relaxed">
            Each partner brings a distinct evaluation framework and tone. Marcus will stay strictly
            in character as your chosen partner for the entire session.
          </p>
        </div>

        {/* Persona Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
          {PERSONAS.map((persona) => {
            const isSelected = selectedId === persona.id;
            return (
              <Card
                key={persona.id}
                className={`relative cursor-pointer transition-colors duration-150 border-2 ${
                  isSelected
                    ? 'border-emerald-500 ring-4 ring-emerald-500/15'
                    : persona.disabled
                      ? 'opacity-45 cursor-not-allowed border-transparent'
                      : 'border-transparent hover:border-coral/40'
                }`}
                onClick={() => !persona.disabled && setSelectedId(persona.id)}
              >
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-full border border-ink/15 flex items-center justify-center font-display text-sm text-ink/70 flex-shrink-0">
                      {persona.initials}
                    </div>
                    <div>
                      <h3 className="font-display text-lg text-ink leading-tight">{persona.name}</h3>
                      <p className="text-xs text-ink-soft mt-0.5">{persona.title}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-sm text-ink/75 leading-relaxed">{persona.description}</p>

                  <div className="flex flex-wrap gap-1.5">
                    {persona.traits.map((trait) => (
                      <span
                        key={trait}
                        className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wide border border-ink/15 text-ink-soft"
                      >
                        {trait}
                      </span>
                    ))}
                  </div>

                  <p className="text-sm text-ink/70 italic border-l-2 border-coral/50 pl-3 leading-relaxed">
                    {persona.style}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Note */}
        <div className="border-l-2 border-coral/50 bg-paper-dim pl-4 py-3 mb-10 rounded-r-md">
          <p className="text-xs font-mono uppercase tracking-widest text-coral mb-1">Note</p>
          <p className="text-sm text-ink-soft leading-relaxed">
            The selected partner's framework, tone, and priorities govern every question and the final verdict.
          </p>
        </div>

        {/* Action Button */}
        <Button
          onClick={handleContinue}
          disabled={!selectedId || selectedId === 'template'}
          size="lg"
          className="w-full h-13 text-base font-medium"
        >
          Begin Diligence
        </Button>
      </div>
    </div>
  );
}

export default PersonaSelect;
