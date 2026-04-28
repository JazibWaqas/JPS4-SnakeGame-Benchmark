import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALGO = os.path.join(ROOT, "src", "algorithms")
GAME = os.path.join(ROOT, "src", "game")

for path in (ROOT, ALGO, GAME):
    if path not in sys.path:
        sys.path.insert(0, path)
