import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Upload } from 'lucide-react';

function SectionEyebrow({ index, children }) {
  return (
    <div className="flex items-center gap-3 pb-2 border-b border-ink/10">
      <span className="font-mono text-xs text-coral tracking-widest">{index}</span>
      <span className="text-sm font-semibold uppercase tracking-wide text-ink/70">{children}</span>
    </div>
  );
}

function HomePage({ onSubmit }) {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [formData, setFormData] = useState({
    companyName: '',
    industry: '',
    foundedYear: '',
    teamSize: '',
    currentStage: '',
    fundingAmount: '',
    revenueModel: '',
    problemStatement: '',
    solution: '',
    targetMarket: '',
    traction: '',
    competitiveAdvantage: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const validTypes = ['application/pdf', 'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'];
      if (validTypes.includes(file.type)) {
        setUploadedFile(file);
      } else {
        alert('Please upload a PDF or PPT file');
      }
    }
  };

  const handleSubmit = () => {
    const requiredFields = ['companyName', 'industry', 'foundedYear', 'teamSize', 'currentStage', 'fundingAmount', 'revenueModel', 'problemStatement', 'solution', 'targetMarket', 'traction', 'competitiveAdvantage'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());

    if (missingFields.length > 0) {
      alert('Please fill all required fields');
      return;
    }

    onSubmit({ formData, file: uploadedFile });
  };

  return (
    <div className="min-h-screen bg-paper phase-in relative">
      <div className="margin-marks margin-marks-left" data-label="VC Pitch Analyzer" />
      <div className="margin-marks margin-marks-right" data-label="Step 02 of 03" />

      {/* Header */}
      <div className="border-b border-border sticky top-0 z-10 bg-paper/95 backdrop-blur">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
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
            Step 02 · Pitch Intake
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-12">
        <Card>
          <CardHeader>
            <CardTitle className="font-display text-2xl font-normal">Submit for Diligence</CardTitle>
            <CardDescription>
              Give your partner the details of the business. Optionally attach your deck for deeper context.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {/* Basic Information */}
              <div className="space-y-4">
                <SectionEyebrow index="01">Basic Information</SectionEyebrow>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="companyName">Company name *</Label>
                    <Input
                      id="companyName"
                      name="companyName"
                      value={formData.companyName}
                      onChange={handleInputChange}
                      placeholder="e.g., TechVenture AI"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="industry">Industry *</Label>
                    <Input
                      id="industry"
                      name="industry"
                      value={formData.industry}
                      onChange={handleInputChange}
                      placeholder="e.g., AI/SaaS, Fintech"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="foundedYear">Founded year *</Label>
                    <Input
                      id="foundedYear"
                      name="foundedYear"
                      type="number"
                      value={formData.foundedYear}
                      onChange={handleInputChange}
                      placeholder="e.g., 2023"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="teamSize">Team size *</Label>
                    <Input
                      id="teamSize"
                      name="teamSize"
                      type="number"
                      value={formData.teamSize}
                      onChange={handleInputChange}
                      placeholder="e.g., 8"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="currentStage">Current stage *</Label>
                    <Input
                      id="currentStage"
                      name="currentStage"
                      value={formData.currentStage}
                      onChange={handleInputChange}
                      placeholder="e.g., Seed, Series A"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fundingAmount">Funding sought ($) *</Label>
                    <Input
                      id="fundingAmount"
                      name="fundingAmount"
                      type="number"
                      value={formData.fundingAmount}
                      onChange={handleInputChange}
                      placeholder="e.g., 500000"
                    />
                  </div>
                </div>
              </div>

              {/* Business Model & Strategy */}
              <div className="space-y-4">
                <SectionEyebrow index="02">Business Model & Strategy</SectionEyebrow>

                <div className="space-y-2">
                  <Label htmlFor="revenueModel">Revenue model *</Label>
                  <Textarea
                    id="revenueModel"
                    name="revenueModel"
                    value={formData.revenueModel}
                    onChange={handleInputChange}
                    placeholder="Describe how your company makes money..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="problemStatement">Problem statement *</Label>
                  <Textarea
                    id="problemStatement"
                    name="problemStatement"
                    value={formData.problemStatement}
                    onChange={handleInputChange}
                    placeholder="What problem are you solving?"
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="solution">Your solution *</Label>
                  <Textarea
                    id="solution"
                    name="solution"
                    value={formData.solution}
                    onChange={handleInputChange}
                    placeholder="How does your product or service solve this problem?"
                    rows={3}
                  />
                </div>
              </div>

              {/* Market & Traction */}
              <div className="space-y-4">
                <SectionEyebrow index="03">Market & Traction</SectionEyebrow>

                <div className="space-y-2">
                  <Label htmlFor="targetMarket">Target market *</Label>
                  <Textarea
                    id="targetMarket"
                    name="targetMarket"
                    value={formData.targetMarket}
                    onChange={handleInputChange}
                    placeholder="Describe your target market and its size..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="traction">Current traction *</Label>
                  <Textarea
                    id="traction"
                    name="traction"
                    value={formData.traction}
                    onChange={handleInputChange}
                    placeholder="Users, revenue, partnerships, growth metrics..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="competitiveAdvantage">Competitive advantage *</Label>
                  <Textarea
                    id="competitiveAdvantage"
                    name="competitiveAdvantage"
                    value={formData.competitiveAdvantage}
                    onChange={handleInputChange}
                    placeholder="What makes you different from competitors?"
                    rows={3}
                  />
                </div>
              </div>

              {/* File Upload */}
              <div className="space-y-4">
                <SectionEyebrow index="04">Pitch Deck (Optional)</SectionEyebrow>

                <div className="border-2 border-dashed border-ink/15 rounded-lg p-6 text-center hover:border-coral/50 transition-colors">
                  <input
                    type="file"
                    id="pitchDeck"
                    accept=".pdf,.ppt,.pptx"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <label htmlFor="pitchDeck" className="cursor-pointer">
                    <Upload className="w-8 h-8 mx-auto text-coral mb-3" />
                    <p className="text-sm font-medium text-ink/80 mb-1">
                      {uploadedFile ? uploadedFile.name : 'Click to upload your deck'}
                    </p>
                    <p className="text-xs text-ink/50">PDF or PPT format · optional</p>
                  </label>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <Button
                  onClick={handleSubmit}
                  size="lg"
                  className="w-full h-13 text-base font-medium"
                >
                  Submit for Diligence
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default HomePage;
