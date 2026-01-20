import jsPDF from 'jspdf';
import 'jspdf-autotable';

export const generatePDFReport = (analysisData, pitchData) => {
  try {
    console.log('PDF Generation - Analysis Data:', analysisData);
    console.log('PDF Generation - Pitch Data:', pitchData);

    if (!analysisData) {
      console.error('No analysis data provided');
      alert('Cannot generate PDF: No analysis data available');
      return;
    }

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.width;
    const pageHeight = doc.internal.pageSize.height;
    let yPos = 20;

  // Helper function to add page if needed
  const checkAddPage = (spaceNeeded = 20) => {
    if (yPos + spaceNeeded > pageHeight - 20) {
      doc.addPage();
      yPos = 20;
      return true;
    }
    return false;
  };

  // Helper to add section
  const addSection = (title, content, color = [79, 70, 229]) => {
    checkAddPage(30);
    
    // Section title with colored background
    doc.setFillColor(color[0], color[1], color[2]);
    doc.roundedRect(14, yPos - 5, pageWidth - 28, 12, 2, 2, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(14);
    doc.setFont(undefined, 'bold');
    doc.text(title, 20, yPos + 3);
    yPos += 15;

    doc.setTextColor(0, 0, 0);
    doc.setFont(undefined, 'normal');
    doc.setFontSize(10);

    if (Array.isArray(content)) {
      content.forEach((item, idx) => {
        checkAddPage(15);
        const lines = doc.splitTextToSize(`${idx + 1}. ${item}`, pageWidth - 50);
        doc.text(lines, 25, yPos);
        yPos += lines.length * 5 + 5;
      });
    } else if (typeof content === 'object') {
      Object.entries(content).forEach(([key, value]) => {
        checkAddPage(15);
        doc.setFont(undefined, 'bold');
        doc.text(`${key.replace(/_/g, ' ').toUpperCase()}:`, 20, yPos);
        yPos += 6;
        doc.setFont(undefined, 'normal');
        const lines = doc.splitTextToSize(value, pageWidth - 50);
        doc.text(lines, 25, yPos);
        yPos += lines.length * 5 + 3;
      });
    } else {
      const lines = doc.splitTextToSize(content, pageWidth - 40);
      doc.text(lines, 20, yPos);
      yPos += lines.length * 5;
    }
    
    yPos += 10;
  };

  // ==================== PAGE 1: COVER PAGE ====================
  
  // Gradient background (simulated with rectangles)
  doc.setFillColor(238, 242, 255);
  doc.rect(0, 0, pageWidth, pageHeight, 'F');
  
  // Company logo placeholder
  doc.setFillColor(79, 70, 229);
  doc.circle(pageWidth / 2, 60, 20, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(24);
  doc.text('AI', pageWidth / 2, 63, { align: 'center' });

  // Title
  doc.setTextColor(30, 41, 59);
  doc.setFontSize(32);
  doc.setFont(undefined, 'bold');
  doc.text('Investment Analysis Report', pageWidth / 2, 100, { align: 'center' });

  // Company name
  doc.setFontSize(24);
  doc.setTextColor(79, 70, 229);
  doc.text(pitchData?.companyName || pitchData?.company_name || 'Startup', pageWidth / 2, 120, { align: 'center' });

  // Subtitle
  doc.setFontSize(14);
  doc.setTextColor(100, 116, 139);
  doc.setFont(undefined, 'normal');
  doc.text(`${pitchData?.industry || 'Technology'} • ${pitchData?.stage || pitchData?.currentStage || 'Seed Stage'}`, pageWidth / 2, 135, { align: 'center' });

  // Investment Score Box
  doc.setFillColor(79, 70, 229);
  doc.roundedRect(pageWidth / 2 - 40, 160, 80, 60, 5, 5, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(48);
  doc.setFont(undefined, 'bold');
  doc.text(`${analysisData.investment_score || 'N/A'}`, pageWidth / 2, 190, { align: 'center' });
  doc.setFontSize(12);
  doc.text('INVESTMENT SCORE', pageWidth / 2, 210, { align: 'center' });

  // Overall Verdict
  if (analysisData.overall_verdict) {
    doc.setFontSize(11);
    doc.setTextColor(30, 41, 59);
    const verdictLines = doc.splitTextToSize(analysisData.overall_verdict, pageWidth - 60);
    doc.text(verdictLines, pageWidth / 2, 240, { align: 'center' });
  }

  // Footer
  doc.setFontSize(10);
  doc.setTextColor(148, 163, 184);
  doc.text(`Generated on ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`, pageWidth / 2, pageHeight - 20, { align: 'center' });
  doc.text('Powered by VC Multi-Agent Analysis System', pageWidth / 2, pageHeight - 13, { align: 'center' });

  // ==================== PAGE 2: EXECUTIVE SUMMARY ====================
  doc.addPage();
  yPos = 20;

  doc.setFontSize(24);
  doc.setTextColor(30, 41, 59);
  doc.setFont(undefined, 'bold');
  doc.text('Executive Summary', 20, yPos);
  yPos += 15;

  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0);
  doc.setFont(undefined, 'normal');

  // Company Overview Table
  doc.autoTable({
    startY: yPos,
    head: [['Company Information', 'Details']],
    body: [
      ['Company Name', pitchData?.companyName || pitchData?.company_name || 'N/A'],
      ['Industry', pitchData?.industry || 'N/A'],
      ['Stage', pitchData?.stage || pitchData?.currentStage || 'N/A'],
      ['Founded', pitchData?.foundedYear || 'N/A'],
      ['Team Size', pitchData?.teamSize || 'N/A'],
      ['Funding Target', pitchData?.fundingAmount ? `$${pitchData.fundingAmount}` : 'N/A'],
    ],
    theme: 'striped',
    headStyles: { fillColor: [79, 70, 229], textColor: 255 },
    margin: { left: 20, right: 20 },
  });

  yPos = doc.lastAutoTable.finalY + 20;

  // ==================== DETAILED ANALYSIS SECTIONS ====================
  
  if (analysisData.pros && analysisData.pros.length > 0) {
    addSection('✨ Key Strengths', analysisData.pros, [34, 197, 94]);
  }

  if (analysisData.cons && analysisData.cons.length > 0) {
    addSection('⚠️ Major Concerns', analysisData.cons, [239, 68, 68]);
  }

  if (analysisData.good_parts && analysisData.good_parts.length > 0) {
    addSection('👍 What\'s Being Done Well', analysisData.good_parts, [59, 130, 246]);
  }

  if (analysisData.bad_parts && analysisData.bad_parts.length > 0) {
    addSection('🔧 Areas Needing Improvement', analysisData.bad_parts, [249, 115, 22]);
  }

  // Risk Assessment
  if (analysisData.risk_assessment) {
    addSection('🛡️ Risk Assessment', analysisData.risk_assessment, [168, 85, 247]);
  }

  // Recommendations
  if (analysisData.recommendations && analysisData.recommendations.length > 0) {
    addSection('💡 Strategic Recommendations', analysisData.recommendations, [139, 92, 246]);
  }

  // ==================== FINAL PAGE: CONCLUSION ====================
  checkAddPage(80);
  
  doc.setFillColor(238, 242, 255);
  doc.roundedRect(14, yPos, pageWidth - 28, 60, 3, 3, 'F');
  
  doc.setFontSize(16);
  doc.setTextColor(79, 70, 229);
  doc.setFont(undefined, 'bold');
  doc.text('Final Recommendation', 20, yPos + 10);
  
  doc.setFontSize(11);
  doc.setTextColor(30, 41, 59);
  doc.setFont(undefined, 'normal');
  
  const finalText = analysisData.overall_verdict || 'Based on our comprehensive analysis, this investment opportunity shows potential. Please review all sections for detailed insights.';
  const finalLines = doc.splitTextToSize(finalText, pageWidth - 50);
  doc.text(finalLines, 20, yPos + 22);

  yPos += 70;
  
  // Signature section
  doc.setFontSize(9);
  doc.setTextColor(100, 116, 139);
  doc.text('_____________________________', 20, yPos + 20);
  doc.text('AI Investment Analyst', 20, yPos + 28);
  doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, yPos + 35);

  // Disclaimer
  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  const disclaimer = 'This report is generated by AI and should be used as a supplementary tool for investment decision-making. Always conduct thorough due diligence and consult with financial advisors before making investment decisions.';
  const disclaimerLines = doc.splitTextToSize(disclaimer, pageWidth - 40);
  doc.text(disclaimerLines, pageWidth / 2, pageHeight - 25, { align: 'center' });

  // Save the PDF
  const fileName = `Investment_Analysis_${(pitchData?.companyName || pitchData?.company_name || 'Report').replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
  doc.save(fileName);
  console.log('PDF saved successfully:', fileName);
  } catch (error) {
    console.error('PDF generation error:', error);
    alert(`Failed to generate PDF: ${error.message}`);
  }
};
