import sys
import os

# Adds Back-end/app/ to sys.path so test files can import as:
#   from schemas.X import ...
# While schema files themselves use:
#   from app.schemas.base import CustomBaseModel  (resolved via Back-end/ root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
