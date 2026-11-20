import hashlib
from unittest.mock import Mock

import pytest

from scripts import download_data as downloader


@pytest.mark.parametrize("valid", [True, False])
def test_pinned_download_validates_bytes_before_replacing(tmp_path, monkeypatch, valid):
    source = tmp_path / "cached.csv"
    source.write_bytes(b"valid" if valid else b"corrupt")
    destination = tmp_path / "raw" / "train.csv"
    destination.parent.mkdir()
    destination.write_bytes(b"previous")
    monkeypatch.setattr(downloader, "SHA256", hashlib.sha256(b"valid").hexdigest())
    download = Mock(return_value=source)
    monkeypatch.setattr(downloader.kagglehub, "dataset_download", download)

    if valid:
        assert downloader.download_data(destination) == destination
        assert destination.read_bytes() == b"valid"
        downloader.download_data(destination)
    else:
        with pytest.raises(ValueError, match="SHA-256 mismatch"):
            downloader.download_data(destination)
        assert destination.read_bytes() == b"previous"

    download.assert_called_once_with(
        "rohitsahoo/sales-forecasting/versions/2", path="train.csv"
    )
    assert list(destination.parent.iterdir()) == [destination]
