#!/bin/bash
# Start 0711 website as a daemon (persists after terminal close)

cd /home/christoph.bertsch/0711/0711-OS/apps/website

# Kill existing process if running
if [ -f /tmp/0711_website.pid ]; then
    OLD_PID=$(cat /tmp/0711_website.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing website process (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
fi

# Start website in background
echo "Starting 0711 website on port 4000..."
nohup npm run dev -- -p 4000 > /tmp/0711_website.log 2>&1 &
WEBSITE_PID=$!
echo $WEBSITE_PID > /tmp/0711_website.pid

echo "✓ Website started (PID: $WEBSITE_PID)"
echo "  Access: http://localhost:4000"
echo "  Logs: tail -f /tmp/0711_website.log"
