"""
Fabric deployment script for Quizicle Django application.
Automates deployment from local repository to production server.

Usage:
    fab deploy --host=your-server-ip --user=your-username
"""

import os
import tempfile
import subprocess
from datetime import datetime

from fabric import Connection, task


# Configuration
PROJECT_NAME = "quizicle"
REMOTE_PROJECT_DIR = f"/var/www/{PROJECT_NAME}"
BACKUP_DIR = f"/var/www/{PROJECT_NAME}/backups"
ARCHIVE_NAME = f"{PROJECT_NAME}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"


def create_archive():
    """Create a tar.gz archive of the project using git archive."""
    print("📦 Creating project archive using git...")

    temp_dir = tempfile.mkdtemp()
    archive_path = os.path.join(temp_dir, ARCHIVE_NAME)

    try:
        # Use git archive to create the archive
        subprocess.run([
            'git', 'archive',
            '--format=tar.gz',
            f'--output={archive_path}',
            'HEAD'
        ], capture_output=True, text=True, check=True)

        print(f"✅ Archive created using git: {archive_path}")
        return archive_path

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create git archive: {e.stderr}")
        print("💡 Make sure you're in a git repository and have committed your changes")
        raise
    except FileNotFoundError:
        print("❌ Git not found. Please install git or ensure it's in your PATH")
        raise


@task
def deploy(ctx, backup=False, quick=False):
    """
    Deploy application to production server.

    Args:
        backup: Create database backup before deployment (default: False)
        quick: Skip building images, only restart containers (default: False)
    """
    # host = ctx.host
    # user = ctx.user or 'root'

    host = 'doha.trialine.lv'
    user = 'ubuntu'

    print(f"🚀 Starting deployment to {user}@{host}")

    # Create connection to remote server
    conn = Connection(host, user=user)

    try:
        # Step 1: Create project archive
        if not quick:
            archive_path = create_archive()

        # Step 2: Prepare remote server
        setup_remote_environment(conn)

        # Step 3: Backup existing data (only if requested)
        if backup:
            backup_database(conn)

        # Step 4: Upload and extract new code
        if not quick:
            upload_and_extract(conn, archive_path)

        # Step 5: Deploy application
        deploy_application(conn, quick=quick)

        # Step 6: Verify deployment
        verify_deployment(conn)

        # Cleanup local archive
        if not quick and os.path.exists(archive_path):
            os.remove(archive_path)
            print("🧹 Cleaned up local archive")

        print("🎉 Deployment completed successfully!")

    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        raise


def setup_remote_environment(conn):
    """Setup necessary directories and permissions on remote server."""
    print("🔧 Setting up remote environment...")

    # Create project directories
    conn.sudo(f'mkdir -p {REMOTE_PROJECT_DIR}')
    conn.sudo(f'mkdir -p {BACKUP_DIR}')
    conn.sudo(f'mkdir -p {REMOTE_PROJECT_DIR}/ssl')

    # Set ownership to current user
    conn.sudo(f'chown -R {conn.user}:{conn.user} {REMOTE_PROJECT_DIR}')

    # Check if Docker is available (don't install, just verify)
    result = conn.run('which docker', warn=True)
    if result.failed:
        print("⚠️  Docker not found on server. Please ensure Docker is installed and accessible.")
        raise Exception("Docker not available on server")

    # Check if user is in docker group
    result = conn.run('groups | grep docker', warn=True)
    if result.failed:
        print("⚠️  User is not in docker group. You may need to run: sudo usermod -aG docker $USER")

    print("✅ Remote environment ready")


def backup_database(conn):
    """Create backup of existing database."""
    print("💾 Creating database backup...")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"db_backup_{timestamp}.sqlite3"

    # Check if database exists
    result = conn.run(f'test -f {REMOTE_PROJECT_DIR}/db.sqlite3', warn=True)
    if result.ok:
        conn.run(f'cp {REMOTE_PROJECT_DIR}/db.sqlite3 {BACKUP_DIR}/{backup_name}')
        print(f"✅ Database backed up as: {backup_name}")

        # Keep only last 10 backups
        conn.run(f'cd {BACKUP_DIR} && ls -t db_backup_*.sqlite3 | tail -n +11 | xargs -r rm')
    else:
        print("ℹ️  No existing database found, skipping backup")


def upload_and_extract(conn, archive_path):
    """Upload archive to server and extract it."""
    print("📤 Uploading archive to server...")

    remote_archive_path = f"/tmp/{ARCHIVE_NAME}"

    # Upload archive
    conn.put(archive_path, remote_archive_path)
    print("✅ Archive uploaded")

    # Extract archive
    print("📂 Extracting archive...")
    conn.run(f'cd {REMOTE_PROJECT_DIR} && tar -xzf {remote_archive_path}')

    # Cleanup remote archive
    conn.run(f'rm {remote_archive_path}')
    print("✅ Archive extracted and cleaned up")


def deploy_application(conn, quick=False):
    """Build and run Docker containers."""
    print("🐳 Deploying Docker application...")

    with conn.cd(REMOTE_PROJECT_DIR):
        # Stop existing containers
        print("🛑 Stopping existing containers...")
        conn.run('docker compose down', warn=True)

        if not quick:
            # Build new images
            print("🔨 Building Docker images...")
            conn.run('docker compose build --no-cache')

        # Start containers
        print("▶️  Starting containers...")
        conn.run('docker compose up -d')

        # Run migrations
        print("🗃️  Running database migrations...")
        conn.run('docker compose exec -T quizicle_web python manage.py migrate')

        # Collect static files
        print("📁 Collecting static files...")
        conn.run('docker compose exec -T quizicle_web python manage.py collectstatic --noinput')

    print("✅ Application deployed")


def verify_deployment(conn):
    """Verify that the deployment was successful."""
    print("🔍 Verifying deployment...")

    with conn.cd(REMOTE_PROJECT_DIR):
        # Check container status
        result = conn.run('docker compose ps')
        print("Container status:")
        print(result.stdout)

        # Test application response
        print("🌐 Testing application response...")
        result = conn.run('curl -s -o /dev/null -w "%{http_code}" http://localhost', warn=True)

        if result.stdout.strip() == '200':
            print("✅ Application is responding correctly")
        else:
            print(f"⚠️  Application returned status code: {result.stdout.strip()}")


@task
def backup(ctx):
    """Create a backup of the production database."""
    conn = Connection(ctx.host, user=ctx.user or 'root')
    backup_database(conn)


@task
def logs(ctx, service='web', lines=100):
    """View application logs."""
    conn = Connection(ctx.host, user=ctx.user or 'root')

    with conn.cd(REMOTE_PROJECT_DIR):
        conn.run(f'docker compose logs --tail={lines} -f {service}')


@task
def status(ctx):
    """Check application status."""
    conn = Connection(ctx.host, user=ctx.user or 'root')

    with conn.cd(REMOTE_PROJECT_DIR):
        print("📊 Container Status:")
        conn.run('docker compose ps')

        print("\n💾 Disk Usage:")
        conn.run('df -h /')

        print("\n🗃️  Database Size:")
        conn.run(f'ls -lh {REMOTE_PROJECT_DIR}/db.sqlite3', warn=True)


@task
def restart(ctx, service=None):
    """Restart application services."""
    conn = Connection(ctx.host, user=ctx.user or 'root')

    with conn.cd(REMOTE_PROJECT_DIR):
        if service:
            print(f"🔄 Restarting {service} service...")
            conn.run(f'docker compose restart {service}')
        else:
            print("🔄 Restarting all services...")
            conn.run('docker compose restart')


@task
def shell(ctx):
    """Open Django shell on remote server."""
    conn = Connection(ctx.host, user=ctx.user or 'root')

    with conn.cd(REMOTE_PROJECT_DIR):
        conn.run('docker compose exec web python manage.py shell')


@task
def update_env(ctx, env_file='.env'):
    """Upload environment file to server."""
    conn = Connection(ctx.host, user=ctx.user or 'root')

    if not os.path.exists(env_file):
        print(f"❌ Environment file {env_file} not found")
        return

    print(f"📤 Uploading {env_file} to server...")
    conn.put(env_file, f'{REMOTE_PROJECT_DIR}/.env')
    print("✅ Environment file updated")


@task
def quick_deploy(ctx):
    """Quick deployment - only restart containers without rebuilding."""
    deploy(ctx, backup=False, quick=True)


@task
def deploy_with_backup(ctx):
    """Deploy with database backup (for safer deployments)."""
    deploy(ctx, backup=True, quick=False)


# Helper function for local development
@task
def local_test(ctx):
    """Test the deployment locally."""
    print("🧪 Testing deployment locally...")

    ctx.run('docker compose down', warn=True)
    ctx.run('docker compose build')
    ctx.run('docker compose up -d')

    print("✅ Local test deployment complete")
    print("🌐 Access your app at: http://localhost")