import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkles, User2 } from 'lucide-react';

const PERSONAS = [
  {
    id: 'aarav-mehta',
    name: 'Aarav Mehta',
    title: 'High-Conviction Venture Capitalist',
    description: 'General Partner, Early-stage VC (Seed to Series A). Pattern-driven, clarity-obsessed investor who backs founders with deep thinking and asymmetric upside plays.',
    traits: ['Skeptical', 'Direct', 'Clarity-Focused', 'Data-Driven', 'AI/ML Expert'],
    style: 'Calm, measured questioning. Drills into assumptions. Asks "Why now?" and "What if this fails?"',
  },
  {
    id: 'vikram-khanna',
    name: 'Vikram Khanna',
    title: 'The Brutally Honest Venture Capitalist',
    description: 'Managing Partner, Aggressive Early-Stage VC. Blunt, sarcastic, and zero politeness. Believes tough questions reveal reality. If he argues with you, he\'s interested.',
    traits: ['Brutally Honest', 'Direct', 'Aggressive', 'Reality-Testing', 'Fast-Paced'],
    style: 'Blunt and sarcastic. Interrupts frequently. Short, sharp sentences. "This doesn\'t make sense" and "Convince me I\'m wrong."',
  },
  {
    id: 'template',
    name: 'Coming Soon',
    title: 'More Personas',
    description: 'Additional investor personas will be added to represent diverse investment philosophies and approaches.',
    traits: ['Template', 'Placeholder', 'Future-Ready'],
    style: 'Add more personas to the personas/ folder as .md files to expand evaluation styles.',
    disabled: true,
  },
];

function PersonaSelect({ onPersonaSelect }) {
  const [selectedId, setSelectedId] = useState(null);

  const handleContinue = () => {
    if (selectedId && selectedId !== 'template') {
      const persona = PERSONAS.find(p => p.id === selectedId);
      onPersonaSelect(persona);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">VC Pitch Analyzer</h1>
                <p className="text-sm text-gray-500">Select Your Investor Persona</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-12">
        <div className="mb-8 text-center space-y-2">
          <h2 className="text-3xl font-bold text-gray-900">Choose Your Investor Type</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Select an investor persona to receive feedback tailored to their specific investment philosophy, evaluation criteria, and communication style. The Marcus Agent will adopt this persona strictly throughout the evaluation.
          </p>
        </div>

        {/* Persona Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {PERSONAS.map((persona) => (
            <Card
              key={persona.id}
              className={`cursor-pointer transition-all ${
                selectedId === persona.id
                  ? 'ring-2 ring-indigo-600 shadow-lg'
                  : persona.disabled
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:shadow-lg hover:ring-1 hover:ring-indigo-400'
              } ${persona.disabled ? 'bg-gray-50' : 'bg-white'}`}
              onClick={() => !persona.disabled && setSelectedId(persona.id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-2">
                    <CardTitle className="flex items-center gap-2">
                      <User2 className="w-5 h-5 text-indigo-600" />
                      {persona.name}
                    </CardTitle>
                    <CardDescription className="text-sm font-medium text-indigo-700">
                      {persona.title}
                    </CardDescription>
                  </div>
                  {selectedId === persona.id && (
                    <div className="w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-gray-700 text-sm">{persona.description}</p>

                {/* Traits */}
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Key Traits</p>
                  <div className="flex flex-wrap gap-2">
                    {persona.traits.map((trait) => (
                      <span
                        key={trait}
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                          selectedId === persona.id
                            ? 'bg-indigo-100 text-indigo-800'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {trait}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Style */}
                <div className="pt-2 border-t">
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Communication Style</p>
                  <p className="text-sm text-gray-600 italic">{persona.style}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Info Box */}
        <Card className="bg-blue-50 border-blue-200 mb-8">
          <CardContent className="pt-6">
            <p className="text-sm text-blue-900">
              <strong>💡 Tip:</strong> The Marcus Agent will strictly embody the selected persona's evaluation framework, communication patterns, and investment philosophy. All feedback will reflect their specific perspective and priorities.
            </p>
          </CardContent>
        </Card>

        {/* Action Button */}
        <div className="flex gap-3">
          <Button
            onClick={handleContinue}
            disabled={!selectedId || selectedId === 'template'}
            className="flex-1 h-12 text-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            Continue with Selected Persona
          </Button>
        </div>
      </div>
    </div>
  );
}

export default PersonaSelect;
