#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy.sh — Blue-Green Deployment Script
# Runs on EC2 server. Called by GitHub Actions after git pull.
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "🚀 Starting Blue-Green Deployment..."

# ── Step 1: Determine current active port ────────────────────────────────────
if [ -f active_port.txt ]; then
    CURRENT_PORT=$(cat active_port.txt)
else
    CURRENT_PORT=8001
    echo "8001" > active_port.txt
fi

# ── Step 2: Determine new target ─────────────────────────────────────────────
if [ "$CURRENT_PORT" == "8001" ]; then
    NEW_PORT=8002
    NEW_ENV="green"
    OLD_ENV="blue"
else
    NEW_PORT=8001
    NEW_ENV="blue"
    OLD_ENV="green"
fi

echo "🔵 Currently live: $OLD_ENV (port $CURRENT_PORT)"
echo "🟢 Deploying to:   $NEW_ENV (port $NEW_PORT)"

# ── Step 3: Build new image ───────────────────────────────────────────────────
echo "📦 Building new Docker image..."
sudo docker compose build app-$NEW_ENV

# ── Step 4: Start new container ───────────────────────────────────────────────
echo "⏳ Starting $NEW_ENV container..."
sudo docker compose up -d app-$NEW_ENV

# ── Step 5: Health check (wait up to 60 seconds) ─────────────────────────────
echo "🔍 Waiting for $NEW_ENV to be healthy..."
for i in {1..30}; do
    if curl -s -f http://127.0.0.1:$NEW_PORT/ > /dev/null 2>&1; then
        echo "✅ $NEW_ENV is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Health check failed after 60s. Aborting deployment."
        sudo docker compose stop app-$NEW_ENV
        exit 1
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

# ── Step 6: Switch Nginx traffic to new container ────────────────────────────
echo "🔄 Switching traffic to $NEW_ENV (port $NEW_PORT)..."
sudo sed -i "s/proxy_pass http:\/\/127.0.0.1:[0-9]*/proxy_pass http:\/\/127.0.0.1:$NEW_PORT/" /etc/nginx/conf.d/fastapi.conf
sudo nginx -t && sudo systemctl reload nginx

# ── Step 7: Save new active port ─────────────────────────────────────────────
echo "$NEW_PORT" > active_port.txt
echo "✅ Traffic now live on $NEW_ENV (port $NEW_PORT)"

# ── Step 8: Stop old container ────────────────────────────────────────────────
echo "🛑 Stopping old $OLD_ENV (port $CURRENT_PORT)..."
sudo docker compose stop app-$OLD_ENV
sudo docker compose rm -f app-$OLD_ENV

# ── Step 9: Clean up unused images ────────────────────────────────────────────
sudo docker system prune -f

echo ""
echo "✅ Blue-Green deployment complete!"
echo "   Live:    $NEW_ENV on port $NEW_PORT"
echo "   Standby: $OLD_ENV stopped"
