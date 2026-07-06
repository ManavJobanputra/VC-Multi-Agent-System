import jsPDF from 'jspdf';
import { autoTable } from 'jspdf-autotable';

export const generatePDFReport = (analysisData, pitchData) => {
  try {
    if (!analysisData) {
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

    // Section title bar shared by every section renderer below
    const addSectionTitle = (title, color) => {
      checkAddPage(30);
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
    };

    // Plain paragraph, always coerced to a string - the crash this
    // replaces came from passing objects (e.g. a risk_assessment entry)
    // straight into splitTextToSize, which requires a string.
    const addParagraph = (text, x = 20, width = pageWidth - 40) => {
      const lines = doc.splitTextToSize(String(text ?? ''), width);
      doc.text(lines, x, yPos);
      yPos += lines.length * 5;
    };

    // Numbered list of plain strings (pros, cons, good_parts, bad_parts, recommendations)
    const addListSection = (title, items, color) => {
      if (!items || items.length === 0) return;
      addSectionTitle(title, color);
      items.forEach((item, idx) => {
        checkAddPage(15);
        const lines = doc.splitTextToSize(`${idx + 1}. ${String(item)}`, pageWidth - 50);
        doc.text(lines, 25, yPos);
        yPos += lines.length * 5 + 5;
      });
      yPos += 10;
    };

    // Risk assessment: each entry is now {severity, reasoning, confidence}
    // rather than a plain string.
    const addRiskSection = (riskAssessment, color) => {
      if (!riskAssessment) return;
      addSectionTitle('Risk Assessment', color);
      Object.entries(riskAssessment).forEach(([key, value]) => {
        checkAddPage(20);
        const isObject = value && typeof value === 'object';
        const severity = isObject ? value.severity : String(value).split(':')[0];
        const reasoning = isObject ? value.reasoning : String(value);
        const confidence = isObject ? value.confidence : null;

        doc.setFont(undefined, 'bold');
        const label = `${key.replace(/_/g, ' ').toUpperCase()}: ${severity || 'N/A'}`;
        doc.text(label, 20, yPos);
        yPos += 6;
        doc.setFont(undefined, 'normal');
        addParagraph(reasoning, 25, pageWidth - 50);
        if (confidence !== null && confidence !== undefined) {
          yPos += 2;
          doc.setFontSize(8);
          doc.setTextColor(120, 120, 120);
          doc.text(`Confidence: ${confidence}%`, 25, yPos);
          doc.setFontSize(10);
          doc.setTextColor(0, 0, 0);
          yPos += 5;
        }
        yPos += 5;
      });
      yPos += 10;
    };

    const addContradictionsSection = (contradictions, color) => {
      if (!contradictions || contradictions.length === 0) return;
      addSectionTitle('Contradictions Raised & Resolved', color);
      contradictions.forEach((c) => {
        checkAddPage(30);
        doc.setFont(undefined, 'bold');
        doc.text(`${c.topic || 'Untitled'} - ${c.resolved ? 'Resolved' : 'Unresolved'}`, 20, yPos);
        yPos += 6;
        doc.setFont(undefined, 'normal');
        addParagraph(`Raised: ${c.concern_raised || 'N/A'}`, 25, pageWidth - 50);
        yPos += 2;
        addParagraph(`${c.resolved ? 'Resolution' : 'Status'}: ${c.resolution || 'N/A'}`, 25, pageWidth - 50);
        yPos += 8;
      });
      yPos += 10;
    };

    const addAgentAssessmentSection = (agentAssessment, color) => {
      const entries = agentAssessment ? Object.entries(agentAssessment) : [];
      if (entries.length === 0) return;
      addSectionTitle('Specialist Panel Read', color);
      entries.forEach(([key, agent]) => {
        checkAddPage(20);
        doc.setFont(undefined, 'bold');
        doc.text(`${key.replace(/_/g, ' ').toUpperCase()}: ${agent.score ?? 'N/A'}/10`, 20, yPos);
        yPos += 6;
        doc.setFont(undefined, 'normal');
        addParagraph(agent.summary || 'N/A', 25, pageWidth - 50);
        yPos += 8;
      });
      yPos += 10;
    };

    const addAnswerQualitySection = (answerQuality, color) => {
      if (!answerQuality || answerQuality.length === 0) return;
      addSectionTitle('Answer-by-Answer Quality', color);
      answerQuality.forEach((qa) => {
        checkAddPage(20);
        doc.setFont(undefined, 'bold');
        const stars = '*'.repeat(qa.rating || 0) + '-'.repeat(5 - (qa.rating || 0));
        addParagraph(`[${stars}] ${qa.question || 'N/A'}`, 20, pageWidth - 40);
        yPos += 2;
        doc.setFont(undefined, 'normal');
        addParagraph(qa.reason || 'N/A', 25, pageWidth - 50);
        yPos += 6;
      });
      yPos += 10;
    };

    const addRecommendationSection = (recommendation, color) => {
      if (!recommendation) return;
      addSectionTitle('Recommendation', color);
      doc.setFont(undefined, 'bold');
      doc.text(`Decision: ${recommendation.decision || 'N/A'} (Confidence: ${recommendation.confidence ?? 'N/A'}%)`, 20, yPos);
      yPos += 10;
      doc.setFont(undefined, 'normal');

      const addSubList = (label, items) => {
        if (!items || items.length === 0) return;
        checkAddPage(15);
        doc.setFont(undefined, 'bold');
        doc.text(label, 20, yPos);
        yPos += 6;
        doc.setFont(undefined, 'normal');
        items.forEach((item) => {
          checkAddPage(12);
          addParagraph(`- ${item}`, 25, pageWidth - 50);
          yPos += 3;
        });
        yPos += 6;
      };

      addSubList('Reasons to Invest', recommendation.reasons_to_invest);
      addSubList('Reasons Not to Invest', recommendation.reasons_not_to_invest);
      addSubList('Open Questions', recommendation.open_questions);
      yPos += 4;
    };

    // ==================== PAGE 1: COVER PAGE ====================

    doc.setFillColor(238, 242, 255);
    doc.rect(0, 0, pageWidth, pageHeight, 'F');

    doc.setFillColor(79, 70, 229);
    doc.circle(pageWidth / 2, 60, 20, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(24);
    doc.text('AI', pageWidth / 2, 63, { align: 'center' });

    doc.setTextColor(30, 41, 59);
    doc.setFontSize(32);
    doc.setFont(undefined, 'bold');
    doc.text('Investment Analysis Report', pageWidth / 2, 100, { align: 'center' });

    doc.setFontSize(24);
    doc.setTextColor(79, 70, 229);
    doc.text(pitchData?.companyName || pitchData?.company_name || 'Startup', pageWidth / 2, 120, { align: 'center' });

    doc.setFontSize(14);
    doc.setTextColor(100, 116, 139);
    doc.setFont(undefined, 'normal');
    doc.text(`${pitchData?.industry || 'Technology'} | ${pitchData?.stage || pitchData?.currentStage || 'Seed Stage'}`, pageWidth / 2, 135, { align: 'center' });

    doc.setFillColor(79, 70, 229);
    doc.roundedRect(pageWidth / 2 - 40, 160, 80, 60, 5, 5, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(48);
    doc.setFont(undefined, 'bold');
    doc.text(`${analysisData.investment_score ?? 'N/A'}`, pageWidth / 2, 190, { align: 'center' });
    doc.setFontSize(12);
    doc.text('INVESTMENT SCORE', pageWidth / 2, 210, { align: 'center' });

    if (analysisData.overall_verdict) {
      doc.setFontSize(11);
      doc.setTextColor(30, 41, 59);
      const verdictLines = doc.splitTextToSize(String(analysisData.overall_verdict), pageWidth - 60);
      doc.text(verdictLines, pageWidth / 2, 240, { align: 'center' });
    }

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

    autoTable(doc, {
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

    if (analysisData.investment_thesis) {
      addSectionTitle('Investment Thesis', [79, 70, 229]);
      addParagraph(analysisData.investment_thesis);
      yPos += 10;
    }

    // ==================== DETAILED ANALYSIS SECTIONS ====================

    addContradictionsSection(analysisData.contradictions, [234, 179, 8]);
    addListSection('Key Strengths', analysisData.pros, [34, 197, 94]);
    addListSection('Major Concerns', analysisData.cons, [239, 68, 68]);
    addListSection("What's Being Done Well", analysisData.good_parts, [59, 130, 246]);
    addListSection('Areas Needing Improvement', analysisData.bad_parts, [249, 115, 22]);
    addRiskSection(analysisData.risk_assessment, [168, 85, 247]);
    addAgentAssessmentSection(analysisData.agent_assessment, [14, 165, 233]);
    addAnswerQualitySection(analysisData.answer_quality, [236, 72, 153]);
    addRecommendationSection(analysisData.recommendation, [79, 70, 229]);
    addListSection('Next Steps', analysisData.recommendations, [139, 92, 246]);

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
    const finalLines = doc.splitTextToSize(String(finalText), pageWidth - 50);
    doc.text(finalLines, 20, yPos + 22);

    yPos += 70;

    doc.setFontSize(9);
    doc.setTextColor(100, 116, 139);
    doc.text('_____________________________', 20, yPos + 20);
    doc.text('AI Investment Analyst', 20, yPos + 28);
    doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, yPos + 35);

    doc.setFontSize(8);
    doc.setTextColor(148, 163, 184);
    const disclaimer = 'This report is generated by AI and should be used as a supplementary tool for investment decision-making. Always conduct thorough due diligence and consult with financial advisors before making investment decisions.';
    const disclaimerLines = doc.splitTextToSize(disclaimer, pageWidth - 40);
    doc.text(disclaimerLines, pageWidth / 2, pageHeight - 25, { align: 'center' });

    const fileName = `Investment_Analysis_${(pitchData?.companyName || pitchData?.company_name || 'Report').replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
  } catch (error) {
    console.error('PDF generation error:', error);
    alert(`Failed to generate PDF: ${error.message}`);
  }
};
