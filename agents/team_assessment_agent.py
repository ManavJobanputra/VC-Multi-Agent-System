import json
import logging
import re
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from backend.mistral_client import MistralClient

logger = logging.getLogger(__name__)

# Research-backed signals this agent scores against (not demographic factors
# like age/gender, which some VC studies correlate with outcomes but which
# have no place in an automated scoring rubric):
#
# - First Round Capital's "10 Year Project" (300 companies, ~600 founders):
#   multi-founder teams outperformed solo founders by 163%; a technical
#   co-founder correlated with 230% better outcomes for enterprise startups,
#   but no-technical-cofounder consumer teams outperformed mixed teams by
#   31% (technical cofounders are overrated for consumer products); founders
#   with experience at major tech companies performed 160% better.
# - Standard VC due-diligence practice evaluates founders at two levels:
#   individual (domain expertise, founder-market fit, prior track record)
#   and group (complementary skills, role clarity, team dynamics).
# - Team-intelligence platforms (e.g. Harmonic.ai) build structured founder
#   profiles - education, career history, prior startups/exits - rather
#   than reading unstructured form fields, since most pitch data doesn't
#   arrive in neat structured fields.


class TeamAssessmentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Team Assessment Agent",
            description="Founding team evaluation, execution capability, and hiring-gap analyst"
        )
        self.mistral_client = MistralClient()

    # ------------------------------------------------------------------
    # LLM Extraction: pull structured founder/team facts out of free-text
    # pitch content. Real pitches don't arrive with a "teamSize" form
    # field - the team composition has to be read out of the narrative,
    # the same way a human analyst would.
    # ------------------------------------------------------------------
    def _extract_team_data_with_llm(self, pitch_text: str, founder_name: str) -> Dict[str, Any]:
        prompt = f"""
You are an expert VC analyst extracting founding-team facts from a startup pitch.

Extract ONLY what is explicitly stated or clearly implied in the pitch text below.
Use "N/A" or an empty list if something isn't mentioned - do not invent details.

Named founder (may or may not be the only one): {founder_name or "N/A"}

Return ONLY valid JSON with this shape:
{{
  "founders": [
    {{
      "name": "string",
      "role": "string (e.g. CEO, CTO) or N/A",
      "is_technical": true/false/null,
      "prior_startup_experience": "string describing prior founding/exec experience, or N/A",
      "notable_affiliations": "string - prior employers, schools, publications, patents, or N/A"
    }}
  ],
  "team_size_mentioned": "number as string, or N/A if not stated",
  "roles_covered_by_team": ["list of functions the team explicitly has covered, e.g. engineering, product"],
  "roles_founders_are_personally_covering": ["list of functions founders say THEY do themselves, e.g. sales, marketing - a signal of gaps"],
  "hiring_plans_mentioned": "string describing any hiring plans stated, or N/A"
}}

Startup Pitch:
{pitch_text}
"""
        messages = [
            {"role": "system", "content": "You extract structured founding-team data from startup pitches. Never invent facts not present in the text."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.mistral_client.call_openrouter_api(messages, temperature=0.1, max_tokens=800)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in LLM response")
            return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Team data extraction failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # LLM Judgment: founder-market fit is inherently qualitative - does
    # this specific team's background give them real insight into this
    # specific problem? That's not something a lookup table can answer.
    # ------------------------------------------------------------------
    def _assess_founder_market_fit(self, pitch_text: str, extracted: Dict[str, Any]) -> str:
        prompt = f"""
You are a sharp VC partner assessing founder-market fit: does this team have
genuine, differentiated insight into the problem they're solving, or are
they generalists picking a trendy space?

Founding team facts:
{json.dumps(extracted, indent=2)}

Full pitch for context:
{pitch_text}

In 2-4 sentences, give a direct, candid assessment of founder-market fit.
Cite specific facts from the team's background. If the pitch gives you
nothing to work with (no real founder background mentioned), say so plainly
instead of praising the team anyway.
"""
        return self.mistral_client.call_openrouter_api(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )

    # ------------------------------------------------------------------
    # Deterministic scoring on top of the extracted facts, grounded in
    # First Round Capital's 10-Year Project findings.
    # ------------------------------------------------------------------
    def _score_team_composition(self, extracted: Dict[str, Any], industry: str) -> Dict[str, Any]:
        founders = extracted.get("founders") or []
        founder_count = len(founders)
        has_technical_cofounder = any(f.get("is_technical") is True for f in founders)
        is_consumer = any(kw in industry.lower() for kw in ["consumer", "d2c", "social", "media"])

        signals = []
        concerns = []

        if founder_count >= 2:
            signals.append(
                "Multiple founders (First Round Capital's 10-Year Project found "
                "multi-founder teams outperform solo founders by 163%)."
            )
        elif founder_count == 1:
            concerns.append(
                "Solo founder - historically a headwind (First Round Capital found "
                "teams with 2+ founders outperform solo founders by 163%); "
                "not disqualifying, but worth probing on bandwidth and bus-factor risk."
            )
        else:
            concerns.append("Pitch doesn't clearly describe who the founders are.")

        if has_technical_cofounder and not is_consumer:
            signals.append(
                "Has a technical co-founder, which First Round's data ties to "
                "230% better outcomes for enterprise/B2B startups specifically."
            )
        elif not has_technical_cofounder and not is_consumer and founder_count > 0:
            concerns.append(
                "No technical co-founder identified - First Round's data found this "
                "matters more for enterprise/B2B than consumer products, and this "
                "pitch isn't a consumer play."
            )

        notable_bg = [f for f in founders if f.get("notable_affiliations") not in (None, "", "N/A")]
        if notable_bg:
            signals.append(
                f"{len(notable_bg)} founder(s) have notable prior affiliations mentioned "
                "(prior employers/startups correlate with credibility and network access)."
            )

        roles_covered = set(extracted.get("roles_covered_by_team") or [])
        roles_founder_covering = set(extracted.get("roles_founders_are_personally_covering") or [])
        core_functions = {"sales", "marketing", "engineering", "product", "customer success", "operations"}
        gaps = core_functions - roles_covered - roles_founder_covering
        # Roles founders say they personally cover are real gaps in a scaling sense,
        # even though someone is nominally doing them.
        stretched_thin = roles_founder_covering & {"sales", "marketing", "customer success"}

        if stretched_thin:
            concerns.append(
                f"Founders are personally covering {', '.join(sorted(stretched_thin))} - "
                "common pre-seed reality, but a real bottleneck at the scale this pitch describes."
            )

        return {
            "founder_count": founder_count,
            "has_technical_cofounder": has_technical_cofounder,
            "signals": signals or ["Not enough team information in the pitch to identify positive signals."],
            "concerns": concerns or ["No major team composition concerns identified from available information."],
            "functional_gaps": sorted(gaps),
            "founders_personally_stretched_across": sorted(stretched_thin),
        }

    # ------------------------------------------------------------------
    # Main Analysis
    # ------------------------------------------------------------------
    def assess_team(self, pitch_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("TeamAssessmentAgent: Starting analysis")

        pitch_text = pitch_data.get("content", "")
        founder_name = pitch_data.get("founder_name", "")
        industry = pitch_data.get("industry", "")

        if not pitch_text:
            return {"status": "error", "message": "No pitch content provided."}

        extracted = self._extract_team_data_with_llm(pitch_text, founder_name)
        if not extracted:
            return {
                "status": "incomplete",
                "message": "Could not extract team information from pitch content.",
            }

        composition = self._score_team_composition(extracted, industry)
        founder_market_fit = self._assess_founder_market_fit(pitch_text, extracted)

        # Functional gaps (e.g. no dedicated marketing/ops hire) are normal at
        # pre-seed/seed and shouldn't alone drive risk up - only the scored
        # concerns (solo founder, no technical co-founder where it matters,
        # founders stretched across core functions) should.
        num_concerns = len(composition["concerns"])
        risk_level = "High" if num_concerns >= 2 else ("Medium" if num_concerns == 1 else "Low")

        return {
            "title": "Team Assessment Report",
            "extracted_team": extracted,
            "founder_market_fit": founder_market_fit,
            "team_composition": composition,
            "team_risk_summary": {
                "overall_risk": risk_level,
                "key_concerns": composition["concerns"],
                "functional_gaps": composition["functional_gaps"],
            },
        }

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return self.assess_team(data)
