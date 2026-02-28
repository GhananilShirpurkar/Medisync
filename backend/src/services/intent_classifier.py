"""
SEMANTIC INTENT CLASSIFIER
===========================
Lightweight intent classification using sentence transformers.

Uses all-MiniLM-L6-v2 (80MB) - optimized for CPU and low RAM.
Also provides semantic medicine name extraction from free-form user messages.
"""

from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
import threading


class IntentClassifier:
    """
    Semantic intent classifier using sentence transformers.

    Model: all-MiniLM-L6-v2 (80MB, fast on CPU)
    """

    def __init__(self):
        """Initialize the classifier with lightweight model."""
        print("Loading intent classifier (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Define intent examples for semantic matching
        # More diverse phrasings reduce misclassification
        self.intent_examples = {
            "symptom": [
                # Direct symptom statements
                "I have a headache",
                "I'm feeling feverish",
                "My stomach hurts",
                "I have a cold and cough",
                "I'm experiencing pain",
                "I feel nauseous",
                "I have body aches",
                "I'm dizzy",
                "I have a sore throat",
                "I have a runny nose",
                "I feel weak and tired",
                "I have joint pain",
                "My back is hurting",
                "I have chest congestion",
                "I have a skin rash",
                "I'm having trouble sleeping",
                "I have an upset stomach",
                "I have diarrhea",
                "I feel feverish and have chills",
                "my head is killing me",
                "I feel terrible",
                "I'm not feeling well",
                # Medicine-for-symptom queries
                "what medicines are available for headache",
                "tell me medicines for fever",
                "show me drugs for cold",
                "medicines in stock for pain",
                "I want medicine for headache",
                "what medicines should I take for fever",
                "what should I take for headache",
                "which medicine is good for cold",
                "what can I take for stomach pain",
                "suggest medicine for fever",
                "recommend something for headache",
                "what helps with fever",
                "what is good for a cold",
                "medicine for body pain",
                "something for my sore throat",
                "what do you have for allergies",
                "anything for nausea",
                # Hinglish / Hindi-influenced
                "sir mujhe bukhar hai",
                "mujhe sar dard ho raha hai",
                "pet mein dard hai",
                "khansi aur zukam ke liye kya lun",
            ],
            "known_medicine": [
                # Direct requests
                "I need Paracetamol",
                "Do you have Ibuprofen?",
                "I want Aspirin",
                "Can I get Crocin?",
                "I'm looking for Dolo 650",
                "Give me Paracetamol",
                "I need some Aspirin tablets",
                "Do you stock Cetirizine?",
                "Do you have Diclofenac?",
                "Is Paracetamol available?",
                "Can you give me Aspirin?",
                "I want to buy Ibuprofen",
                "Do you sell Crocin?",
                "I'm looking for Paracetamol",
                "Give me some Aspirin",
                "I need Ibuprofen tablets",
                # Information queries about a specific medicine
                "What is Paracetamol used for?",
                "Tell me about Aspirin",
                "What does Ibuprofen do?",
                "How does Paracetamol work?",
                "What are the uses of Aspirin?",
                "Information about Paracetamol",
                "side effects of Ibuprofen",
                "dosage of Paracetamol",
                "can I take Aspirin with food",
                # Natural / indirect phrasing
                "do you have something like ibuprofen",
                "I usually take Crocin for headaches",
                "my doctor prescribed Amoxicillin",
                "looking for an antibiotic",
                "need an antihistamine",
                "do you carry Metformin",
                "I take Atorvastatin daily, do you have it",
                "Azithromycin please",
            ],
            "refill": [
                "I need to refill my prescription",
                "I want to refill my diabetes medication",
                "Can I refill my previous order?",
                "I need a refill",
                "Refill my blood pressure medicine",
                "same as last time",
                "order the same medicines again",
                "my monthly medicines",
                "reorder my prescription",
            ],
            "prescription_upload": [
                "I have a prescription",
                "Can I upload my prescription?",
                "I want to upload a prescription image",
                "I have a doctor's prescription",
                "Can you process my prescription?",
                "doctor gave me this",
                "here is my medicine slip",
                "I want to show you my prescription",
                "read this prescription",
                "scan my prescription",
                "I have a photo of my prescription",
            ],
            "greeting": [
                "Hello",
                "Hi there",
                "Good morning",
                "Hey",
                "Namaste",
                "Good evening",
                "Hi",
            ],
            "generic_help": [
                "I need help",
                "Can you help me?",
                "I want medicines",
                "I need medication",
                "What can you do?",
                "How does this work?",
                "help me",
            ],
        }

        # Pre-compute embeddings for all examples
        print("Computing intent embeddings...")
        self.intent_embeddings = {}
        for intent, examples in self.intent_examples.items():
            embeddings = self.model.encode(examples, convert_to_numpy=True)
            self.intent_embeddings[intent] = embeddings

        # Medicine name embeddings — lazy loaded on first use
        self._medicine_name_embeddings: Optional[np.ndarray] = None
        self._medicine_names: Optional[List[str]] = None

        print("✅ Intent classifier ready!")

    def classify(self, message: str, threshold: float = 0.35) -> Dict:
        """
        Classify user intent using semantic similarity.

        Args:
            message: User message
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            Dict with intent, confidence, and reasoning
        """
        # Encode user message
        message_embedding = self.model.encode([message], convert_to_numpy=True)[0]

        # Calculate similarity with each intent
        intent_scores = {}

        for intent, embeddings in self.intent_embeddings.items():
            # Calculate cosine similarity with all examples
            similarities = np.dot(embeddings, message_embedding) / (
                np.linalg.norm(embeddings, axis=1) * np.linalg.norm(message_embedding)
            )

            # Use max similarity as intent score
            max_similarity = float(np.max(similarities))
            intent_scores[intent] = max_similarity

        # Get best intent
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[best_intent]

        # Map generic intents
        if best_intent == "greeting":
            return {
                "intent": "greeting",
                "confidence": confidence,
                "reasoning": "User is greeting",
            }

        if best_intent == "generic_help":
            return {
                "intent": "generic_help",
                "confidence": confidence,
                "reasoning": "Generic help request",
            }

        # Check if confidence is too low
        if confidence < threshold:
            return {
                "intent": "symptom",  # Default to symptom
                "confidence": confidence,
                "reasoning": f"Low confidence ({confidence:.2f}) - defaulting to symptom",
                "needs_clarification": True,
            }

        return {
            "intent": best_intent,
            "confidence": confidence,
            "reasoning": f"Semantic match with {best_intent} examples (confidence: {confidence:.2f})",
        }

    def get_top_intents(self, message: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Get top K intents with their confidence scores.

        Args:
            message: User message
            top_k: Number of top intents to return

        Returns:
            List of (intent, confidence) tuples
        """
        message_embedding = self.model.encode([message], convert_to_numpy=True)[0]

        intent_scores = {}
        for intent, embeddings in self.intent_embeddings.items():
            similarities = np.dot(embeddings, message_embedding) / (
                np.linalg.norm(embeddings, axis=1) * np.linalg.norm(message_embedding)
            )
            intent_scores[intent] = float(np.max(similarities))

        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_intents[:top_k]

    def _load_medicine_embeddings(self) -> bool:
        """
        Lazily load and cache medicine name embeddings from the database.

        Returns:
            True if loaded successfully, False otherwise
        """
        if self._medicine_names is not None:
            return True  # Already loaded

        try:
            from src.db_config import get_db_context
            from src.models import Medicine

            with get_db_context() as db:
                medicines = db.query(Medicine.name).all()
                self._medicine_names = [m.name for m in medicines]

            if not self._medicine_names:
                return False

            print(f"Computing embeddings for {len(self._medicine_names)} medicines...")
            self._medicine_name_embeddings = self.model.encode(
                self._medicine_names, convert_to_numpy=True
            )
            print("✅ Medicine name embeddings ready!")
            return True

        except Exception as e:
            print(f"⚠️  Could not load medicine embeddings: {e}")
            return False

    def extract_medicine_name_semantic(
        self, message: str, threshold: float = 0.55
    ) -> Optional[str]:
        """
        Extract the most likely medicine name from a free-form user message
        using sentence transformer cosine similarity.

        Compares the message embedding against all medicine names in the DB
        and returns the best match above the threshold.

        Args:
            message: User message (e.g. "do you have something like ibuprofen")
            threshold: Minimum cosine similarity to accept a match

        Returns:
            Best matching medicine name from DB, or None if no good match
        """
        if not self._load_medicine_embeddings():
            return None

        message_embedding = self.model.encode([message], convert_to_numpy=True)[0]

        # Cosine similarity against all medicine names
        similarities = np.dot(self._medicine_name_embeddings, message_embedding) / (
            np.linalg.norm(self._medicine_name_embeddings, axis=1)
            * np.linalg.norm(message_embedding)
        )

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score >= threshold:
            medicine_name = self._medicine_names[best_idx]
            print(
                f"SEMANTIC EXTRACT: '{medicine_name}' (score={best_score:.3f}) from '{message[:60]}'"
            )
            return medicine_name

        print(
            f"SEMANTIC EXTRACT: No match above threshold {threshold} "
            f"(best={best_score:.3f}) for '{message[:60]}'"
        )
        return None

    def invalidate_medicine_cache(self):
        """Invalidate cached medicine embeddings (call after DB changes)."""
        self._medicine_name_embeddings = None
        self._medicine_names = None


# Global instance (lazy loaded)
_classifier = None
_classifier_lock = threading.Lock()


def get_intent_classifier() -> IntentClassifier:
    """Get or create global intent classifier instance."""
    global _classifier
    if _classifier is None:
        with _classifier_lock:
            if _classifier is None:
                _classifier = IntentClassifier()
    return _classifier


def classify_intent(message: str) -> Dict:
    """
    Classify user intent using semantic similarity.

    Args:
        message: User message

    Returns:
        Dict with intent, confidence, and reasoning
    """
    classifier = get_intent_classifier()
    return classifier.classify(message)


def extract_medicine_name_semantic(message: str, threshold: float = 0.55) -> Optional[str]:
    """
    Extract medicine name from message using sentence transformer similarity.

    Args:
        message: User message
        threshold: Minimum cosine similarity threshold

    Returns:
        Medicine name from DB or None
    """
    classifier = get_intent_classifier()
    return classifier.extract_medicine_name_semantic(message, threshold)
