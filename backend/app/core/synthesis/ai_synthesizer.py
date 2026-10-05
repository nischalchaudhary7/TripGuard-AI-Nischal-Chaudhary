import asyncio
import json
from datetime import date
from typing import Any

from app.config import Settings
from app.core.models.assessment import RiskResult, Synthesis
from app.core.models.airport import Airport
from app.core.models.signal import Signal
from app.core.synthesis.citations import valid_signal_ids
from pydantic import BaseModel, Field


class GeminiRiskClaim(BaseModel):
    description: str = Field(description="A concise risk claim based only on supplied signals.")
    signal_ids: list[str] = Field(description="One or more valid Signal IDs supporting this risk claim.")


class GeminiSynthesisOutput(BaseModel):
    concise_verdict: str
    main_risks: list[GeminiRiskClaim]
    recommended_actions: list[str]
    confidence_explanation: str
    caveats: list[str]


class AISynthesizer:
    def __init__(self, settings: Settings, client=None, gemini_client=None):
        self.settings = settings
        self.client = client
        self.gemini_client = gemini_client

    async def synthesize(
        self,
        risk: RiskResult,
        signals: list[Signal],
        caveats: list[str],
        *,
        origin: Airport | None = None,
        destination: Airport | None = None,
        travel_date: date | None = None,
        confidence: float | None = None,
    ) -> Synthesis:
        provider = self.settings.ai_provider.strip().lower()
        if provider == "gemini" and self.settings.gemini_api_key:
            try:
                return await self._gemini(risk, signals, caveats, origin, destination, travel_date, confidence)
            except Exception:
                return self._fallback(risk, signals, caveats, confidence)
        if provider == "openai" and self.settings.openai_api_key and self.client:
            try:
                return await self._openai(risk, signals, caveats)
            except Exception:
                return self._fallback(risk, signals, caveats, confidence)
        return self._fallback(risk, signals, caveats, confidence)

    async def _gemini(
        self,
        risk: RiskResult,
        signals: list[Signal],
        caveats: list[str],
        origin: Airport | None,
        destination: Airport | None,
        travel_date: date | None,
        confidence: float | None,
    ) -> Synthesis:
        output = await asyncio.to_thread(
            self._call_gemini_sync,
            {
                "trip": {
                    "origin": origin.model_dump(mode="json") if origin else None,
                    "destination": destination.model_dump(mode="json") if destination else None,
                    "travel_date": travel_date.isoformat() if travel_date else None,
                },
                "risk": {"score": risk.score, "level": risk.level, "verdict": risk.verdict},
                "confidence": confidence,
                "caveats": caveats,
                "signals": [signal.model_dump(mode="json") for signal in signals],
            }
        )
        return self._validate_gemini_output(output, signals, caveats)

    def _call_gemini_sync(self, payload: dict[str, Any]) -> GeminiSynthesisOutput:
        if self.gemini_client is None:
            from google import genai

            self.gemini_client = genai.Client(api_key=self.settings.gemini_api_key)

        prompt = (
            "You are TripGuard AI's synthesis layer. Use only the supplied normalized signals and deterministic risk data. "
            "Do not calculate or alter scores, risk levels, signal severity, source evidence, or source timestamps. "
            "Do not invent cancellations, delays, weather, closures, FAA restrictions, strikes, incidents, or disruptions. "
            "Every risk claim must include one or more Signal IDs from the supplied signals. "
            "If no supplied signal supports a claim, omit the claim. Explain uncertainty clearly.\n\n"
            f"TripGuard input:\n{json.dumps(payload)}"
        )
        response_format = {
            "type": "text",
            "mime_type": "application/json",
            "schema": GeminiSynthesisOutput.model_json_schema(),
        }
        if hasattr(self.gemini_client, "interactions"):
            response = self.gemini_client.interactions.create(
                model=self.settings.gemini_model,
                input=prompt,
                response_format=response_format,
            )
            return GeminiSynthesisOutput.model_validate_json(response.output_text)

        from google.genai import types

        response = self.gemini_client.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiSynthesisOutput,
            ),
        )
        if getattr(response, "parsed", None):
            return response.parsed
        return GeminiSynthesisOutput.model_validate_json(response.text)

    def _validate_gemini_output(self, output: GeminiSynthesisOutput, signals: list[Signal], fallback_caveats: list[str]) -> Synthesis:
        allowed = {signal.id for signal in signals}
        main_risks: list[str] = []
        requested_ids: list[str] = []
        for claim in output.main_risks:
            if not claim.signal_ids and signals:
                raise ValueError("Gemini risk claim did not cite a signal ID.")
            valid_ids = valid_signal_ids(signals, claim.signal_ids)
            if valid_ids != claim.signal_ids:
                raise ValueError("Gemini synthesis cited an unknown signal ID.")
            if signals and not set(valid_ids).issubset(allowed):
                raise ValueError("Gemini synthesis cited an invalid signal ID.")
            requested_ids.extend(valid_ids)
            citation = ", ".join(valid_ids)
            main_risks.append(f"{claim.description} [{citation}]" if citation else claim.description)

        unique_ids = list(dict.fromkeys(requested_ids))
        return Synthesis(
            summary=output.concise_verdict,
            main_risks=main_risks or ["No active disruption signals from available sources."],
            recommended_actions=output.recommended_actions,
            confidence_explanation=output.confidence_explanation,
            caveats=output.caveats or fallback_caveats,
            cited_signal_ids=unique_ids,
            provider="gemini",
            fallback_used=False,
        )

    async def _openai(self, risk: RiskResult, signals: list[Signal], caveats: list[str]) -> Synthesis:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["summary", "main_risks", "recommended_actions", "cited_signal_ids"],
            "properties": {
                "summary": {"type": "string"},
                "main_risks": {"type": "array", "items": {"type": "string"}},
                "recommended_actions": {"type": "array", "items": {"type": "string"}},
                "cited_signal_ids": {"type": "array", "items": {"type": "string"}},
            },
        }
        payload = {
            "model": self.settings.openai_model,
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You synthesize normalized travel disruption signals. Do not invent facts, risks, or sources. "
                        "Every risk claim must cite only signal IDs provided in the input. Mention uncertainty explicitly."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "risk": risk.model_dump(),
                            "signals": [signal.model_dump(mode="json") for signal in signals],
                            "caveats": caveats,
                        }
                    ),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "tripguard_synthesis",
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        response = await self.client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {self.settings.openai_api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = json.loads(self._extract_output_text(response.json()))
        requested_ids = data.get("cited_signal_ids", [])
        cited_ids = valid_signal_ids(signals, requested_ids)
        if requested_ids != cited_ids:
            raise ValueError("OpenAI synthesis cited an unknown signal ID.")
        if signals and any(not any(signal_id in risk for signal_id in cited_ids) for risk in data["main_risks"]):
            raise ValueError("OpenAI synthesis included a risk claim without a valid signal citation.")
        return Synthesis(
            summary=data["summary"],
            main_risks=data["main_risks"],
            recommended_actions=data["recommended_actions"],
            cited_signal_ids=cited_ids,
            provider="openai",
            fallback_used=False,
        )

    def _extract_output_text(self, response: dict) -> str:
        if response.get("output_text"):
            return response["output_text"]
        for item in response.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content.get("text", "")
        raise ValueError("OpenAI response did not include output text.")

    def _fallback(self, risk: RiskResult, signals: list[Signal], caveats: list[str], confidence: float | None = None) -> Synthesis:
        top = sorted(signals, key=lambda item: item.severity, reverse=True)[:4]
        if top:
            summary = f"{risk.level} risk ({risk.score}/100): " + "; ".join(signal.summary for signal in top[:2])
            main_risks = [f"{signal.summary} [{signal.id}]" for signal in top]
            cited = [signal.id for signal in top]
        else:
            summary = f"{risk.level} risk ({risk.score}/100): no disruption signals were found."
            main_risks = ["No active disruption signals from available sources."]
            cited = []

        actions = {
            "LOW": ["Proceed normally.", "Check airline notifications before leaving for the airport."],
            "MODERATE": ["Monitor airline and airport updates.", "Allow extra time and keep alternate flights in mind."],
            "HIGH": ["Confirm flight status before traveling.", "Consider backup routing or flexible rebooking options."],
            "SEVERE": ["Contact the airline before heading to the airport.", "Prepare for delays, cancellations, or rerouting."],
        }[risk.level]
        if caveats:
            actions.append("Review uncertainty notes before relying on live operational data.")
        confidence_text = (
            f"Confidence is {round(confidence * 100)}% based on source coverage, signal freshness, and trip horizon."
            if confidence is not None
            else "Confidence is based on source coverage, signal freshness, and trip horizon."
        )
        return Synthesis(
            summary=summary,
            main_risks=main_risks,
            recommended_actions=actions,
            confidence_explanation=confidence_text,
            caveats=caveats,
            cited_signal_ids=cited,
            provider="deterministic",
            fallback_used=True,
        )
