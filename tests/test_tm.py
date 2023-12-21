import tempfile
from pathlib import Path

from tm import create_tm, get_next_version


def test_get_next_version():
    next_version = get_next_version("TM0001_test")
    assert next_version.startswith("v")
    assert next_version[1:].isdigit()


def test_create_tm():
    with tempfile.TemporaryDirectory() as tmp_dir:
        align_dir = Path(tmp_dir)
        align_fn = align_dir / "TM0001_test.txt"
        align_fn.write_text("bo sent\ten sent")
        text_pair = {
            "text_id": "0001_test",
            "bo_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-bo.txt",
            "en_file_url": "https://raw.githubusercontent.com/OpenPecha/tibetan-aligner/main/tests/data/text-en.txt",
        }

        tm_url = create_tm(align_fn, text_pair)

        assert tm_url.startswith("https://github.com")
