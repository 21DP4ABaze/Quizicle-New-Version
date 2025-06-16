# Fabric Deployment Script for Quizicle

This Fabric script automates the deployment of your Quizicle Django application from your local machine to a production server.

## Features

- 📦 **Archives your repository** using `git archive` (only committed files)
- 📤 **Uploads to production server** via SSH
- 🐳 **Builds and runs Docker containers** automatically
- 💾 **Optional database backups** (disabled by default)
- ✅ **Verifies deployment** success
- 🔧 **Manages server environment** (assumes Docker is pre-installed)

## Prerequisites

### Local Machine
- Git repository with committed changes
- Python with Fabric installed
- SSH access to production server

### Production Server
- Ubuntu/Debian Linux
- SSH access
- Sudo privileges for the deployment user
- **Docker and Docker Compose pre-installed**
- User added to docker group

## Setup

### 1. Install Fabric Dependencies

```bash
pip install -r deploy-requirements.txt
```

### 2. Server Prerequisites

Ensure your production server has:
- Docker and Docker Compose installed
- User added to docker group: `sudo usermod -aG docker $USER`

## Usage

### Initial Deployment

```bash
fab deploy --host=YOUR_SERVER_IP --user=YOUR_USERNAME
```

Example:
```bash
fab deploy --host=doha.trialine.lv --user=ubuntu
```

### Environment File

Before first deployment, create your production `.env` file:

```bash
# Copy the example
cp env.example .env.production

# Edit with your production settings
nano .env.production

# Upload to server
fab update-env --env-file=.env.production --host=doha.trialine.lv --user=ubuntu
```

## Available Commands

### 🚀 Deployment Commands

| Command | Description | Example |
|---------|-------------|---------|
| `deploy` | Full deployment (no backup) | `fab deploy --host=SERVER --user=USER` |
| `deploy-with-backup` | Full deployment with backup | `fab deploy-with-backup --host=SERVER --user=USER` |
| `quick-deploy` | Fast deployment (no rebuild) | `fab quick-deploy --host=SERVER --user=USER` |
| `update-env` | Upload environment file | `fab update-env --env-file=.env.prod --host=SERVER --user=USER` |

### 💾 Management Commands

| Command | Description | Example |
|---------|-------------|---------|
| `backup` | Create database backup | `fab backup --host=SERVER --user=USER` |
| `status` | Check application status | `fab status --host=SERVER --user=USER` |
| `logs` | View application logs | `fab logs --host=SERVER --user=USER` |
| `restart` | Restart services | `fab restart --host=SERVER --user=USER` |
| `shell` | Open Django shell | `fab shell --host=SERVER --user=USER` |

### 🧪 Development Commands

| Command | Description | Example |
|---------|-------------|---------|
| `local-test` | Test deployment locally | `fab local-test` |

## Important Notes

### Git Archive Usage
- The script uses `git archive` to create deployment packages
- **Only committed files** are included in the deployment
- Make sure to commit your changes before deploying
- Uncommitted files will NOT be deployed

### Database Backup
- Database backup is **disabled by default** for faster deployments
- Use `fab deploy-with-backup` for safer deployments
- Manual backup: `fab backup --host=SERVER --user=USER`

### Docker Requirements
- Docker and Docker Compose must be pre-installed on the server
- User must be in the docker group
- Script will verify Docker availability but won't install it

## Deployment Process

When you run `fab deploy`, the script performs these steps:

1. **📦 Git Archive Creation**
   - Creates archive using `git archive HEAD`
   - Only includes committed files from your repository
   - Automatically excludes .git directory and uncommitted changes

2. **🔧 Server Setup**
   - Creates project directories (`/opt/quizicle/`)
   - Verifies Docker is available
   - Sets proper permissions

3. **💾 Backup (Optional)**
   - Creates timestamped backup of existing database
   - Keeps last 10 backups automatically
   - Only runs if `--backup=True` or using `deploy-with-backup`

4. **📤 Upload & Extract**
   - Uploads archive to server
   - Extracts to project directory
   - Cleans up temporary files

5. **🐳 Docker Deployment**
   - Stops existing containers
   - Builds new Docker images
   - Starts containers
   - Runs database migrations
   - Collects static files

6. **✅ Verification**
   - Checks container status
   - Tests HTTP response
   - Reports deployment result

## Command Options

### Deploy Command Options

```bash
# Standard deployment (no backup, default)
fab deploy --host=SERVER --user=USER

# Deploy with database backup
fab deploy --backup=True --host=SERVER --user=USER
# OR
fab deploy-with-backup --host=SERVER --user=USER

# Quick deploy (no image rebuild)
fab deploy --quick=True --host=SERVER --user=USER
# OR
fab quick-deploy --host=SERVER --user=USER
```

### Logs Command Options

```bash
# View last 100 lines (default)
fab logs --host=SERVER --user=USER

# View last 500 lines
fab logs --lines=500 --host=SERVER --user=USER

# View nginx logs
fab logs --service=nginx --host=SERVER --user=USER
```

### Restart Command Options

```bash
# Restart all services
fab restart --host=SERVER --user=USER

# Restart specific service
fab restart --service=web --host=SERVER --user=USER
```

## File Structure on Server

```
/opt/quizicle/
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── .env
├── db.sqlite3
├── media/
├── staticfiles/
├── ssl/
└── backups/
    ├── db_backup_20241201_120000.sqlite3
    └── db_backup_20241201_180000.sqlite3
```

## SSH Configuration

For easier deployment, configure SSH in `~/.ssh/config`:

```
Host quizicle-prod
    HostName doha.trialine.lv
    User ubuntu
    IdentityFile ~/.ssh/quizicle_deploy_key
```

Then deploy with:
```bash
fab deploy --host=quizicle-prod
```

## Environment Variables

The script looks for these environment variables on the server:

```bash
# Django Configuration
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Troubleshooting

### Git Archive Issues

```bash
# Make sure you're in a git repository
git status

# Commit your changes before deploying
git add .
git commit -m "Ready for deployment"

# Then deploy
fab deploy --host=SERVER --user=USER
```

### Docker Permission Issues

```bash
# Add user to docker group on server
sudo usermod -aG docker $USER
# Then log out and back in

# Verify docker access
docker ps
```

### Connection Issues

```bash
# Test SSH connection first
ssh user@server

# Check if server is accessible
ping server-ip
```

### Docker Issues

```bash
# Check Docker status on server
fab status --host=SERVER --user=USER

# View container logs
fab logs --host=SERVER --user=USER

# Restart containers
fab restart --host=SERVER --user=USER
```

### Database Issues

```bash
# Create manual backup
fab backup --host=SERVER --user=USER

# Access Django shell
fab shell --host=SERVER --user=USER
```

## Security Best Practices

1. **Use SSH Keys**: Set up SSH key authentication instead of passwords
2. **Firewall**: Configure firewall to only allow necessary ports (22, 80, 443)
3. **Updates**: Keep server OS and Docker updated
4. **Backups**: Create manual backups for important deployments
5. **Environment**: Never commit `.env` files to version control
6. **Git**: Only committed code is deployed - review commits before deployment

## Automation

### Cron Job for Backups

Add to server crontab:
```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/quizicle && /usr/local/bin/docker-compose exec -T web cp /app/db.sqlite3 /app/backups/daily_$(date +\%Y\%m\%d).sqlite3
```

### Git Hook Deployment

Create a post-receive hook for automatic deployment:
```bash
#!/bin/bash
cd /path/to/local/repo
fab deploy --host=production-server --user=deploy-user
```

## Examples

### First-time Deployment

```bash
# 1. Ensure changes are committed
git add .
git commit -m "Initial production deployment"

# 2. Setup environment file
cp env.example .env.production
nano .env.production

# 3. Deploy application (with backup for safety)
fab deploy-with-backup --host=doha.trialine.lv --user=ubuntu

# 4. Upload environment
fab update-env --env-file=.env.production --host=doha.trialine.lv --user=ubuntu

# 5. Verify deployment
fab status --host=doha.trialine.lv --user=ubuntu
```

### Regular Updates

```bash
# 1. Commit your changes
git add .
git commit -m "Feature update"

# 2. Quick deployment for code changes
fab quick-deploy --host=production-server --user=deploy

# 3. Full deployment with new dependencies
fab deploy --host=production-server --user=deploy
```

### Safe Deployment

```bash
# For important updates, use backup
fab deploy-with-backup --host=production-server --user=deploy
```

### Monitoring

```bash
# Check application status
fab status --host=production-server --user=deploy

# View recent logs
fab logs --lines=200 --host=production-server --user=deploy

# Create manual backup before major changes
fab backup --host=production-server --user=deploy
```

## Workflow Recommendations

### Development Workflow
1. Develop and test locally
2. Commit changes to git
3. Deploy using `fab deploy` or `fab quick-deploy`

### Production Workflow
1. Test in staging environment first
2. Create backup: `fab backup`
3. Deploy: `fab deploy-with-backup`
4. Verify: `fab status`
5. Monitor: `fab logs`