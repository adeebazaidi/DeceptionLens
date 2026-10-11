# DeceptionLens
## Entropy-Driven Image Forgery Detection

A full-stack forensic image analysis tool built with **React + Vite** (frontend) and **FastAPI + Python** (backend).

> ⚠️ **Disclaimer**: DeceptionLens provides **preliminary image-forensic analysis** for research and educational purposes only. Entropy variation, ELA, noise, texture, and ML outputs are analytical indicators and must not be interpreted as definitive proof that an image has been manipulated.

---

## Architecture

```
React Frontend (Vite)
       │
       │ REST API (POST /api/image/analyze)
       ▼
FastAPI Backend
       │
  ┌────┴──────┐
  │           │
  ▼           ▼
Forensics   ML (optional)
  │
  ├── Entropy Analysis (Shannon entropy, local block variation)
  ├── ELA (Error Level Analysis)
  ├── Noise Analysis (Gaussian blur subtraction)
  ├── Texture Analysis (GLCM features)
  └── Metadata Extraction (EXIF)
       │
       ▼
  JSON Response → React Dashboard
```

---

## Project Structure

```
DeceptionLens/
├── backend/
│   ├── main.py                     # FastAPI app entry point (all forensic routers)
│   ├── requirements.txt            # Python dependencies (FastAPI, PyTorch/EasyOCR, spaCy, scikit-image)
│   ├── .env                        # Configuration (CORS, upload size limits)
│   ├── api/routes/
│   │   ├── image_routes.py         # POST /api/image/analyze
│   │   ├── fingerprint_routes.py   # POST /api/fingerprint/compare
│   │   ├── signature_routes.py     # POST /api/signature/analyze
│   │   └── document_routes.py      # POST /api/document/analyze
│   ├── evaluation/
│   │   └── evaluate_fingerprint.py # FVC2002/SOCOFing benchmark performance evaluation
│   ├── modules/                    # Forensic Analysis Modules
│   │   ├── __init__.py             # Master package exports & backward-compatibility aliases
│   │   ├── image/                  # Image Forgery Detection Module
│   │   │   ├── __init__.py
│   │   │   ├── preprocessing.py    # Image decode & validation
│   │   │   ├── entropy_analysis.py # Shannon entropy & block variation heatmaps
│   │   │   ├── ela_analysis.py     # Error Level Analysis re-compression difference
│   │   │   ├── noise_analysis.py   # High-frequency noise residuals
│   │   │   ├── texture_analysis.py # GLCM second-order texture descriptors
│   │   │   ├── metadata_analysis.py# EXIF/TIFF metadata & software artifact extraction
│   │   │   ├── feature_extraction.py # 17-dimensional canonical feature vector for ML
│   │   │   ├── forgery_detector.py # Rule-based multi-factor heuristic risk scoring
│   │   │   └── advanced_analysis.py# Laplacian blur variance, copy-move detection
│   │   ├── signature/              # Handwritten Signature Analysis Module
│   │   │   ├── __init__.py
│   │   │   └── signature_analysis.py # Stroke tremor, skeletonization & 1-vs-1 verification
│   │   ├── fingerprint/            # Biometric Fingerprint Comparison Module
│   │   │   ├── __init__.py
│   │   │   ├── preprocessing.py    # Image decode, grayscale, CLAHE, denoising
│   │   │   ├── enhancement.py      # Orientation field, top-hat/black-hat, mask
│   │   │   ├── minutiae.py         # Binarization, skeletonization, CN extraction
│   │   │   ├── matching.py         # Rigid alignment & tolerance minutiae pairing
│   │   │   ├── visualization.py    # Minutiae overlays & comparison correspondence maps
│   │   │   └── service.py          # End-to-end pipeline service orchestrator
│   │   └── document_analysis/      # Forensic Document Analysis Module
│   │       ├── __init__.py         # Subpackage exports
│   │       ├── analyzer.py         # Document pipeline orchestrator
│   │       ├── ocr_service.py      # PyMuPDF rasterization & EasyOCR engine
│   │       ├── nlp_service.py      # spaCy NER & forensic regex extraction
│   │       ├── normalization.py    # Date, name, location, and money normalizers
│   │       └── consistency_checker.py # Cross-field conflict & contradiction detector
│   ├── ml/
│   │   ├── train_classifier.py
│   │   ├── predict.py
│   │   └── models/                # Trained Random Forest model artifacts
│   ├── outputs/                   # Generated artifacts (entropy, ela, noise, fingerprint, signature)
│   └── tests/                     # 61 Automated Pytest Unit & Integration Tests
│       ├── test_entropy.py
│       ├── test_ela.py
│       ├── test_fingerprint.py
│       ├── test_signature.py
│       ├── test_consistency.py
│       └── test_api.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx                    # Landing page & forensic suites showcase
│   │   │   ├── ImageAnalysis.jsx           # Forensic image forgery dashboard
│   │   │   ├── FingerprintComparison.jsx   # Biometric fingerprint verification page
│   │   │   ├── SignatureAnalysis.jsx       # Handwritten signature analysis page
│   │   │   └── DocumentAnalysis.jsx        # Multi-page document OCR & consistency page
│   │   ├── components/                     # Reusable UI components & uploaders
│   │   ├── api/
│   │   │   ├── imageApi.js
│   │   │   ├── fingerprintApi.js
│   │   │   ├── signatureApi.js
│   │   │   └── documentApi.js
│   │   └── styles/app.css
│   └── vite.config.js             # Dev proxy to backend (/api & /outputs)
├── dataset/                       
│   ├── authentic/                 # Unmanipulated images
│   ├── forged/                    # Manipulated images
│   └── fingerprints/              # FVC2002/SOCOFing benchmark datasets
├── COLAB_TRAINING_GUIDE.md        # Cloud ML model training guide
└── README.md
```

---

## Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher
- **npm** 9 or higher

---

## Running the Backend

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Edit configuration
#    Edit .env to change FRONTEND_URL, MAX_UPLOAD_SIZE_MB, etc.

# 3. Start the server
uvicorn main:app --reload --port 8000
# (Alternatively, you can simply run: python main.py)
```

The backend will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Running the Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start the dev server
npm run dev
```

The frontend will be available at: **http://localhost:5173**

> The Vite dev server proxies `/api` and `/outputs` to `http://localhost:8000` automatically.

---

## API Endpoint

### `POST /api/image/analyze`
[Content remains same]

---

### `POST /api/document/analyze`

**Content-Type:** `multipart/form-data`

**Field:** `file` — document file (PDF, JPG, JPEG, PNG, TIFF)

**Max size:** 20 MB

**Example response:**

```json
{
  "document": {
    "filename": "statement.pdf",
    "type": "pdf",
    "page_count": 2
  },
  "pages": [...],
  "text": {
    "raw": "...",
    "cleaned": "..."
  },
  "entities": {
    "persons": [{"value": "Rahul Sharma", "type": "PERSON", "page": 1, "source_text": "...Rahul Sharma..."}],
    "dates": [{"value": "12/08/2026", "type": "DATE", "page": 1, "source_text": "...on 12/08/2026..."}],
    "locations": [],
    "organizations": [],
    "money": []
  },
  "case_information": {
    "case_numbers": [{"value": "FIR-1234", "page": 1, "source_text": "..."}],
    "keywords": [{"value": "accused", "page": 2, "source_text": "..."}]
  },
  "consistency_analysis": {
    "status": "Potential inconsistency",
    "issues": [
      {
        "type": "DATE_INCONSISTENCY",
        "title": "Potential date inconsistency",
        "reason": "Multiple distinct dates were found in the document.",
        "evidence": [
          {"value": "12/08/2026", "page": 1},
          {"value": "15/08/2026", "page": 2}
        ]
      }
    ]
  }
}
```

---

### `POST /api/fingerprint/compare`

**Content-Type:** `multipart/form-data`

**Field:** `file` — image file (JPG, JPEG, PNG, WEBP)

**Max size:** 10 MB (configurable in `.env`)

**Example response:**

```json
{
  "success": true,
  "filename": "sample.jpg",
  "image_info": { "width": 1920, "height": 1080, "format": "JPEG", "file_size": 245678 },
  "entropy": {
    "global": 6.42, "mean_local": 6.21, "std_local": 0.72,
    "min_local": 4.81, "max_local": 7.91, "anomaly_score": 0.12,
    "heatmap_url": "/outputs/entropy/abc123.png"
  },
  "ela": { "mean": 12.4, "std": 8.2, "max": 87, "image_url": "/outputs/ela/abc123.png" },
  "noise": { "mean": 4.3, "std": 3.1, "max": 28, "image_url": "/outputs/noise/abc123.png" },
  "texture": { "contrast": 1.82, "dissimilarity": 0.91, "homogeneity": 0.73, "energy": 0.42, "correlation": 0.84 },
  "metadata": { "format": "JPEG", "width": 1920, "height": 1080, "software": null },
  "preliminary_result": { "risk_level": "MEDIUM", "reason": ["Moderate local entropy variation detected"] },
  "ml_prediction": { "available": false, "message": "ML model has not been trained yet." }
}
```

---

### `POST /api/fingerprint/compare`

**Content-Type:** `multipart/form-data`

**Fields:**
- `reference` (or `reference_image`) — Reference exemplar fingerprint image (TIF, PNG, JPG, BMP)
- `questioned` (or `questioned_image`) — Questioned / query fingerprint impression
- `threshold` (optional) — Custom match decision threshold percentage (default: `45.0`)

**Max size:** 10 MB per file

**Example response:**

```json
{
  "success": true,
  "result": "Likely Match",
  "similarity_score": 52.89,
  "reference_minutiae": 12,
  "questioned_minutiae": 11,
  "matched_minutiae": 6,
  "threshold": 45.0,
  "processing_time": 0.38,
  "details": {
    "reference_endings": 8,
    "reference_bifurcations": 4,
    "questioned_endings": 7,
    "questioned_bifurcations": 4,
    "alignment": {
      "base_ref_idx": 0,
      "base_quest_idx": 0,
      "rotation_degrees": 3.5,
      "translation_x": 4.0,
      "translation_y": -3.0
    },
    "matched_count": 6
  },
  "visualizations": {
    "reference_enhanced": "/outputs/fingerprint/a1b2c3_ref_enhanced.png",
    "reference_skeleton": "/outputs/fingerprint/a1b2c3_ref_skeleton.png",
    "reference_minutiae": "/outputs/fingerprint/a1b2c3_ref_minutiae.png",
    "questioned_enhanced": "/outputs/fingerprint/a1b2c3_quest_enhanced.png",
    "questioned_skeleton": "/outputs/fingerprint/a1b2c3_quest_skeleton.png",
    "questioned_minutiae": "/outputs/fingerprint/a1b2c3_quest_minutiae.png",
    "comparison": "/outputs/fingerprint/a1b2c3_comparison.png"
  }
}
```

---

## Document Analysis Pipeline

**Purpose:** Extract and analyze information from forensic documents and identify potential internal inconsistencies.

**Technology:** EasyOCR, spaCy, Python, Regex/pattern matching, Rule-based consistency analysis, React frontend, FastAPI backend.

The module performs:
Document → OCR → Text Cleaning → Entity Extraction → Information Normalization → Consistency Analysis → Structured Report

This module handles forensic document evaluation. It provides extracted text mapping, context-preserved NLP entity extraction, and intelligent rule-based mismatch detection across pages (e.g., date contradictions).

---

## Fingerprint Verification Pipeline & Viva Guide

### 12 Viva Questions & Concise Explanations

1. **What is a fingerprint ridge?**
   A fingerprint ridge is a raised friction skin furrow on the epidermis that leaves an impression when pressed against a surface. In digital biometric imaging, ridges appear as darker parallel curves and valleys appear as lighter spacing between them.

2. **Why do we preprocess the image?**
   Raw optical or capacitive scans contain sensor noise, uneven finger pressure, sweat pores, dust, and non-uniform contrast. Preprocessing converts the image to grayscale, normalizes dimensions while preserving aspect ratio, applies median filtering to eliminate high-frequency noise, and runs CLAHE to equalize ridge contrast across the print.

3. **What is ridge enhancement?**
   Ridge enhancement sharpens the ridge-valley pattern. DeceptionLens estimates the local ridge orientation field using gradient covariance and applies morphological Top-Hat/Black-Hat filtering combined with unsharp masking. This clarifies blurry or broken ridges while suppressing background sensor artifacts.

4. **What is skeletonization?**
   Skeletonization (thinning) reduces binary ridge lines of varying thicknesses down to a standardized 1-pixel-wide central axis while preserving topological connectivity. We utilize the Zhang-Suen morphological thinning algorithm from `scikit-image`.

5. **What are minutiae?**
   Minutiae are local ridge discontinuities and topological anomalies where ridges either terminate or split. In biometric forensics (e.g. Galton characteristics), minutiae provide high discriminative entropy for identity verification.

6. **What is a ridge ending?**
   A ridge ending is an abrupt termination point where a friction ridge terminates on the finger surface.

7. **What is a bifurcation?**
   A bifurcation is a point where a single friction ridge splits into two diverging branch ridges.

8. **How are minutiae extracted?**
   Using the **Rutovitz Crossing Number (CN)** on the 1-pixel skeleton:
   $$CN = \frac{1}{2}\sum_{i=1}^8 |P_{i+1} - P_i|$$
   - $CN = 1 \implies$ **Ridge Ending**
   - $CN = 2 \implies$ Continuous Ridge (internal point)
   - $CN = 3 \implies$ **Bifurcation**
   Candidate minutiae near image boundaries or with mutual distances $< 6$ pixels (e.g., broken bridge fragments) are filtered out.

9. **How are two fingerprints compared?**
   Minutiae sets from the reference and questioned impressions undergo **rigid geometric transformation alignment**:
   Candidate pairs are evaluated to calculate trial relative rotation ($\Delta\theta$) and translation $(\Delta x, \Delta y)$. The reference minutiae are transformed, and correspondences are counted within spatial ($R \le 18\text{px}$) and angular ($|\Delta\theta| \le 37^\circ$) tolerances using greedy bipartite matching.

10. **How is similarity calculated?**
    The system computes a balanced normalized score combining the **Sørensen-Dice coefficient** and the **Overlap coefficient**:
    $$\text{Similarity (\%)} = \left[ 0.70 \cdot \frac{2 \cdot N_{\text{matched}}}{N_{\text{ref}} + N_{\text{quest}}} + 0.30 \cdot \frac{N_{\text{matched}}}{\min(N_{\text{ref}}, N_{\text{quest}})} \right] \times 100$$
    This produces a deterministic, explainable percentage between 0% and 100%.

11. **How is the threshold selected?**
    The threshold (default 45.0%) is calibrated using benchmark FVC2002 genuine and impostor distributions to balance False Acceptance Rate (FAR) and False Rejection Rate (FRR). A score $\ge \text{threshold}$ yields **"Likely Match"**; otherwise, **"Likely Non-Match"**.

12. **Why can the system produce false matches or false non-matches?**
    - **False Non-Match (FRR):** Excessive finger rotation ($> 45^\circ$), partial latent overlaps with $< 5$ shared minutiae, high non-linear skin deformation/stretching, or extreme dryness/moisture.
    - **False Match (FAR):** Accidental spatial coincidence of small minutiae subsets in high-density prints or noisy false minutiae.
    *Forensic note: The system serves as an investigative decision aid and not as absolute identification.*

---

## Dataset Benchmark Evaluation (FVC2002 & SOCOFing)

To evaluate the algorithm on the FVC2002 or SOCOFing benchmark datasets:

```bash
cd backend

# 1. Run on FVC2002 benchmark dataset (80 optical impressions)
python -m evaluation.evaluate_fingerprint --dataset-dir ../dataset/fingerprints/fvc2002/sample_pairs --threshold 45.0

# 2. Run on SOCOFing benchmark dataset (Real vs Altered: CR, Obl, Zcut)
python -m evaluation.evaluate_fingerprint --dataset-dir ../dataset/fingerprints/socofing/sample_pairs --threshold 40.0
```

Reports:
- Genuine & Impostor pair counts
- Average Genuine Similarity vs Average Impostor Similarity
- False Acceptance Rate (FAR / FMR)
- False Rejection Rate (FRR / FNMR)
- Verification Accuracy percentage

---

## Running Tests

```bash
cd backend

# Install pytest if not already installed
pip install pytest httpx

# Run all tests
python -m pytest tests/ -v
```

Tests cover:
- Entropy: constant image, normal image, tiny image, bounds, anomaly score range
- ELA: valid JPEG, invalid path, output size, value range, file saving
- API: valid upload, PNG upload, unsupported type (400), missing file (422), oversized (413)

---

## ML Training (Phase 3 — Optional)

### 1. Prepare dataset

Add images to:
```
dataset/authentic/   ← unmanipulated images
dataset/forged/      ← manipulated images
```

### 2. Run training

```bash
cd backend
python ml/train_classifier.py
```

This will:
- Extract forensic features from every image
- Train a Random Forest classifier (80/20 stratified split)
- Print accuracy, precision, recall, F1, confusion matrix, ROC-AUC
- Save `backend/ml/models/forgery_model.joblib`
- Save `backend/ml/models/feature_names.json`

After training, the API will automatically use the model for predictions.

### Features used for ML

| Feature                | Description                          |
|------------------------|--------------------------------------|
| entropy_global         | Whole-image Shannon entropy          |
| entropy_mean_local     | Mean of block-level entropy          |
| entropy_std_local      | Std of block-level entropy           |
| entropy_min/max_local  | Min/max block entropy                |
| entropy_anomaly_score  | Coefficient of variation (heuristic) |
| ela_mean/std/max       | ELA difference statistics            |
| noise_mean/std/max     | Noise residual statistics            |
| texture_contrast       | GLCM contrast                        |
| texture_dissimilarity  | GLCM dissimilarity                   |
| texture_homogeneity    | GLCM homogeneity                     |
| texture_energy         | GLCM energy                          |
| texture_correlation    | GLCM correlation                     |

---

## Environment Variables

Edit `backend/.env`:

| Variable               | Default                   | Description                     |
|------------------------|---------------------------|---------------------------------|
| `FRONTEND_URL`         | `http://localhost:5173`   | Allowed CORS origin             |
| `MAX_UPLOAD_SIZE_MB`   | `10`                      | Max upload file size            |
| `ELA_QUALITY`          | `90`                      | JPEG re-compression quality     |
| `ELA_SCALE`            | `10`                      | ELA amplification factor        |
| `ENTROPY_GRID_SIZE`    | `8`                       | Local entropy grid size (NxN)   |

Risk thresholds can also be overridden via env vars (see `modules/forgery_detector.py`).

---

## Future Work (Phase 4 — CNN)

The architecture is designed to support pretrained CNN integration:
- EfficientNet-B0, ResNet50, or MobileNetV2
- Feature fusion: CNN deep features + forensic features
- Fine-tuning on forensic datasets (CASIA, Columbia, etc.)

> Do not use a generic ImageNet-pretrained model directly for forgery detection without fine-tuning on forensic data.

---

## Analysis Methods

| Method          | Indicator Type    | Notes                                              |
|-----------------|-------------------|----------------------------------------------------|
| Shannon Entropy | Information theory | Local variation suggests inconsistent compression  |
| ELA             | Compression history | Elevated regions may suggest different source      |
| Noise Analysis  | Signal residuals  | Inconsistent noise may indicate region replacement |
| GLCM Texture    | Statistical       | Texture inconsistency across image regions         |
| Random Forest   | ML classification | Only available after training on labeled dataset   |

All results are **preliminary forensic screening indicators** — not definitive forensic conclusions.
