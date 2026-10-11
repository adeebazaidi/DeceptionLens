import os
import io
from typing import List, Dict, Any, Union
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
import easyocr

# Initialize EasyOCR reader (loads model weights into memory once)
reader = easyocr.Reader(['en'], gpu=False)

def load_document(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Loads a document (PDF or image) and returns a list of pages as numpy arrays.
    Returns: [{'page_num': 1, 'image': np.array}, ...]
    """
    ext = os.path.splitext(filename)[1].lower()
    pages = []

    if ext == '.pdf':
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for i in range(len(doc)):
            page = doc[i]
            # render page to an image (zoom for better OCR resolution)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append({'page_num': i + 1, 'image': np.array(img)})
        doc.close()
    else:
        # Assume it's an image
        img = Image.open(io.BytesIO(file_bytes)).convert('RGB')
        pages.append({'page_num': 1, 'image': np.array(img)})

    return pages

def perform_ocr(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Performs OCR on the given pages.
    Returns the pages with OCR text, bounding boxes, and confidence appended.
    """
    results = []
    
    for page in pages:
        img_np = page['image']
        # Read text
        # detail=1 gives bounding boxes, text, and confidence
        ocr_result = reader.readtext(img_np)
        
        extracted_items = []
        raw_text_parts = []
        
        for bbox, text, conf in ocr_result:
            # Convert bbox numpy floats to int
            bbox_int = [[int(x), int(y)] for [x, y] in bbox]
            extracted_items.append({
                'bbox': bbox_int,
                'text': text,
                'confidence': float(conf)
            })
            raw_text_parts.append(text)
            
        page_result = {
            'page_num': page['page_num'],
            'ocr_items': extracted_items,
            'raw_text': " ".join(raw_text_parts)
        }
        results.append(page_result)
        
    return results

def clean_text(text: str) -> str:
    """
    Cleans OCR text by normalizing whitespace while preserving useful forensic info.
    """
    # Replace multiple spaces/newlines with single space
    import re
    cleaned = re.sub(r'\s+', ' ', text)
    return cleaned.strip()

