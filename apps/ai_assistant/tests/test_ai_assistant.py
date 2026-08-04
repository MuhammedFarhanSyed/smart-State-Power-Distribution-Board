import unittest
from unittest.mock import patch
from apps.ai_assistant.services.prompt_builder import PromptBuilder
from apps.ai_assistant.services.fallback_service import FallbackService
from apps.ai_assistant.services.llm_client import LLMClient


class TestAIAssistant(unittest.TestCase):
    """
    Unit test suite for AI Assistant prompt building, provider abstraction, and deterministic fallbacks.
    """

    def setUp(self):
        self.sample_incident = {
            "ticket_id": "12345678-1234-5678-1234-567812345678",
            "asset_type": "span",
            "dt_id": "D-0112",
            "from_pole_id": "P-024431",
            "to_pole_id": "P-024432",
            "affected_poles_count": 4,
            "pincode": "560078",
            "confidence_score": 0.85,
            "confidence_reasons": ["Verified topology", "Direct power_lost packet"],
            "status": "detected",
            "latitude": 12.9678,
            "longitude": 77.5951
        }

    def test_prompt_builder_structure(self):
        """Verifies structured system and user prompt generation."""
        sys_prompt, user_prompt = PromptBuilder.build_summary_prompt(self.sample_incident)
        self.assertIn("strictly operator decision support", sys_prompt)
        self.assertIn("D-0112", user_prompt)
        self.assertIn("P-024431", user_prompt)
        self.assertIn("JSON", user_prompt)

    def test_fallback_service_execution(self):
        """Verifies deterministic fallback generation when LLM fails or is in mock mode."""
        summary = FallbackService.get_summary_fallback(self.sample_incident)
        self.assertTrue(summary.get('is_fallback'))
        self.assertIn("P-024431", summary['summary'])
        self.assertIn("P-024432", summary['summary'])

        rec = FallbackService.get_recommendation_fallback(self.sample_incident)
        self.assertTrue(rec.get('is_fallback'))
        self.assertGreaterEqual(rec['recommended_crew_size'], 2)
        self.assertIn("repair kit", rec['required_equipment'][0].lower())

    def test_llm_client_mock_provider(self):
        """Verifies that LLMClient safely returns fallback JSON when provider is mock."""
        fallback = FallbackService.get_summary_fallback(self.sample_incident)
        sys_p, user_p = PromptBuilder.build_summary_prompt(self.sample_incident)

        result = LLMClient.generate_json_response(sys_p, user_p, fallback)
        self.assertEqual(result, fallback)
        self.assertTrue(result['is_fallback'])


if __name__ == '__main__':
    unittest.main()
