"""Allow running hyprbind as a module: python -m hyprbind"""

import sys
from hyprbind.main import main

if __name__ == "__main__":
    sys.exit(main())
