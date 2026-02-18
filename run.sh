#!/bin/bash
set -e

echo "Starting Hindsight API..."
hindsight-api &
HINDSIGHT_PID=$!

# Wait for API to be ready
for i in $(seq 1 30); do
    if curl -s http://localhost:8888/health > /dev/null 2>&1; then
        echo "Hindsight API ready."
        break
    fi
    sleep 1
done

echo "Starting Streamlit app..."
streamlit run app.py --server.headless true

# Cleanup
kill $HINDSIGHT_PID 2>/dev/null
