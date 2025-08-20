#!/bin/bash
# Painel do Clima Server Management Script

case "$1" in
    start)
        echo "Starting Painel do Clima server..."
        cd "$(dirname "$0")"
        python backend/serve.py
        ;;
    dev)
        echo "Starting Painel do Clima server in development mode..."
        cd "$(dirname "$0")"
        uvicorn backend.serve:app --reload --host 0.0.0.0 --port 8000
        ;;
    stop)
        echo "Stopping server..."
        pkill -f "python.*serve.py"
        pkill -f "uvicorn.*serve"
        echo "Server stopped."
        ;;
    status)
        if pgrep -f "serve.py\|uvicorn.*serve" > /dev/null; then
            echo "Server is running"
            echo "Access: http://localhost:8000"
        else
            echo "Server is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|dev|stop|status}"
        echo ""
        echo "Commands:"
        echo "  start  - Start the production server"
        echo "  dev    - Start development server with auto-reload"
        echo "  stop   - Stop the server"
        echo "  status - Check if server is running"
        exit 1
        ;;
esac
