# Fingerprint Benchmark Datasets (FVC2002 & SOCOFing)

This directory houses the fingerprint benchmark datasets used for validating the minutiae extraction, alignment, and verification algorithms in DeceptionLens.

---

## 1. Directory Structure

```text
backend/
└── datasets/
    └── fingerprints/
        ├── README.md                 <-- (This guide)
        ├── fvc2002/                  <-- FVC2002 Benchmark
        │   ├── DB1_B/                <-- FVC2002 DB1 (Set B: 80 TIF impressions)
        │   └── sample_pairs/         <-- Bundled demonstration PNG samples
        └── socofing/                 <-- SOCOFing Benchmark
            ├── README.md
            ├── generate_socofing_samples.py
            └── sample_pairs/         <-- Bundled demonstration BMP samples (Real & Altered)
```

> **Note:**
> - The live application does **not** load this dataset into memory during startup.
> - The user-facing comparison page runs on uploaded image pairs independently.
> - Do **not** commit full multi-hundred megabyte datasets into Git repositories.

---

## 2. Dataset Overview: FVC2002

The **Fingerprint Verification Competition 2002 (FVC2002)** is an internationally recognized standard benchmark in biometrics and digital forensics:

| Database | Sensor Type | Image Size | Resolution | Description |
|:---|:---|:---|:---|:---|
| **DB1** | Optical Sensor ("TouchView II" by Identix) | 388 × 374 | 500 dpi | Clear optical ridges, realistic dryness variations |
| **DB2** | Optical Sensor ("FX2000" by Biometrika) | 296 × 560 | 569 dpi | Moderate sensor noise and minor skin distortion |
| **DB3** | Capacitive Sensor ("100 SC" by Precise Biometrics) | 300 × 300 | 500 dpi | Silicon sensor with non-linear skin elasticity |
| **DB4** | Synthetic Fingerprints ("SFinGe v2.51") | 288 × 384 | ~500 dpi | Pure synthetic fingerprints with known ground truth |

Each database contains fingers numbered `101` to `110` (Set B: public evaluation set) with **8 impressions per finger** (e.g. `101_1.tif` to `101_8.tif`).

---

## 3. How to Obtain the Dataset

1. Download the public FVC2002 benchmark archives from the official Biometric System Laboratory repository:
   - Official URL: [http://bias.csr.unibo.it/fvc2002/databases.asp](http://bias.csr.unibo.it/fvc2002/databases.asp)
   - Or download standard FVC2002 Set B ZIP archives (e.g. `DB1_B.zip`).
2. Extract the TIFF or PNG image files into:
   ```text
   backend/datasets/fingerprints/fvc2002/DB1_B/
   ```

---

## 4. Running the Benchmark Evaluation

Once images are in place (or using bundled sample pairs), run the automated performance evaluation script:

```bash
cd backend

# Evaluate on FVC2002 benchmark:
python -m evaluation.evaluate_fingerprint --dataset-dir datasets/fingerprints/fvc2002/DB1_B --threshold 45.0

# Evaluate on SOCOFing benchmark:
python -m evaluation.evaluate_fingerprint --dataset-dir datasets/fingerprints/socofing/sample_pairs --threshold 40.0
```

This will automatically:
1. Construct **genuine pairs** (different impressions of the same finger, e.g., `101_1` vs `101_2`).
2. Construct **impostor pairs** (impressions from different fingers, e.g., `101_1` vs `102_1`).
3. Compute the match scores and report:
   - Average Genuine Similarity (%)
   - Average Impostor Similarity (%)
   - False Acceptance Rate (FAR / FMR)
   - False Rejection Rate (FRR / FNMR)
   - Overall Verification Accuracy (%)
