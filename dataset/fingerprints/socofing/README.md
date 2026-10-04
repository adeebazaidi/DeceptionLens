# SOCOFing (Sokoto Coventry Fingerprint Dataset) Guide

This directory integrates the **SOCOFing** fingerprint benchmark into DeceptionLens for evaluating minutiae matching against realistic biometric alterations (rotations, obliterations, and scars).

---

## 1. Directory Structure

```text
backend/datasets/fingerprints/socofing/
├── README.md                      <-- This documentation
├── generate_socofing_samples.py   <-- Generator for synthetic SOCOFing BMP pairs
├── sample_pairs/                  <-- Bundled demonstration pairs (Real & Altered)
│   ├── 1__M_Left_index_finger.BMP
│   ├── 1__M_Left_index_finger_CR.BMP     (Central Rotation)
│   ├── 1__M_Left_index_finger_Obl.BMP    (Obliteration)
│   ├── 1__M_Left_index_finger_Zcut.BMP   (Z-Cut)
│   ├── 2__M_Left_index_finger.BMP        (Impostor Real)
│   ├── 2__M_Left_index_finger_CR.BMP
│   ├── 3__F_Right_thumb_finger.BMP
│   └── 3__F_Right_thumb_finger_CR.BMP
└── real_dataset/                  <-- Extract full Kaggle SOCOFing here (optional)
    ├── Real/
    └── Altered/
        ├── Altered-Easy/
        ├── Altered-Medium/
        └── Altered-Hard/
```

---

## 2. Dataset Overview: SOCOFing

* **Paper**: *Biometric Technology Today*, Sokoto Coventry Fingerprint Dataset.
* **Subjects**: 600 African subjects, 10 impressions per subject (6,000 real impressions).
* **Format**: 8-bit Grayscale Windows BMP, resolution 96 × 103 pixels.
* **Naming Scheme**:
  - **Real**: `<SubjectID>__<Gender>_<Hand>_<Finger>_finger.BMP`  
    *(e.g., `1__M_Left_index_finger.BMP`)*
  - **Altered**: `<SubjectID>__<Gender>_<Hand>_<Finger>_finger_<AlterationType>.BMP`  
    - `CR`: Central Rotation (core rotated by 15°–45°)
    - `Obl`: Obliteration (scratches / erased tissue)
    - `Zcut`: Z-Cut (surgical / traumatized tissue displacement)

---

## 3. How to Obtain Full Dataset

1. Download the full 6,000+ image dataset from Kaggle:
   👉 [kaggle.com/datasets/ruizgara/socofing](https://www.kaggle.com/datasets/ruizgara/socofing)
2. Extract the `SOCOFing` folder into:
   ```text
   backend/datasets/fingerprints/socofing/real_dataset/
   ```

---

## 4. Running Benchmark Evaluation

Run the automated evaluation on the bundled demonstration sample pairs or the full dataset:

```bash
cd backend

# Run on bundled sample pairs:
python -m evaluation.evaluate_fingerprint --dataset-dir datasets/fingerprints/socofing/sample_pairs --threshold 40.0

# Run on full downloaded dataset:
python -m evaluation.evaluate_fingerprint --dataset-dir datasets/fingerprints/socofing/real_dataset --threshold 40.0
```
