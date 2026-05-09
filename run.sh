#!/bin/bash
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-your-api-key-here}"
echo "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}"
export PATH="/c/Users/Administrator/AppData/Local/Programs/Python/Python312:/c/Users/Administrator/AppData/Local/Programs/Python/Python312/Scripts:$PATH"
cd "$(dirname "$0")"
python run.py
