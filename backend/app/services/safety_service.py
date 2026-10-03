import re
from typing import Tuple

CRISIS_KEYWORDS = [
    r"\bsuicid(e|al)\b",
    r"\bkill myself\b",
    r"\bwant to die\b",
    r"\bend my life\b",
    r"\bself[- ]harm\b",
    r"\bhurt myself\b",
    r"\boverdose\b",
    r"\bhang myself\b",
]

CRISIS_SAFETY_MESSAGE = (
    "It sounds like you are going through an extraordinarily difficult time, and your safety and life matter deeply. "
    "I am an AI assistant and cannot provide medical care or crisis intervention. Please connect right away with people who can help support you:\n\n"
    "- **In the US & Canada:** Call or text **988** to reach the Suicide & Crisis Lifeline (free, confidential, 24/7).\n"
    "- **Crisis Text Line:** Text **HOME to 741741** to connect with a crisis counselor.\n"
    "- **In the UK:** Call **111** (NHS) or call the Samaritans at **116 123**.\n"
    "- **International:** Find local support resources at https://findahelpline.com or contact your local emergency services (e.g. 911 / 999 / 112).\n\n"
    "Please reach out to a trusted loved one, adult, counselor, or emergency service right now. You don't have to carry this alone."
)

EMOTIONAL_SUPPORT_SYSTEM_INSTRUCTION = (
    "You are a compassionate, thoughtful, and supportive AI personal assistant. "
    "Your objective is to provide a safe, respectful, and comforting sounding board for the user.\n\n"
    "GUIDELINES FOR EMOTIONAL ASSISTANCE:\n"
    "1. Practice active, non-judgmental listening and validate the user's feelings warmly.\n"
    "2. Help the user gently organize their thoughts, reflect on their emotions, or try journaling prompts.\n"
    "3. Offer gentle, everyday healthy coping strategies (e.g., box breathing, mindful walks, taking a pause, writing things down).\n"
    "4. Warmly encourage connecting with trusted friends, family, or communities when appropriate.\n\n"
    "CRITICAL BOUNDARIES & DISCLAIMER:\n"
    "- You are an AI assistant, NOT a doctor, therapist, psychologist, or healthcare professional.\n"
    "- Never diagnose medical, mental health, or psychological conditions.\n"
    "- Never prescribe medication or psychiatric treatment.\n"
    "- If the user expresses thoughts of self-harm or suicide, provide crisis lifeline information immediately.\n"
    "- Maintain a warm, grounded, patient, and humble tone."
)

class SafetyService:
    @staticmethod
    def check_crisis(text: str) -> Tuple[bool, str]:
        """
        Check if user query contains critical self-harm or suicide indicators.
        Returns (is_crisis, response_message).
        """
        lower = text.lower()
        for pattern in CRISIS_KEYWORDS:
            if re.search(pattern, lower):
                return True, CRISIS_SAFETY_MESSAGE
        return False, ""

    @staticmethod
    def get_emotional_support_instruction() -> str:
        return EMOTIONAL_SUPPORT_SYSTEM_INSTRUCTION

safety_service = SafetyService()
