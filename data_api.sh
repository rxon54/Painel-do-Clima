#!/bin/bash

# Painel do Clima Data API Service Management Script

API_SERVICE_FILE="backend/data_api_service.py"
PID_FILE="/tmp/painel_data_api.pid"
LOG_FILE="backend/data_api_service.log"

case "$1" in
    start)
        echo "Starting Painel do Clima Data API Service..."
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Service is already running with PID $(cat $PID_FILE)"
            exit 1
        fi
        
        cd "$(dirname "$0")"
        nohup python "$API_SERVICE_FILE" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "Data API Service started with PID $!"
        echo "API documentation available at: http://localhost:8001/docs"
        echo "Health check: http://localhost:8001/health"
        echo "Logs: tail -f $LOG_FILE"
        ;;
        
    stop)
        echo "Stopping Painel do Clima Data API Service..."
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "Data API Service stopped"
            else
                echo "Service was not running"
                rm -f "$PID_FILE"
            fi
        else
            echo "PID file not found. Service may not be running."
        fi
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "Data API Service is running with PID $PID"
                echo "API docs: http://localhost:8001/docs"
            else
                echo "Service is not running (stale PID file)"
                rm -f "$PID_FILE"
            fi
        else
            echo "Data API Service is not running"
        fi
        ;;
        
    dev)
        echo "Starting Data API Service in development mode..."
        cd "$(dirname "$0")"
        python "$API_SERVICE_FILE"
        ;;
        
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "Log file not found: $LOG_FILE"
        fi
        ;;
        
    test)
        echo "Testing Data API Service endpoints..."
        echo "Health check:"
        curl -s http://localhost:8001/health | python -m json.tool
        echo -e "\nIndicator count:"
        curl -s http://localhost:8001/api/v1/indicadores/count | python -m json.tool
        echo -e "\nAll indicators (first 3):"
        curl -s "http://localhost:8001/api/v1/indicadores/estrutura?limit=3" | python -m json.tool
        echo -e "\nFiltered by sector (Saúde, first 2):"
        curl -s "http://localhost:8001/api/v1/indicadores/estrutura?setor=Sa%C3%BAde&limit=2" | python -m json.tool
        echo -e "\nSample indicator (ID 2):"
        curl -s http://localhost:8001/api/v1/indicadores/estrutura/2 | python -m json.tool
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|dev|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Data API service in background"
        echo "  stop    - Stop the Data API service"
        echo "  restart - Restart the Data API service"
        echo "  status  - Check if the service is running"
        echo "  dev     - Run in development mode (foreground)"
        echo "  logs    - Show live logs"
        echo "  test    - Test API endpoints"
        exit 1
        ;;
esac
