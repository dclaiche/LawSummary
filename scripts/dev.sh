#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Law Summary development servers..."

# Start backend
(
  cd "$PROJECT_DIR/backend"
  echo "[Backend] Starting FastAPI on port 8000..."
  uvicorn main:app --reload --port 8000
) &
BACKEND_PID=$!

# Start frontend
(
  cd "$PROJECT_DIR/frontend"
  echo "[Frontend] Starting Vite on port 5173..."
  npm run dev
) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

echo "Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both servers."

wait
