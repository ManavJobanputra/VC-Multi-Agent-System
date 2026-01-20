import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Upload, Sparkles, FileText, Building2, DollarSign, Users, Target, Loader2 } from 'lucide-react';

// Test data utility
const TEST_DATA = {
  companyName: "TechVenture AI",
  industry: "Artificial Intelligence / SaaS",
  foundedYear: "2023",
  teamSize: "8",
  currentStage: "Seed",
  fundingAmount: "500000",
  revenueModel: "Subscription-based SaaS with tiered pricing. We charge $99/month for startups, $499/month for SMBs, and custom enterprise pricing starting at $2000/month.",
  problemStatement: "Businesses spend 40% of their time on repetitive data entry and analysis tasks. Current solutions are either too expensive, too complex, or lack AI capabilities.",
  solution: "Our AI-powered automation platform reduces manual work by 80% through intelligent document processing, automated data extraction, and predictive analytics.",
  targetMarket: "B2B SaaS targeting SMBs and enterprises in finance, healthcare, and legal sectors. Total addressable market of $15B.",
  traction: "250 beta users, $15K MRR, 25% month-over-month growth. Partnerships with 3 Fortune 500 companies in pilot phase.",
  competitiveAdvantage: "Proprietary AI models with 95% accuracy, 10x faster than competitors, and seamless integration with existing workflows."
};

function App() {
  const [isLoading, setIsLoading] = useState(false);
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

  const fillTestData = () => {
    setFormData(TEST_DATA);
  };

  const handleSubmit = () => {
    // Validate required fields
    const requiredFields = ['companyName', 'industry', 'foundedYear', 'teamSize', 'currentStage', 'fundingAmount', 'revenueModel', 'problemStatement', 'solution', 'targetMarket', 'traction', 'competitiveAdvantage'];
    const missingFields = requiredFields.filter(field => !formData[field].trim());
    
    if (missingFields.length > 0) {
      alert('Please fill all required fields');
      return;
    }
    
    setIsLoading(true);
    
    // Simulate processing time
    setTimeout(() => {
      setIsLoading(false);
      // Later: navigate to results page
    }, 6000);
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">VC Pitch Analyzer</h1>
                <p className="text-sm text-gray-500">AI-Powered Startup Evaluation</p>
              </div>
            </div>
            <Button variant="outline" onClick={fillTestData}>
              <FileText className="w-4 h-4 mr-2" />
              Fill Test Data
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="text-2xl">Submit Your Startup Pitch</CardTitle>
            <CardDescription>
              Provide details about your startup and optionally upload your pitch deck for comprehensive AI analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Basic Information */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-lg font-semibold text-gray-800 border-b pb-2">
                  <Building2 className="w-5 h-5 text-indigo-600" />
                  Basic Information
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="companyName">Company Name *</Label>
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
                      placeholder="e.g., AI/SaaS, FinTech"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="foundedYear">Founded Year *</Label>
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
                    <Label htmlFor="teamSize">Team Size *</Label>
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
                    <Label htmlFor="currentStage">Current Stage *</Label>
                    <Input
                      id="currentStage"
                      name="currentStage"
                      value={formData.currentStage}
                      onChange={handleInputChange}
                      placeholder="e.g., Seed, Series A"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="fundingAmount">Funding Sought ($) *</Label>
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
                <div className="flex items-center gap-2 text-lg font-semibold text-gray-800 border-b pb-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  Business Model & Strategy
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="revenueModel">Revenue Model *</Label>
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
                  <Label htmlFor="problemStatement">Problem Statement *</Label>
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
                  <Label htmlFor="solution">Your Solution *</Label>
                  <Textarea
                    id="solution"
                    name="solution"
                    value={formData.solution}
                    onChange={handleInputChange}
                    placeholder="How does your product/service solve this problem?"
                    rows={3}
                  />
                </div>
              </div>

              {/* Market & Traction */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-lg font-semibold text-gray-800 border-b pb-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  Market & Traction
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="targetMarket">Target Market *</Label>
                  <Textarea
                    id="targetMarket"
                    name="targetMarket"
                    value={formData.targetMarket}
                    onChange={handleInputChange}
                    placeholder="Describe your target market and size..."
                    rows={3}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="traction">Current Traction *</Label>
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
                  <Label htmlFor="competitiveAdvantage">Competitive Advantage *</Label>
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
                <div className="flex items-center gap-2 text-lg font-semibold text-gray-800 border-b pb-2">
                  <Upload className="w-5 h-5 text-purple-600" />
                  Pitch Deck (Optional)
                </div>
                
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-400 transition-colors">
                  <input
                    type="file"
                    id="pitchDeck"
                    accept=".pdf,.ppt,.pptx"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <label htmlFor="pitchDeck" className="cursor-pointer">
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                    <p className="text-sm font-medium text-gray-700 mb-1">
                      {uploadedFile ? uploadedFile.name : 'Click to upload pitch deck'}
                    </p>
                    <p className="text-xs text-gray-500">
                      PDF or PPT format (Optional)
                    </p>
                  </label>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-4">
                <Button 
                  onClick={handleSubmit}
                  className="w-full h-12 text-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                >
                  <Sparkles className="w-5 h-5 mr-2" />
                  Analyze My Pitch
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Loading Screen Component
function LoadingScreen() {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  
  const steps = [
    { icon: FileText, text: "Processing pitch data...", duration: 1000 },
    { icon: Users, text: "Analyzing market opportunity...", duration: 1500 },
    { icon: DollarSign, text: "Evaluating financial projections...", duration: 1200 },
    { icon: Target, text: "Assessing competitive landscape...", duration: 1300 },
    { icon: Sparkles, text: "Generating insights...", duration: 1000 }
  ];

  useEffect(() => {
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < steps.length - 1) return prev + 1;
        return prev;
      });
    }, 1200);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev < 100) return prev + 2;
        return 100;
      });
    }, 100);

    return () => {
      clearInterval(stepInterval);
      clearInterval(progressInterval);
    };
  }, []);

  const CurrentIcon = steps[currentStep].icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 flex items-center justify-center">
      <Card className="w-full max-w-md shadow-2xl">
        <CardContent className="pt-12 pb-12">
          <div className="text-center space-y-6">
            {/* Animated Icon */}
            <div className="relative">
              <div className="w-24 h-24 mx-auto bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
                <CurrentIcon className="w-12 h-12 text-white" />
              </div>
              <div className="absolute inset-0 w-24 h-24 mx-auto bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full opacity-20 animate-ping"></div>
            </div>

            {/* Current Step */}
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-gray-800">Analyzing Your Pitch</h2>
              <p className="text-gray-600 font-medium">{steps[currentStep].text}</p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-500">{progress}% Complete</p>
            </div>

            {/* Step Indicators */}
            <div className="flex justify-center gap-2 pt-4">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    index <= currentStep 
                      ? 'bg-indigo-600 w-8' 
                      : 'bg-gray-300'
                  }`}
                ></div>
              ))}
            </div>

            {/* Loading Spinner */}
            <div className="flex justify-center pt-2">
              <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default App;