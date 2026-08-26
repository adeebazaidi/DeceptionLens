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
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env                       # Configuration
│   ├── api/routes/image_routes.py # POST /api/image/analyze
│   ├── modules/
│   │   ├── preprocessing.py
│   │   ├── entropy_analysis.py
│   │   ├── ela_analysis.py
│   │   ├── noise_analysis.py
│   │   ├── texture_analysis.py
│   │   ├── metadata_analysis.py
│   │   ├── feature_extraction.py
│   │   └── forgery_detector.py
│   ├── ml/
│   │   ├── train_classifier.py
│   │   ├── predict.py
│   │   └── models/               # Model saved here after training
│   ├── outputs/                  # Generated heatmaps (entropy/ela/noise)
│   └── tests/
│       ├── test_entropy.py
│       ├── test_ela.py
│       └── test_api.py
├── frontend/
│   ├── src/
│   │   ├── pages/Home.jsx
│   │   ├── pages/ImageAnalysis.jsx
│   │   ├── components/           # All UI components
│   │   ├── api/imageApi.js
│   │   └── styles/app.css
│   └── vite.config.js            # Dev proxy to backend
├── dataset/
│   ├── authentic/                # Place authentic images here for ML training
│   └── forged/                   # Place forged images here for ML training
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
