// Test data for quick form filling during development

export const TEST_DATA = {
  companyName: "TechVenture AI",
  industry: "Artificial Intelligence / SaaS",
  foundedYear: "2023",
  teamSize: "8",
  currentStage: "Seed",
  fundingAmount: "500000",
  revenueModel: "Subscription-based SaaS with tiered pricing. We charge $99/month for startups, $499/month for SMBs, and custom enterprise pricing starting at $2000/month. Additional revenue from professional services and implementation fees.",
  problemStatement: "Businesses spend 40% of their time on repetitive data entry and analysis tasks. Current solutions are either too expensive (enterprise-only), too complex (requiring data science teams), or lack AI capabilities. This results in $2.5 trillion in lost productivity annually across SMBs.",
  solution: "Our AI-powered automation platform reduces manual work by 80% through intelligent document processing, automated data extraction, and predictive analytics. No-code interface allows non-technical users to deploy AI workflows in minutes. Seamless integration with existing tools like Salesforce, QuickBooks, and Google Workspace.",
  targetMarket: "B2B SaaS targeting SMBs and mid-market enterprises in finance, healthcare, legal, and real estate sectors. Total addressable market of $15B, growing at 23% CAGR. Initial focus on finance and legal sectors with 50,000+ potential customers in North America.",
  traction: "250 beta users across 8 countries, $15K MRR with 25% month-over-month growth. 92% customer retention rate. Partnerships with 3 Fortune 500 companies in pilot phase. Featured in TechCrunch and won Best AI Startup at Web Summit 2023. LOIs worth $450K in ARR.",
  competitiveAdvantage: "Proprietary AI models with 95% accuracy (vs 70-80% for competitors). 10x faster processing speed. Patent-pending document understanding technology. Strategic partnerships with Microsoft Azure and AWS. Strong founding team with 2 PhDs in ML and former executives from Google and Salesforce."
};

export const TEST_DATA_VARIATIONS = {
  fintech: {
    companyName: "PayFlow",
    industry: "FinTech / Payment Processing",
    foundedYear: "2022",
    teamSize: "12",
    currentStage: "Series A",
    fundingAmount: "2000000",
    revenueModel: "Transaction fees (2.5% per transaction) + monthly subscription for premium features ($199-$999/month)",
    problemStatement: "Small businesses lose 15% of revenue to payment processing delays and high fees from traditional processors",
    solution: "Real-time payment processing with 0.9% fees and instant settlement using blockchain technology",
    targetMarket: "E-commerce and retail SMBs, $45B TAM",
    traction: "1,200 merchants, $2.5M monthly transaction volume, 40% MoM growth",
    competitiveAdvantage: "Proprietary blockchain integration, lowest fees in market, same-day settlement"
  },
  
  healthtech: {
    companyName: "MediCare AI",
    industry: "HealthTech / Medical Diagnostics",
    foundedYear: "2023",
    teamSize: "15",
    currentStage: "Seed",
    fundingAmount: "1500000",
    revenueModel: "Per-scan pricing model ($50-$200 per diagnostic scan) + hospital subscription packages",
    problemStatement: "Radiologists face 30% diagnostic error rate and 3-week backlogs due to volume overload",
    solution: "AI-powered diagnostic assistant that analyzes medical images with 98% accuracy in under 60 seconds",
    targetMarket: "Hospitals and diagnostic centers, $12B TAM in US alone",
    traction: "5 hospital pilots, 10,000 scans processed, 97% accuracy rate validated by Johns Hopkins",
    competitiveAdvantage: "FDA clearance in process, partnerships with GE Healthcare, peer-reviewed publications in JAMA"
  }
};

export default TEST_DATA;