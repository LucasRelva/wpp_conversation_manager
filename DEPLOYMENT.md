# Production Deployment Guide

## Prerequisites
- Docker & Docker Compose
- Linux server (Ubuntu 20.04+ recommended)
- Domain name (for SSL)
- Cloud provider account (AWS, GCP, DigitalOcean, etc.)

## Deployment Options

### Option 1: Docker Compose on Single Server

#### Step 1: Prepare Server
```bash
# SSH into server
ssh user@your-server-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker & Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install -y docker-compose

# Create app directory
mkdir -p /opt/handoff-dashboard
cd /opt/handoff-dashboard
```

#### Step 2: Clone Repository
```bash
git clone <your-repo> .
```

#### Step 3: Configure Environment
```bash
# Production environment
cat > backend/.env << EOF
REDIS_URL=redis://redis:6379
API_HOST=0.0.0.0
API_PORT=8000
WHATSAPP_API_TOKEN=your_token_here
TELEGRAM_API_TOKEN=your_token_here
FRONTEND_URL=https://your-domain.com
EOF

cat > frontend/.env << EOF
REACT_APP_API_URL=https://your-domain.com/api
REACT_APP_WS_URL=wss://your-domain.com
EOF
```

#### Step 4: Setup SSL with Let's Encrypt
```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificates
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  --agree-tos \
  --email admin@your-domain.com
```

#### Step 5: Setup Nginx Reverse Proxy
```bash
sudo tee /etc/nginx/sites-available/handoff << EOF
upstream api {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # API
    location /api/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/handoff /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### Step 6: Start Services
```bash
cd /opt/handoff-dashboard

# Build and start
docker-compose up -d

# Check status
docker-compose logs -f
docker-compose ps
```

#### Step 7: Monitor
```bash
# View logs
docker-compose logs -f api
docker-compose logs -f redis
docker-compose logs -f frontend

# Check Redis
docker exec handoff_redis redis-cli INFO

# Check API health
curl https://your-domain.com/health
```

#### Step 8: Backups
```bash
# Setup automated backup
crontab -e

# Add daily backup at 2 AM
0 2 * * * docker exec handoff_redis redis-cli BGSAVE && \
  sudo tar -czf /backups/redis_$(date +\%Y\%m\%d).tar.gz \
  /var/lib/docker/volumes/*/redis_data
```

### Option 2: Kubernetes Deployment

#### Prerequisites
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

#### Create Kubernetes Manifests

**redis-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

**api-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: your-registry/handoff-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: redis://redis:6379
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
```

**frontend-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/handoff-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: https://your-domain.com/api
        - name: REACT_APP_WS_URL
          value: wss://your-domain.com
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  selector:
    app: frontend
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 3000
```

**ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: handoff-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/websocket-services: api
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - your-domain.com
    secretName: handoff-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

#### Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace handoff

# Apply manifests
kubectl apply -f redis-deployment.yaml -n handoff
kubectl apply -f api-deployment.yaml -n handoff
kubectl apply -f frontend-deployment.yaml -n handoff
kubectl apply -f ingress.yaml -n handoff

# Monitor
kubectl get pods -n handoff
kubectl logs -f deployment/api -n handoff
```

## Production Checklist

### Security
- [ ] HTTPS/SSL enabled
- [ ] Redis password authentication
- [ ] API authentication implemented
- [ ] Webhook signature verification
- [ ] Rate limiting enabled
- [ ] CORS configured properly
- [ ] Firewall rules in place
- [ ] Regular security updates

### Monitoring
- [ ] Application metrics collected
- [ ] Error tracking (Sentry/similar)
- [ ] Log aggregation (ELK/Datadog)
- [ ] Database monitoring
- [ ] Uptime monitoring
- [ ] Alerts configured

### Backups
- [ ] Daily Redis backups
- [ ] Backup verification tested
- [ ] Backup storage redundant
- [ ] Restore procedure documented
- [ ] Off-site backups

### Performance
- [ ] Load testing completed
- [ ] Database indexes optimized
- [ ] Caching implemented
- [ ] CDN configured
- [ ] Database sharding planned

### Capacity
- [ ] CPU/memory headroom
- [ ] Storage capacity
- [ ] Network bandwidth
- [ ] Scaling plan documented
- [ ] Database replication

### Documentation
- [ ] Runbook created
- [ ] Deployment documented
- [ ] Disaster recovery plan
- [ ] Contact information
- [ ] Troubleshooting guide

## Scaling

### Horizontal Scaling (Multiple Instances)

#### With Docker Compose
```bash
# Use docker-compose with scaling
docker-compose up -d --scale api=3
```

#### With Kubernetes
```bash
# Scale replicas
kubectl scale deployment api --replicas=5 -n handoff
```

### Vertical Scaling
```bash
# Increase resource limits in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Maintenance

### Regular Tasks
```bash
# Update images monthly
docker pull python:3.11-slim
docker pull node:18-alpine
docker pull redis:7-alpine

# Rebuild images
docker-compose build --no-cache

# Restart services
docker-compose down
docker-compose up -d

# Check health
docker-compose ps
curl https://your-domain.com/health
```

### Database Maintenance
```bash
# Monitor Redis memory
docker exec handoff_redis redis-cli INFO memory

# Clear old data
docker exec handoff_redis redis-cli FLUSHDB ASYNC

# Backup
docker exec handoff_redis redis-cli BGSAVE
```

## Troubleshooting Production

### Service Down
```bash
# Check status
docker-compose ps

# Restart all
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs -f --tail=100
```

### High Memory Usage
```bash
# Check Redis
docker exec handoff_redis redis-cli INFO memory

# Check API
docker top handoff_api
```

### Slow Performance
```bash
# Check Redis latency
docker exec handoff_redis redis-cli --latency

# Check API logs for slow queries
docker-compose logs api | grep "duration"
```

## Support & SLA

Implement monitoring and alerting:
- Uptime target: 99.9%
- Response time: < 500ms (p95)
- Error rate: < 0.1%
- Support: 24/7 alerting

Monitor and maintain to meet SLA targets.
