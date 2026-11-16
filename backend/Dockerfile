# DeceptionLens backend — Linux container image.
#
# Running in Linux avoids Windows Smart App Control blocking spaCy's compiled
# extensions, and gives every developer the same environment.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System libraries required by OpenCV
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch (pulled in by EasyOCR) — avoids multi-GB CUDA wheels.
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

# Bake models into the image so the first request does not download them.
RUN python -m spacy download en_core_web_sm \
    && python -c "import easyocr; easyocr.Reader(['en'], gpu=False, verbose=False)"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
