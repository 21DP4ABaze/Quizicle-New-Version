# Quizicle Production Deployment Guide

This guide explains how to deploy the Quizicle Django application using Docker for production with SQLite database.

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose v2.0 or later
- Domain name (for production with SSL)
- SSL certificates (for HTTPS)

## Quick Start

1. **Clone and prepare the environment:**
   ```bash
   git clone <your-repository>
   cd Quizicle
   cp env.example .env
   ```

2. **Configure environment variables:**
   Edit the `.env` file with your production settings:
   ```bash
   nano .env
   ```

   **Important:** Change the following values:
   - `SECRET_KEY`: Generate a new secret key
   - `ALLOWED_HOSTS`: Add your domain name
   - Email settings (if using email features)

3. **Build and start the services:**
   ```bash
   docker-compose up -d --build
   ```

4. **Run database migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create a superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access your application:**
   - HTTP: http://localhost (or your domain)
   - Admin: http://localhost/admin

## Production Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Django Configuration
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# Security Settings (uncomment for production with HTTPS)
# SECURE_SSL_REDIRECT=True
# SESSION_COOKIE_SECURE=True
# CSRF_COOKIE_SECURE=True
```

### Database Configuration

This setup uses **SQLite** for production, which is perfect for small to medium-scale applications:
- **Database file**: `db.sqlite3` is mounted as a volume for persistence
- **No external database server** required
- **Automatic backups** can be done by copying the SQLite file

### SSL/HTTPS Configuration

1. **Place SSL certificates:**
   ```bash
   mkdir ssl
   # Copy your SSL certificate files to the ssl directory
   cp cert.pem ssl/
   cp key.pem ssl/
   ```

2. **Update nginx.conf:**
   Uncomment the HTTPS server block in `nginx.conf` and update:
   - `server_name` with your domain
   - SSL certificate paths if different

3. **Update settings:**
   In your `.env` file, uncomment and set:
   ```bash
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

## Architecture Overview

The deployment consists of:
- **Web container**: Django app with Python 3.13.1 and Gunicorn
- **Nginx container**: Reverse proxy, static file serving, and SSL termination
- **SQLite database**: File-based database mounted as volume

## Service Management

### Starting Services
```bash
docker-compose up -d
```

### Stopping Services
```bash
docker-compose down
```

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f nginx
```

### Database Management

#### Backup Database
```bash
# Create backup directory
mkdir -p backups

# Copy SQLite database file
docker-compose exec web cp /app/db.sqlite3 /app/media/backup_$(date +%Y%m%d_%H%M%S).db
cp ./media/backup_*.db ./backups/
```

#### Restore Database
```bash
# Stop the web service
docker-compose stop web

# Replace the database file
cp backups/your_backup.db ./db.sqlite3

# Start the web service
docker-compose start web
```

#### Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### Application Management

#### Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

#### Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

#### Access Django Shell
```bash
docker-compose exec web python manage.py shell
```

## Monitoring

### Container Health
```bash
docker-compose ps
```

### Resource Usage
```bash
docker stats
```

### Application Logs
```bash
docker-compose logs -f web
```

## Performance Optimization

### Database Optimization
- SQLite is optimized for read-heavy workloads
- Regular VACUUM operations to optimize database file
- Consider WAL mode for better concurrency

### Static Files
- Static files are served by Nginx with proper cache headers
- Consider using a CDN for global distribution

### Application Scaling
- Adjust Gunicorn workers in Dockerfile based on your server specs
- Monitor memory usage and adjust accordingly

## Security Considerations

1. **Environment Variables:**
   - Never commit `.env` files to version control
   - Use strong, unique passwords
   - Generate new SECRET_KEY for production

2. **Database Security:**
   - SQLite file permissions are managed by Docker volumes
   - Regular backups are essential for data protection

3. **Network Security:**
   - Use HTTPS in production
   - Configure proper firewall rules
   - Nginx handles SSL termination

4. **Regular Updates:**
   - Keep Docker images updated
   - Monitor security advisories for dependencies
   - Regular security audits

## Backup Strategy

### Automated Backups
Create an automated backup script:

```bash
#!/bin/bash
# backup-script.sh
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

# Create database backup
docker-compose exec -T web cp /app/db.sqlite3 /tmp/backup_$DATE.db
docker cp $(docker-compose ps -q web):/tmp/backup_$DATE.db ./backups/

# Keep only last 7 days of backups
find backups/ -name "backup_*.db" -mtime +7 -delete

echo "Backup completed: backup_$DATE.db"
```

Add to crontab:
```bash
0 2 * * * /path/to/backup-script.sh
```

## Troubleshooting

### Common Issues

1. **Database Lock Errors:**
   - Check if multiple processes are accessing SQLite
   - Restart the web service: `docker-compose restart web`

2. **Permission Errors:**
   - Check file permissions for media directory
   - Ensure proper ownership of volumes: `sudo chown -R $USER:$USER ./media ./db.sqlite3`

3. **Static Files Not Loading:**
   - Run collectstatic: `docker-compose exec web python manage.py collectstatic`
   - Check Nginx configuration
   - Verify volume mounts

4. **Memory Issues:**
   - Monitor container resource usage: `docker stats`
   - Adjust Gunicorn worker count in Dockerfile
   - Consider adding swap space

### Getting Help

- Check container logs: `docker-compose logs [service]`
- Inspect container: `docker-compose exec [service] bash`
- Check Django logs in the application

## Scaling Considerations

For small to medium applications, this SQLite setup provides:
- **Simplicity**: No external database management
- **Performance**: SQLite is very fast for most web applications
- **Reliability**: Fewer moving parts = fewer failure points

### When to Consider Upgrading

Consider PostgreSQL if you need:
- High concurrency (1000+ simultaneous users)
- Complex queries and relationships
- Multiple application instances
- Advanced database features

## Updates and Maintenance

### Updating the Application
```bash
# Pull latest code
git pull origin main

# Backup database first
./backup-script.sh

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run migrations if needed
docker-compose exec web python manage.py migrate
```

### Regular Maintenance
- Monitor disk space (SQLite database growth)
- Clean old Docker images: `docker system prune`
- Review and rotate logs
- Update SSL certificates before expiry
- Regular database backups

## Container Specifications

- **Python Version**: 3.13.1
- **Django**: Latest supported version
- **Web Server**: Gunicorn with 3 workers
- **Reverse Proxy**: Nginx Alpine
- **Database**: SQLite (file-based)
- **Static Files**: Served by Nginx with caching

This setup is ideal for:
- Small to medium websites
- Development and staging environments
- Applications with moderate traffic
- Simple deployment requirements