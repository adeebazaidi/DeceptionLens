import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from modules.document_analysis.analyzer import analyze_document

router = APIRouter()

@router.post("/analyze")
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    Analyzes a forensic document (PDF or Image).
    Extracts text, entities, normalizes data, and identifies internal inconsistencies.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
        
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in ['pdf', 'png', 'jpg', 'jpeg', 'tif', 'tiff']:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or Images.")
        
    try:
        file_bytes = await file.read()
        
        # We don't want to process excessively large files in memory directly if we can avoid it,
        # but for this module, reading into bytes is fine. Max 20MB check.
        if len(file_bytes) > 20 * 1024 * 1024:
             raise HTTPException(status_code=400, detail="File too large. Maximum 20MB allowed.")
             
        analysis_result = analyze_document(file_bytes, file.filename)
        
        return JSONResponse(content=analysis_result)
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")
