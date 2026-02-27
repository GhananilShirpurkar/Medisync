import unittest
from unittest.mock import patch, MagicMock
from src.agents.severity_scorer import assess_severity
from src.state import PharmacyState

class TestSeverityIntegration(unittest.TestCase):

    @patch('src.agents.severity_scorer._get_ai_severity_score')
    @patch('src.agents.severity_scorer.logger')
    def test_high_severity_override(self, mock_logger, mock_get_ai):
        # Mock AI to return low severity, but we will test emergency override logic if implemented
        # However, assess_severity uses _check_emergency_red_flags which is deterministic
        
        # Let's mock the whole assess_severity if we want to test integration into medical_validator, 
        # but here we are assessing severity logic itself being called correctly.
        
        # Actually, let's test the assess_severity function itself with mocks.
        
        # Case 1: High Severity Symptom (Checst Pain)
        # We need to ensure that assess_severity correctly identifies it.
        # But assess_severity relies on _get_ai_severity_score which calls LLM.
        # We must mock _get_ai_severity_score to return a high score.
        
        mock_get_ai.return_value = {
            "severity_score": 8,
            "risk_level": "high",
            "red_flags_detected": [],
            "reasoning": "High pain reported",
            "recommended_action": "doctor_referral"
        }
        
        result = assess_severity("Chest pain", {})
        
        self.assertEqual(result['severity_score'], 9)
        self.assertEqual(result['risk_level'], "critical")
        self.assertEqual(result['route'], "EMERGENCY_ALERT")

    @patch('src.agents.severity_scorer._get_ai_severity_score')
    def test_low_severity(self, mock_get_ai):
        mock_get_ai.return_value = {
            "severity_score": 2,
            "risk_level": "low",
            "red_flags_detected": [],
            "reasoning": "Mild headache",
            "recommended_action": "otc"
        }
        
        result = assess_severity("Mild headache", {})
        
        self.assertEqual(result['severity_score'], 2)
        self.assertEqual(result['route'], "OTC_RECOMMENDATION")

if __name__ == '__main__':
    unittest.main()
