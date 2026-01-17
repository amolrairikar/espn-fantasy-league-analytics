"""Compatibility shim exposing `lambda_layer.common_utils` as `common_utils`.

This allows modules that import `common_utils.*` to work during local
tests (the actual code lives under `lambda_layer.common_utils`).
"""

import importlib
import sys

try:
    _mod = importlib.import_module("lambda_layer.common_utils")
    # Replace the current shim module in sys.modules with the real module so
    # that imports like `common_utils.batch_write_dynamodb` resolve correctly
    # via the real package's __path__.
    sys.modules["common_utils"] = _mod
    # Update this module's globals to mirror the real package (best-effort).
    globals().update({k: getattr(_mod, k) for k in dir(_mod) if not k.startswith("__")})
except Exception:
    # If import fails, leave an empty module; tests may patch submodules.
    pass
