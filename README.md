# Docker & Docker Swarm: Build, Push to Docker Hub, and Deploy to AWS EC2

**Course**: Advanced Cloud Computing  
**Student / Maintainer**: `lihengkh`  
**GitHub Repository**: [https://github.com/lihengsomkh/adv_clouds_homework1](https://github.com/lihengsomkh/adv_clouds_homework1)  
**Docker Hub Repository**: [https://hub.docker.com/r/lihengkh/homework](https://hub.docker.com/r/lihengkh/homework)  

---

## 📋 Table of Contents
1. [Project Overview & Architecture](#project-overview--architecture)
2. [Repository Structure](#repository-structure)
3. [Part 1: Docker Compose (20 Pts)](#part-1-docker-compose-20-pts)
4. [Part 2: Docker Swarm (20 Pts)](#part-2-docker-swarm-20-pts)
5. [Part 3: Push Image to Docker Hub (25 Pts)](#part-3-push-image-to-docker-hub-25-pts)
6. [Part 4: Deploy to AWS EC2 (25 Pts)](#part-4-deploy-to-aws-ec2-25-pts)
7. [Part 5: Deliverables & Screenshot Checklist (10 Pts)](#part-5-deliverables--screenshot-checklist-10-pts)

---

## 🏗️ Project Overview & Architecture

This project demonstrates a production-grade containerized lifecycle:
- **Application**: Python Flask web application (`cloud-counter`) with real-time visitor counter, container ID resolution, dynamic environment handling, and data persistence test form.
- **Backing Store**: Redis 7 Alpine cache & database with append-only file (`AOF`) persistence.
- **Local Multi-Container Orchestration**: Docker Compose with custom user-defined bridge network (`counter-net`) and named volume (`redis_data`).
- **Cluster Orchestration**: Docker Swarm stack (`docker-stack.yml`) with declarative replicas, resource reservations/limits, routing mesh, and auto-recovery self-healing.
- **Image Registry**: Automated versioning on Docker Hub (`v1` and `v2`).
- **Cloud Infrastructure**: AWS EC2 Free Tier deployment with custom Security Group (SSH port 22 restricted to owner IP, public HTTP port 80).

```
[ Web Browser / Client ]
            │
            ▼ (Port 5000 / Port 80)
┌──────────────────────────────────────────────┐
│  Docker / Docker Swarm (counter-net network) │
│                                              │
│   ┌──────────────────────────────────────┐   │
│   │  Flask Web Service (counter-web)     │   │
│   │  lihengkh/homework:v1 / :v2     │   │
│   └──────────────────┬───────────────────┘   │
│                      │                       │
│                      ▼ (Redis protocol 6379) │
│   ┌──────────────────────────────────────┐   │
│   │  Redis 7 Cache (counter-redis)       │   │
│   └──────────────────┬───────────────────┘   │
│                      │                       │
└──────────────────────┼───────────────────────┘
                       ▼
         [ Named Volume: redis_data ]
```

---

## 📂 Repository Structure

```
.
├── app/
│   ├── app.py              # Flask web application logic & UI
│   ├── requirements.txt    # Python dependencies (flask, redis)
│   ├── Dockerfile          # Release v1.0 Docker build definition
│   └── Dockerfile.v2       # Release v2.0 Docker build definition
├── docker-compose.yml      # Local Docker Compose multi-service definition
├── docker-stack.yml        # Docker Swarm cluster stack definition
├── screenshots/            # Directory for assignment submission screenshots
│   ├── screenshot-a.png    # Part 1: Compose running at localhost:5000
│   ├── screenshot-b.png    # Part 2: Swarm 3 active replicas
│   ├── screenshot-c.png    # Part 3: Docker Hub tags v1 and v2
│   └── screenshot-d.png    # Part 4: Live AWS EC2 public IP browser access
├── .gitignore
└── README.md
```

---

## 🚀 Part 1: Docker Compose (20 Pts)

### 1. Requirements Met
- **2 Interconnected Services**: `web` (Flask) and `redis` (Redis 7).
- **Custom User-Defined Bridge Network**: `counter-net` (`driver: bridge`).
- **Named Volume**: `redis_data` mounted at `/data` on Redis.

### 2. Execution Commands

#### Step 1: Start the Multi-Container Stack
```bash
docker compose up -d
```

Verify containers are running:
```bash
docker compose ps
```

#### Step 2: Verify Web App Response
Open your browser at `http://localhost:5000` or run:
```bash
# In PowerShell:
Invoke-RestMethod -Uri "http://localhost:5000/api/info"

# In Bash / curl:
curl -s http://localhost:5000/api/info
```

#### Step 3: Test and Prove Data Persistence
1. Navigate to `http://localhost:5000`.
2. In the **"Data Persistence Test"** input box, enter `Homework Test Note #1` and click **Save**.
3. Confirm the note appears under *Persisted Items* and visit count increments.
4. Stop and remove the containers and network (named volume is preserved):
   ```bash
   docker compose down
   ```
5. Restart the stack:
   ```bash
   docker compose up -d
   ```
6. Refresh `http://localhost:5000` or query the API:
   ```bash
   # In PowerShell:
   (Invoke-RestMethod -Uri "http://localhost:5000/api/info").notes
   ```
   **Verification**: The previously entered note `Homework Test Note #1` and previous visit count remain intact!

---

## 🐝 Part 2: Docker Swarm (20 Pts)

### 1. Requirements Met
- Single-node Swarm initialization.
- Swarm stack file `docker-stack.yml` with `deploy:` block defining replicas, restart policy, and CPU/memory limits.
- Scale web application to 3 active replicas.
- Auto-recovery / self-healing demonstration via forced task termination.

### 2. Execution Commands

#### Step 1: Initialize Docker Swarm (if not already active)
```bash
docker swarm init
```
*(If already initialized, Docker will notify you that the node is already part of a swarm).*

#### Step 2: Clean up Compose Port 5000 before Swarm Deploy
```bash
docker compose down
```

#### Step 3: Deploy the Stack to Swarm
```bash
docker stack deploy -c docker-stack.yml app-stack
```

Verify stack services:
```bash
docker service ls
```

Inspect service tasks:
```bash
docker service ps app-stack_web
```

#### Step 4: Scale to 3 Replicas
```bash
docker service scale app-stack_web=3
```

Verify all 3 replicas are running:
```bash
docker service ps app-stack_web
```
> **Capture Screenshot (b) here**: Show all 3 tasks in `Running` state.

#### Step 5: Test Swarm Self-Healing / Auto-Recovery
Find the container ID of one of the 3 running web tasks:
```bash
# In PowerShell:
docker ps --filter "name=app-stack_web" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
```

Forcefully kill one task container (replace `<container-id>` with one of the returned IDs):
```bash
docker rm -f <container-id>
```

Immediately inspect the service tasks again:
```bash
docker service ps app-stack_web
```
**Observation**: Swarm detects the terminated task (exit code 137 / non-zero), marks it as `Shutdown` or `Failed`, and automatically schedules and starts a brand new replacement container to restore the desired state of 3 replicas!

#### Step 6: Swarm Teardown (when finished testing)
```bash
docker stack rm app-stack
```

---

## 🐳 Part 3: Push Image to Docker Hub (25 Pts)

### 1. Requirements Met
- Build and tag custom web app image with Docker Hub username: `lihengkh/homework:v1`.
- Push `v1` to Docker Hub as a public repository.
- Introduce a visible change (release header, theme badge, title), build and tag as `lihengkh/homework:v2`, and push to Docker Hub.
- Clean pull test without local cache.

### 2. Execution Commands

#### Step 1: Log in to Docker Hub
```bash
docker login
```
Enter your Docker Hub username (`lihengkh`) and Personal Access Token or password.

#### Step 2: Build & Push Release `v1`
```bash
# Build v1 image:
docker build -f app/Dockerfile -t lihengkh/homework:v1 app

# Push v1 to Docker Hub:
docker push lihengkh/homework:v1
```

#### Step 3: Build & Push Release `v2` (Visible Changes)
Release `v2` updates the header and badge to "Release v2.0 - AWS EC2 Cloud Release" with emerald accents:
```bash
# Build v2 image:
docker build -f app/Dockerfile.v2 -t lihengkh/homework:v2 app

# Push v2 to Docker Hub:
docker push lihengkh/homework:v2
```

#### Step 4: Verify Repository on Docker Hub
1. Visit: [https://hub.docker.com/r/lihengkh/homework/tags](https://hub.docker.com/r/lihengkh/homework/tags)
2. Ensure the repository visibility is set to **Public**.
3. Confirm both `v1` and `v2` tags are listed.
> **Capture Screenshot (c) here**: The Docker Hub repository tags page showing `v1` and `v2`.

#### Step 5: Test Pulling Without Local Cache
```bash
# Remove local image:
docker rmi lihengkh/homework:v2

# Pull fresh from Docker Hub:
docker pull lihengkh/homework:v2
```

---

## ☁️ Part 4: Deploy to AWS EC2 (25 Pts)

### 1. Requirements Met
- Launch an AWS Free Tier EC2 instance (Amazon Linux 2023 or Ubuntu 24.04 LTS).
- Security Group inbound rules:
  - SSH (port 22): restricted to `My IP`.
  - HTTP (port 80): accessible from `0.0.0.0/0`.
- Install and enable Docker daemon (`sudo systemctl enable --now docker`).
- Pull and run container: `docker run -d -p 80:5000 lihengkh/homework:v2`.
- Verify browser access via `http://3.27.36.75  # Live deployed instance IP`.
- Terminate EC2 instance after submission.

### 2. Step-by-Step Instructions

#### Step 1: Launch EC2 Instance (AWS Console)
1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/).
2. Navigate to **EC2** &rarr; **Launch Instance**.
3. **Name**: `Homework-Docker-EC2`.
4. **AMI**: **Amazon Linux 2023 AMI** (Free tier eligible) or **Ubuntu 24.04 LTS**.
5. **Instance type**: `t2.micro` (or `t3.micro` depending on region, Free tier eligible).
6. **Key pair**: Select an existing key pair or create a new one (download `.pem` file).
7. **Network settings / Security Group**:
   - Create a new security group named `docker-ec2-sg`.
   - **Rule 1 (SSH)**: Type `SSH`, Port `22`, Source: **My IP** (never open port 22 to 0.0.0.0/0).
   - **Rule 2 (HTTP)**: Type `HTTP`, Port `80`, Source: **Anywhere (0.0.0.0/0)**.
8. Click **Launch Instance**.

#### Step 2: Connect to the EC2 Instance via SSH
From your local terminal (Windows PowerShell or macOS/Linux Terminal):
```bash
# For Amazon Linux 2023:
ssh -i "path/to/your-key.pem" ec2-user@<ec2-public-ip>

# For Ubuntu:
# ssh -i "path/to/your-key.pem" ubuntu@<ec2-public-ip>
```

#### Step 3: Install & Start Docker on EC2

**On Amazon Linux 2023:**
```bash
# Update packages
sudo dnf update -y

# Install Docker
sudo dnf install -y docker

# Enable and start Docker service
sudo systemctl enable --now docker

# (Optional) Allow ec2-user to run docker without sudo
sudo usermod -aG docker ec2-user
newgrp docker
```

**On Ubuntu 24.04 LTS (alternative):**
```bash
sudo apt update -y
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
newgrp docker
```

#### Step 4: Run the Published Container from Docker Hub
```bash
docker run -d -p 80:5000 --name web-v2 lihengkh/homework:v2
```

Verify container is running on EC2:
```bash
docker ps
```

#### Step 5: Test and Verify Live Access
1. Open a web browser on your personal computer / laptop.
2. Visit:
   ```
   http://<ec2-public-ip>
   ```
   *(Note: Use `http://`, not `https://`).*
3. You will see the live application displaying **Release v2.0 - AWS EC2 Cloud Release** with the container ID of the EC2 task!
> **Capture Screenshot (d) here**: Full browser window showing the address bar with `http://<ec2-public-ip>` and the live web page.

#### Step 6: ⚠️ Clean Up to Prevent AWS Charges
When your test and screenshots are complete:
1. Go to AWS Console &rarr; **EC2 Instances**.
2. Select `Homework-Docker-EC2`.
3. Click **Instance state** &rarr; **Terminate instance** (or **Stop instance**).

---

## 📸 Part 5: Deliverables & Screenshot Checklist (10 Pts)

### 1. Screenshot Checklist

| Screenshot | Description | Target File | Status |
|:---:|:---|:---|:---:|
| **(a)** | Web app running locally via Docker Compose (`http://localhost:5000`) | `screenshots/screenshot-a.png` | [ ] Pending Capture |
| **(b)** | Terminal displaying `docker service ps app-stack_web` with 3 active replicas | `screenshots/screenshot-b.png` | [ ] Pending Capture |
| **(c)** | Docker Hub repository UI web page showing both `v1` and `v2` tags | `screenshots/screenshot-c.png` | [ ] Pending Capture |
| **(d)** | Web browser accessing `http://<ec2-public-ip>` showing live EC2 app | `screenshots/screenshot-d.png` | [ ] Pending Capture |

---

### 2. Homework Submission Checklist

- [x] **Part 1: Docker Compose (20 Pts)**
  - [x] Multi-container configuration in `docker-compose.yml`.
  - [x] Custom bridge network defined and linked.
  - [x] Named volume `redis_data` configured and persistence verified across `down` and `up`.
- [x] **Part 2: Docker Swarm (20 Pts)**
  - [x] Stack file `docker-stack.yml` with `deploy:` key, resource limits, and replicas.
  - [x] Deployed stack via `docker stack deploy`.
  - [x] Scaled service to 3 replicas (`docker service scale`).
  - [x] Proved self-healing by killing a container (`docker rm -f`).
- [x] **Part 3: Docker Hub (25 Pts)**
  - [x] Image `lihengkh/homework:v1` built and pushed.
  - [x] Visible update made for `v2` and pushed as `lihengkh/homework:v2`.
  - [x] Verified repository is public on Docker Hub.
  - [x] Tested clean pull without local cache (`docker rmi`).
- [x] **Part 4: Deploy to AWS EC2 (25 Pts)**
  - [x] Launch Free Tier EC2 instance.
  - [x] Configure Security Group (SSH port 22 restricted, HTTP port 80 open).
  - [x] Install & start Docker daemon (`sudo systemctl enable --now docker`).
  - [x] Run container bound to port 80.
  - [x] Verify browser access and include termination reminder.
- [x] **Part 5: Deliverables & Documentation (10 Pts)**
  - [x] Complete `README.md` with full reproduction steps.
  - [x] Clear screenshot guide and checklists.

