import shutil
import sys
from pathlib import Path

NON_SOURCES_FILES = [
    ".",
    "..",
    ".git",
    ".github",
    ".gitignore",
    ".venv",
    ".idea",
    "Dockerfile",
    "__pycache__",
    "tests",
]

if __name__ == "__main__":
    source_dir = Path(sys.argv[1])
    dest_dir = Path(__file__).parent / source_dir.name
    dest_dir.mkdir(exist_ok=True)
    for fn in source_dir.iterdir():
        if fn.name in NON_SOURCES_FILES:
            continue
        dest_fn = dest_dir / fn.name
        shutil.copy2(str(fn), str(dest_fn))
