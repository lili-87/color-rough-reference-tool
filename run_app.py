"""Launch the Color Rough Reference Tool from the repository root."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from color_rough_ref_tool.ui.app import main


if __name__ == "__main__":
    main()
