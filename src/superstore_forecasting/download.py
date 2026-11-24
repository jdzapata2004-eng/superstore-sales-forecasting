import hashlib
import shutil
from pathlib import Path

import kagglehub

from superstore_forecasting.config import DATASET, FILENAME, SHA256


def download_data(destination: Path) -> Path:
    """Download the pinned snapshot, validate SHA-256, atomically place it.

    Re-running is idempotent: if the destination already holds bytes with the
    expected digest, the network call is skipped.
    """
    destination = Path(destination)

    # Atajo idempotente: destino ya válido → no tocar la red.
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() == SHA256:
            return destination

    cached = Path(kagglehub.dataset_download(DATASET, path=FILENAME))
    digest = hashlib.sha256(cached.read_bytes()).hexdigest()
    if digest != SHA256:
        raise ValueError(f"SHA-256 mismatch: expected {SHA256}, got {digest}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(str(destination) + ".tmp")
    shutil.copyfile(cached, staging)
    staging.replace(destination)
    return destination