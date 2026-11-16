import re
from typing import Dict, List, Any

SPACY_MODEL = "en_core_web_sm"

# spaCy is loaded lazily on first use so that a broken or blocked spaCy
# install only disables document NER instead of preventing the whole
# backend from starting.
_nlp = None


class NLPUnavailableError(RuntimeError):
    """Raised when the spaCy NLP engine cannot be loaded."""


def get_nlp():
    """Return the cached spaCy pipeline, loading it on first call."""
    global _nlp
    if _nlp is not None:
        return _nlp

    try:
        import spacy
    except ImportError as exc:
        raise NLPUnavailableError(
            f"The spaCy NLP engine could not be loaded: {exc}"
        ) from exc

    try:
        _nlp = spacy.load(SPACY_MODEL)
    except OSError:
        # Fallback if model not downloaded properly
        import spacy.cli
        spacy.cli.download(SPACY_MODEL)
        _nlp = spacy.load(SPACY_MODEL)
    return _nlp

# Identifier patterns. `\b` stops matches inside words (e.g. "fir" in
# "confirmed"), and the captured ID must contain a digit so ordinary words
# after "case"/"FIR" (e.g. "the case was closed") are not taken as IDs.
_ID = r"([A-Z0-9\-/]*\d[A-Z0-9\-/]*)"
CASE_NUMBER_PATTERN = r"(?i)\bcase(?:\s+no\.?|\s+number)?\s*[:\-#]?\s*" + _ID
FIR_NUMBER_PATTERN = r"(?i)\bfir(?:\s+no\.?|\s+number)?\s*[:\-#]?\s*" + _ID
PHONE_PATTERN = r"(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}"
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Currency amounts that spaCy's small English model misses, notably Indian
# rupees ("Rs. 5,000", "₹1,20,000", "3 lakh", "5,000 rupees").
_AMOUNT = r"\d(?:[\d,]*\d)?(?:\.\d+)?"  # must end in a digit, so "5,000," drops the comma
_INDIAN_UNIT = r"(?:lakhs?|lacs?|crores?)"
MONEY_PATTERN = (
    # "Rs:" is accepted because OCR often misreads the period in "Rs." as a colon.
    r"(?i)(?:₹|\brs\b[.:]?|\binr\b|\busd\b|\$|€|£)\s?" + _AMOUNT + r"(?:\s*" + _INDIAN_UNIT + r"\b)?"
    r"|\b" + _AMOUNT + r"\s*(?:" + _INDIAN_UNIT + r"|rupees)\b"
)

FORENSIC_KEYWORDS = [
    "accused", "victim", "witness", "complaint", "evidence",
    "investigation", "case", "fir", "report", "statement",
    "officer", "department", "incident", "signature", "verification"
]

def find_source_context(text: str, entity_text: str, window: int = 40) -> str:
    """Finds the source text context surrounding the entity."""
    idx = text.find(entity_text)
    if idx == -1:
        return entity_text
    
    start = max(0, idx - window)
    end = min(len(text), idx + len(entity_text) + window)
    
    context = text[start:end].replace('\n', ' ')
    if start > 0:
        context = "..." + context
    if end < len(text):
        context = context + "..."
        
    return context

def extract_entities_and_info(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts NLP entities, regex-based information, and forensic keywords from pages.
    Preserves page number and source context.
    Raises NLPUnavailableError if spaCy cannot be loaded.
    """
    nlp = get_nlp()

    entities = {
        "persons": [],
        "dates": [],
        "locations": [],
        "organizations": [],
        "money": []
    }
    
    case_numbers = []
    phone_numbers = []
    email_addresses = []
    keywords = []

    # Track seen to avoid exact duplicates on the same page
    seen_entities = set()
    
    for page in pages:
        page_num = page.get('page_num', 1)
        raw_text = page.get('raw_text', '')
        
        # We also want to extract from cleaned text to get better NLP
        # but map it back. Let's run NLP on raw text.
        doc = nlp(raw_text)
        
        for ent in doc.ents:
            val = ent.text.strip()
            if not val or len(val) < 2: continue
            
            ent_type = None
            if ent.label_ == "PERSON":
                ent_type = "persons"
            elif ent.label_ == "DATE":
                ent_type = "dates"
            elif ent.label_ in ["GPE", "LOC"]:
                ent_type = "locations"
            elif ent.label_ == "ORG":
                ent_type = "organizations"
            elif ent.label_ == "MONEY":
                ent_type = "money"
                
            if ent_type:
                unique_key = f"{ent_type}:{val}:{page_num}"
                if unique_key not in seen_entities:
                    seen_entities.add(unique_key)
                    entities[ent_type].append({
                        "value": val,
                        "type": ent.label_,
                        "page": page_num,
                        "source_text": find_source_context(raw_text, val)
                    })

        # Regex
        for match in re.finditer(MONEY_PATTERN, raw_text):
            val = match.group(0).strip()
            k = f"money:{val}:{page_num}"
            if k not in seen_entities:
                seen_entities.add(k)
                entities["money"].append({
                    "value": val,
                    "type": "MONEY",
                    "page": page_num,
                    "source_text": find_source_context(raw_text, val)
                })

        for match in re.finditer(CASE_NUMBER_PATTERN, raw_text):
            val = match.group(1).strip()
            k = f"case:{val}:{page_num}"
            if k not in seen_entities:
                seen_entities.add(k)
                case_numbers.append({"value": val, "page": page_num, "source_text": find_source_context(raw_text, val)})
                
        for match in re.finditer(FIR_NUMBER_PATTERN, raw_text):
            val = match.group(1).strip()
            k = f"fir:{val}:{page_num}"
            if k not in seen_entities:
                seen_entities.add(k)
                case_numbers.append({"value": val, "page": page_num, "source_text": find_source_context(raw_text, val)})

        for match in re.finditer(PHONE_PATTERN, raw_text):
            val = match.group(0).strip()
            k = f"phone:{val}:{page_num}"
            if k not in seen_entities:
                seen_entities.add(k)
                phone_numbers.append({"value": val, "page": page_num, "source_text": find_source_context(raw_text, val)})

        for match in re.finditer(EMAIL_PATTERN, raw_text):
            val = match.group(0).strip()
            k = f"email:{val}:{page_num}"
            if k not in seen_entities:
                seen_entities.add(k)
                email_addresses.append({"value": val, "page": page_num, "source_text": find_source_context(raw_text, val)})

        # Keywords
        text_lower = raw_text.lower()
        for keyword in FORENSIC_KEYWORDS:
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', text_lower):
                k = f"kw:{keyword}:{page_num}"
                if k not in seen_entities:
                    seen_entities.add(k)
                    # Use original case from raw_text
                    actual_kw = raw_text[match.start():match.end()]
                    keywords.append({"value": actual_kw, "page": page_num, "source_text": find_source_context(raw_text, actual_kw)})

    case_information = {
        "case_numbers": case_numbers,
        "phone_numbers": phone_numbers,
        "email_addresses": email_addresses,
        "keywords": keywords
    }
    
    return {
        "entities": entities,
        "case_information": case_information
    }
