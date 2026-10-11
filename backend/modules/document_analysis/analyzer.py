from typing import Dict, Any, List
from .ocr_service import load_document, perform_ocr, clean_text
from .nlp_service import extract_entities_and_info
from .consistency_checker import check_consistency

def analyze_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Main orchestration function for Document Analysis.
    Loads doc -> OCR -> Clean Text -> Entity Extraction -> Consistency Check
    """
    # 1. Load Document
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    is_pdf = ext == 'pdf'
    
    pages_raw = load_document(file_bytes, filename)
    page_count = len(pages_raw)
    
    # 2. OCR
    pages_ocr = perform_ocr(pages_raw)
    
    # 3. Text cleaning & assembling output pages
    clean_pages = []
    full_raw_text = []
    full_cleaned_text = []
    
    for p in pages_ocr:
        raw = p.get('raw_text', '')
        cleaned = clean_text(raw)
        
        full_raw_text.append(raw)
        full_cleaned_text.append(cleaned)
        
        clean_pages.append({
            "page_num": p["page_num"],
            "raw_text": raw,
            "cleaned_text": cleaned,
            "ocr_items": p.get("ocr_items", [])
        })
        
    combined_raw_text = "\n".join(full_raw_text)
    combined_cleaned_text = "\n".join(full_cleaned_text)
    
    # 4. Entity & Info Extraction
    # We pass the pages to maintain source context and page numbers
    extraction_results = extract_entities_and_info(clean_pages)
    entities = extraction_results["entities"]
    case_info = extraction_results["case_information"]
    
    # 5. Consistency Analysis
    consistency_results = check_consistency(entities, case_info)
    
    # 6. Construct Final Report
    return {
        "document": {
            "filename": filename,
            "type": ext,
            "page_count": page_count
        },
        "pages": clean_pages,
        "text": {
            "raw": combined_raw_text,
            "cleaned": combined_cleaned_text
        },
        "entities": entities,
        "case_information": case_info,
        "consistency_analysis": consistency_results
    }
