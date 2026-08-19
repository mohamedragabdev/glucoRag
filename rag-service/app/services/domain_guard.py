import re
from enum import Enum
from typing import Optional, Tuple, List
from app.schemas.query import Turn

class IntentType(str, Enum):
    GREETING = "greeting"
    APP_INFO = "app_info"
    IN_SCOPE_SCREENING = "in_scope_screening"
    OUT_OF_SCOPE_TREATMENT = "out_of_scope_treatment"
    OUT_OF_SCOPE_DIAGNOSIS = "out_of_scope_diagnosis"
    OUT_OF_SCOPE_EMERGENCY = "out_of_scope_emergency"
    OUT_OF_SCOPE_GENERAL = "out_of_scope_general"
    UNKNOWN = "unknown"

# Bilingual Standard Messages
MSG_GREETING_EN = "Hello! I'm GlucoRAG, an evidence-grounded assistant specialized in Type 2 Diabetes screening."
MSG_GREETING_AR = "أهلاً! أنا GlucoRAG، مساعد متخصص في فحص السكري من النوع الثاني بالاعتماد على الإرشادات الطبية."

MSG_APP_INFO_EN = "GlucoRAG is an evidence-grounded clinical decision-support assistant specialized in Type 2 Diabetes screening guidance for primary-care clinicians."
MSG_APP_INFO_AR = "GlucoRAG هو مساعد لدعم القرار الإكلينيكي مبني على الأدلة، متخصص حصرياً في إرشادات فحص السكري من النوع الثاني لأطباء الرعاية الأولية."

MSG_REFUSAL_EN = "I’m sorry, but GlucoRAG is limited to Type 2 Diabetes screening guidance. I can help with screening criteria, recommended screening tests, eligibility, thresholds, and screening intervals."
MSG_REFUSAL_AR = "عذرًا، GlucoRAG متخصص فقط في إرشادات فحص السكري من النوع الثاني. يمكنني مساعدتك في معايير الفحص، الفحوصات المستخدمة، الفئات المستهدفة، الحدود المرجعية، وفترات إعادة الفحص."

MSG_INSUFFICIENT_EN = "I couldn't find sufficient information in the current reference documents to answer this reliably."
MSG_INSUFFICIENT_AR = "لم أجد معلومات كافية في المستندات المرجعية الحالية للإجابة عن هذا السؤال بشكل موثوق."


def is_arabic(text: str) -> bool:
    """Check if the text contains Arabic characters."""
    return bool(re.search(r'[\u0600-\u06FF]', text))


class DomainGuard:
    """
    Semantic pre-retrieval clinical domain guard for GlucoRAG.
    Accurately classifies greetings, application questions, and direct out-of-scope requests
    while ensuring all valid Type 2 Diabetes screening queries reach the RAG pipeline.
    """

    @staticmethod
    def classify_intent(question: str, history: Optional[List[Turn]] = None) -> Tuple[IntentType, Optional[str]]:
        q_clean = question.strip().lower()
        arabic = is_arabic(question)

        # 1. Greetings & Basic Politeness
        greetings_en = [
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings", "howdy", "welcome"
        ]
        greetings_ar = [
            "السلام عليكم", "مرحبا", "مرحباً", "اهلا", "أهلا", "أهلاً", "هاي", "صباح الخير", "مساء الخير", "ازيك", "كيفك", "شلونك", "سلام"
        ]

        if q_clean in greetings_en or any(q_clean.startswith(g + " ") for g in ["hi", "hello", "hey", "good morning"]):
            return IntentType.GREETING, MSG_GREETING_EN

        if any(g == q_clean or q_clean.startswith(g + " ") for g in greetings_ar) and len(q_clean.split()) <= 4:
            return IntentType.GREETING, MSG_GREETING_AR

        # 2. Application Info / Identity
        app_info_patterns_en = [
            "what is glucorag", "who are you", "what can you do", "what can you help", "how do you work", "about glucorag"
        ]
        app_info_patterns_ar = [
            "مين انت", "من انت", "من أنت", "مين إنت", "ما هو جلوكوراج", "ما هو glucorag", "بتعمل ايه", "ماذا تفعل", "كيف تساعدني", "ما وظيفتك", "عن النظام"
        ]

        if any(p in q_clean for p in app_info_patterns_en):
            return IntentType.APP_INFO, MSG_APP_INFO_EN

        if any(p in q_clean for p in app_info_patterns_ar):
            return IntentType.APP_INFO, MSG_APP_INFO_AR

        # 3. Explicit Non-Medical & General Off-Topic Queries
        off_topic_en = [
            "write python", "write code", "programming in", "what is the weather", "weather forecast",
            "what's the weather", "tell me a joke", "who is the president", "capital of france", "translate this"
        ]
        off_topic_ar = [
            "اكتب كود", "اكتب بايثون", "برمجة", "حالة الطقس", "الطقس اليوم", "اخبرني نكتة", "من هو رئيس", "عاصمة فرنسا", "ترجم لي"
        ]
        if any(p in q_clean for p in off_topic_en) or any(p in q_clean for p in off_topic_ar):
            return IntentType.OUT_OF_SCOPE_GENERAL, (MSG_REFUSAL_AR if arabic else MSG_REFUSAL_EN)

        # 4. Check if question is an in-scope screening question or screening follow-up
        is_explicit_screening = any(
            k in q_clean
            for k in [
                "screen", "screening", "uspstf", "ada", "fpg", "a1c", "ogtt", "prediabetes",
                "screening age", "screening interval", "screening test", "risk factor",
                "فحص", "مسح", "توصيات", "معايير الفحص", "سن الفحص", "عمر الفحص", "فترة الفحص", "عوامل خطورة"
            ]
        )

        has_screening_history = False
        if history and len(history) > 0:
            last_turns = " ".join([t.content for t in history if t.content]).lower()
            if any(k in last_turns for k in ["screening", "diabetes", "t2d", "فحص", "السكري"]):
                has_screening_history = True

        # If it is an in-scope screening inquiry and not asking for a personal drug/treatment prescription:
        if (is_explicit_screening or has_screening_history) and not any(
            t in q_clean for t in ["what dose", "prescribe", "what medication should i take", "how do i treat", "جرعة", "ماذا أتناول"]
        ):
            return IntentType.IN_SCOPE_SCREENING, None

        # 5. Direct Acute Emergency Requests
        emergency_words_en = ["emergency", "unresponsive", "chest pain", "dka", "hhs", "call 911", "dying"]
        emergency_words_ar = ["طوارئ", "غيبوبة", "إسعاف", "اسعاف", "ألم حاد في الصدر", "مريض فاقد الوعي"]
        if any(w in q_clean for w in emergency_words_en) or any(w in q_clean for w in emergency_words_ar):
            return IntentType.OUT_OF_SCOPE_EMERGENCY, (MSG_REFUSAL_AR if arabic else MSG_REFUSAL_EN)

        # 6. Direct Personal Diagnosis Requests
        diagnosis_words_en = [
            "diagnose", "do i have diabetes", "does this patient have", "diagnose my symptoms",
            "give me a diagnosis", "can you diagnose", "tell me if i have diabetes"
        ]
        diagnosis_words_ar = [
            "شخص حالتي", "شخص لي", "شخصني", "شخص هذا المريض", "هل أنا مصاب بالسكري", "هل عندي سكر",
            "أعطني تشخيص", "هل تقدر تشخص", "هل يمكن تشخيص المريض"
        ]
        if any(w in q_clean for w in diagnosis_words_en) or any(w in q_clean for w in diagnosis_words_ar):
            return IntentType.OUT_OF_SCOPE_DIAGNOSIS, (MSG_REFUSAL_AR if arabic else MSG_REFUSAL_EN)

        # 7. Direct Treatment & Prescription & Non-T2D Disease Requests
        treatment_words_en = [
            "treat", "treatment", "cure", "medication", "medicine", "antibiotic", "metformin", "insulin",
            "dose", "dosage", "prescribe", "prescription", "diet", "what should i eat", "cancer", "asthma",
            "appendicitis", "covid", "how to cure"
        ]
        treatment_words_ar = [
            "علاج", "عالج", "ادوية", "أدوية", "دواء", "مضاد حيوي", "ميتفورمين", "انسولين", "أنسولين",
            "جرعة", "وصفة", "حمية", "ماذا آكل", "خفض السكر", "تنظيم السكر", "سرطان", "ربو", "زائدة دودية"
        ]
        if any(w in q_clean for w in treatment_words_en) or any(w in q_clean for w in treatment_words_ar):
            return IntentType.OUT_OF_SCOPE_TREATMENT, (MSG_REFUSAL_AR if arabic else MSG_REFUSAL_EN)

        # 8. All other queries proceed to RAG retrieval (where clinical documents provide evidence)
        return IntentType.UNKNOWN, None
