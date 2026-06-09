cat > deploy.sh << 'SCRIPT'
#!/bin/bash
set -e

echo " Starting Blue-Green Deployment..."

# 1. Determine current active port
if [ -f active_port.txt ]; then
    CURRENT_PORT=$(cat active_port.txt)
else
    CURRENT_PORT=8001
    echo "8001" > active_port.txt
fi

# 2. Determine new port
if [ "$CURRENT_PORT" == "8001" ]; then
    NEW_PORT=8002
    NEW_ENV="green"
    OLD_ENV="blue"
else
    NEW_PORT=8001
    NEW_ENV="blue"
    OLD_ENV="green"
fi

echo "🔵 Current: $OLD_ENV (Port $CURRENT_PORT)"
echo "🟢 Deploying to: $NEW_ENV (Port $NEW_PORT)"

# 3. Build & Start new environment
echo "📦 Building new image..."
sudo docker compose build app-$NEW_ENV

echo "⏳ Starting $NEW_ENV..."
sudo docker compose up -d app-$NEW_ENV

# 4. Health check
echo " Waiting for $NEW_ENV to be healthy..."
for i in {1..30}; do
    if curl -s -f http://127.0.0.1:$NEW_PORT/docs > /dev/null; then
        echo "✅ $NEW_ENV is healthy!"
        break
    fi
    echo " Waiting... ($i/30)"
    sleep 2
done

# 5. Switch traffic via Nginx
echo "🔄 Switching traffic to port $NEW_PORT..."
sudo sed -i "s/server 127.0.0.1:[0-9]*/server 127.0.0.1:$NEW_PORT/" /etc/nginx/conf.d/fastapi.conf
sudo nginx -t && sudo systemctl reload nginx

# 6. Update state file
echo "$NEW_PORT" > active_port.txt

# 7. Stop old environment
echo " Stopping old $OLD_ENV environment..."
sudo docker compose stop app-$OLD_ENV
sudo docker compose rm -f app-$OLD_ENV

echo "✅ Blue-Green deployment complete! Live on port $NEW_PORT"
SCRIPT

chmod +x deploy.sh