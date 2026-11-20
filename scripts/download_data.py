"""Download the pinned, verified Superstore CSV."""

import argparse
import hashlib
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

import kagglehub

from superstore_forecasting.config import DATASET, FILENAME, RAW_PATH, SHA256


def download_data(destination: Path = RAW_PATH) -> Path:
    """Publish a verified copy atomically in the destination directory."""
    if destination.is_file():
        with destination.open("rb") as existing:
            if hashlib.file_digest(existing, "sha256").hexdigest() == SHA256:
                return destination

    downloaded = Path(kagglehub.dataset_download(DATASET, path=FILENAME))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            with downloaded.open("rb") as source:
                shutil.copyfileobj(source, temporary)
        with temporary_path.open("rb") as staged:
            actual = hashlib.file_digest(staged, "sha256").hexdigest()
        if actual != SHA256:
            raise ValueError(f"SHA-256 mismatch: expected {SHA256}, received {actual}.")
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=RAW_PATH)
    print(download_data(parser.parse_args().output))


if __name__ == "__main__":
    main()
