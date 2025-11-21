# 阿里云部署优化指南

## 已完成的优化

### 1. 镜像加速
- ✅ Debian APT 源使用阿里云镜像
- ✅ PyPI 使用阿里云镜像
- ✅ 多阶段构建优化（待实现）

### 2. 资源限制
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 3. 日志管理
- 日志滚动：最大 10MB，保留 3 个文件
- 避免磁盘空间耗尽

### 4. 健康检查优化
- Qdrant: TCP 连接检查
- MCP Server: HTTP 健康端点
- 启动等待时间：40-60s

### 5. 安全加固
- 非 root 用户运行
- 只读文件系统（部分）
- 禁止权限提升
- tmpfs 临时目录

### 6. 并发性能
- 线程池：10 workers
- 最大并发：20 请求
- 请求超时：60s

## 生产环境部署建议

### 阿里云 ECS 推荐配置

**基础配置**
- CPU: 2核
- 内存: 4GB
- 带宽: 5Mbps

**进阶配置**（高并发）
- CPU: 4核
- 内存: 8GB
- 带宽: 10Mbps

### 网络配置

1. **安全组设置**
```
入站规则:
- 8001/TCP  (MCP Server)
- 6333/TCP  (Qdrant REST API) - 仅内网访问
- 6334/TCP  (Qdrant gRPC) - 仅内网访问
- 22/TCP    (SSH)
```

2. **Nginx 反向代理**（推荐）
```nginx
upstream mcp_backend {
    server localhost:8001;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://mcp_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }
    
    location /health {
        proxy_pass http://mcp_backend/health;
        access_log off;
    }
}
```

### 监控告警

1. **使用阿里云云监控**
```bash
# CPU 使用率 > 80%
# 内存使用率 > 85%
# 磁盘使用率 > 90%
# 网络流量异常
```

2. **自定义监控脚本**
```bash
#!/bin/bash
# 监控 MCP 服务健康状态
while true; do
    if ! curl -f http://localhost:8001/health > /dev/null 2>&1; then
        # 发送告警
        echo "MCP Server down!" | mail -s "Alert" admin@example.com
        # 自动重启
        docker-compose -f docker-compose.mcp-http.yml restart mem0-mcp-http-server
    fi
    sleep 60
done
```

### 备份策略

1. **Qdrant 数据备份**
```bash
#!/bin/bash
# 每日备份脚本
BACKUP_DIR="/backup/qdrant/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 创建快照
curl -X POST "http://localhost:6333/collections/mem0_alicloud/snapshots"

# 复制数据
docker cp mem0-qdrant:/qdrant/storage $BACKUP_DIR/

# 上传到阿里云 OSS
ossutil cp -r $BACKUP_DIR oss://your-bucket/qdrant-backups/
```

2. **配置文件备份**
```bash
tar czf config-backup-$(date +%Y%m%d).tar.gz \
    app/.env \
    docker-compose.mcp-http.yml \
    app/Dockerfile.mcp-http
```

### 性能优化

1. **环境变量调优**
```bash
# app/.env
MAX_CONCURRENT_REQUESTS=50      # 根据 ECS 配置调整
THREAD_POOL_SIZE=20            # CPU 核心数 * 2-3
REQUEST_TIMEOUT=120            # 增加超时时间

# Qdrant 优化
QDRANT__SERVICE__MAX_REQUEST_SIZE_MB=64
```

2. **系统参数优化**
```bash
# /etc/sysctl.conf
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.ip_local_port_range = 10000 65535
fs.file-max = 100000
```

### 故障排查

1. **查看日志**
```bash
# 服务日志
docker-compose -f docker-compose.mcp-http.yml logs -f --tail=100

# 特定容器日志
docker logs mem0-mcp-http-server --tail=100 -f
docker logs mem0-qdrant --tail=100 -f
```

2. **资源监控**
```bash
# 实时监控
docker stats

# 磁盘使用
df -h
du -sh qdrant_storage/
```

3. **网络测试**
```bash
# 测试连通性
curl -v http://localhost:8001/health
curl -v http://localhost:6333/

# 测试并发
ab -n 100 -c 10 http://localhost:8001/health
```

### 自动化部署

使用 deploy-alicloud.sh 脚本：
```bash
chmod +x deploy-alicloud.sh
./deploy-alicloud.sh
```

### 成本优化

1. **使用按量付费 + 预留实例券**
2. **配置自动伸缩（根据负载）**
3. **使用阿里云容器服务 ACK**（Kubernetes）
4. **OSS 存储分层**（冷热数据分离）

### 高可用方案

1. **多可用区部署**
2. **负载均衡 SLB**
3. **数据库主从复制**（Qdrant 集群模式）
4. **自动故障转移**

## 快速开始

1. 克隆仓库并切换分支
```bash
git clone https://github.com/xingxinonline/landoubao-mem0.git
cd landoubao-mem0
git checkout alicloud-optimization
```

2. 配置环境变量
```bash
cp app/.env.example app/.env
vim app/.env  # 填入 API Keys
```

3. 部署
```bash
./deploy-alicloud.sh
```

4. 验证
```bash
curl http://localhost:8001/health
```
