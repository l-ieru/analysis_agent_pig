"""
Entry point — run with: python run.py

Loads all backend modules directly from file paths, then starts the server.
This bypasses Python package resolution issues entirely.
"""
import os
import sys
import io
import importlib.util

# -- Fix Windows console encoding (safe fallback) --
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_module(name, filepath):
    """Load a Python module from an absolute file path and register it in sys.modules."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod       # register BEFORE exec, so internal imports resolve
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    # Load all backend modules in dependency order
    _load_module("backend.config",    os.path.join(ROOT_DIR, "backend", "config.py"))
    _load_module("backend.rag_engine", os.path.join(ROOT_DIR, "backend", "rag_engine.py"))
    _load_module("backend.knowledge_builder", os.path.join(ROOT_DIR, "backend", "knowledge_builder.py"))
    _load_module("backend.crawler",   os.path.join(ROOT_DIR, "backend", "crawler.py"))
    main_mod = _load_module("backend.main", os.path.join(ROOT_DIR, "backend", "main.py"))

    app = main_mod.app

    import uvicorn

    print("=" * 60)
    print("[Pig] Pig Farming Industry Analysis Agent v1.0")
    print("=" * 60)
    print("Open http://localhost:8000 in your browser")
    print("API docs: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
