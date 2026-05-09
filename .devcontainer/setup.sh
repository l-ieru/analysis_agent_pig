#!/bin/bash
set -e

echo "============================================"
echo "  Pig Farming Analysis Agent - Setup"
echo "============================================"
echo ""

# Install Python dependencies
echo "[1/2] Installing dependencies..."
pip install -r backend/requirements.txt -q
echo "  Done."

# Build knowledge base
echo "[2/2] Building knowledge base..."
python -c "
import sys
sys.path.insert(0, '.')
from backend.knowledge_builder import build_knowledge_base
n = build_knowledge_base()
print(f'  Knowledge base ready: {n} documents indexed')
"

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "  Start the server:"
echo "    python run.py"
echo ""
echo "  Then visit: http://localhost:8000"
echo ""
echo "  Or use the forwarded port in the PORTS tab."
echo "============================================"
