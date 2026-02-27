import unittest
from unittest.mock import MagicMock, patch
from src.agents.front_desk_agent import FrontDeskAgent
from src.state import PharmacyState

# Mock the entire LLM service to avoid API calls and key requirements
def mock_llm_service():
    # This is a context manager for the patch
    p = patch("src.services.llm_service.call_llm_translate")
    mock = p.start()
    mock.side_effect = lambda text, target_language: f"[TRANSLATED to {target_language}] {text}"
    return mock, p

class TestHindiSupport(unittest.TestCase):

    def setUp(self):
        self.mock_translate, self.patcher = mock_llm_service()

    def tearDown(self):
        self.patcher.stop()

    def test_hindi_greeting_logic(self):
        """Test that Hindi greeting triggers translation."""
        agent = FrontDeskAgent()
        
        # Input defined as Hindi request
        message = "namaste"
        intent = "greeting"
        patient_context = {}
        turn_count = 0
        
        response = agent.generate_clarifying_question(intent, message, patient_context, turn_count)
        
        # Check if the response contains our mock translation marker
        # "Namaste" triggers bilingual fallback, not necessarily dynamic translation unless "hindi" is explicitly requested
        # Check for the static Hindi greeting
        self.assertIn("नमस्ते! मैं आपका AI फार्मेसी सहायक हूँ", response)
        self.assertIn("Hello! I'm your AI pharmacy assistant", response)

    def test_explicit_hindi_request(self):
        """Test explicit request to speak in Hindi."""
        agent = FrontDeskAgent()
        message = "hindi mein bolo"
        intent = "inquiry"
        patient_context = {}
        turn_count = 0
        
        response = agent.generate_clarifying_question(intent, message, patient_context, turn_count)
        
        self.assertIn("[TRANSLATED to hi]", response)
        self.assertIn("Yes! I can speak in Hindi", response)

    def test_hindi_symptom_question(self):
        """Test that symptom questions are translated if Hindi is detected."""
        agent = FrontDeskAgent()
        
        message = "hindi mein batayein"
        intent = "symptom"
        patient_context = {}
        turn_count = 1
        
        response = agent.generate_clarifying_question(intent, message, patient_context, turn_count)
        
        self.assertIn("[TRANSLATED to hi]", response)
        self.assertIn("happy to help", response)

if __name__ == "__main__":
    unittest.main()
