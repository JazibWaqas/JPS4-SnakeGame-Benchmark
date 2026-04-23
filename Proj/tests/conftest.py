import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODE = os.path.join(ROOT, "src", "Snake Game Code")

for path in (ROOT, CODE):
    if path not in sys.path:
        sys.path.insert(0, path)
