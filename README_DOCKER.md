# Docker 部署教程

> **功能简介**：解决 Alist 挂载strm文件需要进行打开相应的文件夹才能同步到strm文件到本地映射的文件夹。定期扫描 WebDAV 变更，确保 Emby/Plex 媒体库实时同步。

### 方式一：Docker CLI

直接运行以下命令即可启动：

```bash
docker run -d \
  --name webdav-monitor \
  --restart always \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e JWT_SECRET=your_secure_random_string_here \
  -e TZ=Asia/Shanghai \
  liheng6668/webdav-monitor:latest
```

启动后访问 `http://localhost:8000`。
默认账号：`admin` / `admin` (请立即修改)

### 方式二：Docker Compose (推荐)

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  webdav-monitor:
    image: liheng6668/webdav-monitor:latest
    container_name: webdav-monitor
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - JWT_SECRET=your_secure_random_string_here  # [必填] 修改为随机字符串
      - TZ=Asia/Shanghai
```

运行：`docker-compose up -d`

---

### 📂 挂载卷说明

| 宿主机路径 | 容器路径 | 用于存储 |
|------------|----------|----------|
| `./data`   | `/app/data` | 配置文件、任务状态和日志 (必须挂载) |

### ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `JWT_SECRET` | **[必填]** 安全密钥，请设置一个长随机字符串 | (无) |
| `TZ` | 容器时区 | `UTC` |

<br>

---

# Docker Deployment Guide

> **Intro**: Solves the issue where Alist doesn't auto-update cloud drive changes. Periodically scans WebDAV and triggers Alist refresh to keep your Emby/Plex library in sync.

### Option 1: Docker CLI

```bash
docker run -d \
  --name webdav-monitor \
  --restart always \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e JWT_SECRET=your_secure_random_string_here \
  -e TZ=Asia/Shanghai \
  liheng6668/webdav-monitor:latest
```

Dashboard: `http://localhost:8000`
Default Login: `admin` / `admin`

### Option 2: Docker Compose (Recommended)

```yaml
version: '3.8'

services:
  webdav-monitor:
    image: liheng6668/webdav-monitor:latest
    container_name: webdav-monitor
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - JWT_SECRET=your_secure_random_string_here  # [Required] Change me!
      - TZ=Asia/Shanghai
```

Run: `docker-compose up -d`

---

### 📂 Volumes

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data`  | `/app/data`    | Config, State, Logs (Must mount) |

### ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | **[Required]** Secret key for security. | (None) |
| `TZ` | Timezone. | `UTC` |
