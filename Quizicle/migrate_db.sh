#!/bin/bash

# Migration script to copy existing database to the new volume
echo "Starting database migration..."

# Create docker volume if it doesn't exist
docker volume create quizicle_db_data 2>/dev/null || true

# Stop existing container if running
docker-compose down

# Copy existing database to the new volume location
if [ -f "./db.sqlite3" ]; then
    echo "Found existing database file, copying to volume..."

    # Create a temporary container to copy the database
    docker run --rm \
        -v "$(pwd):/source" \
        -v "quizicle_db_data:/destination" \
        alpine:latest \
        sh -c "
            mkdir -p /destination && \
            cp /source/db.sqlite3 /destination/db.sqlite3 && \
            chmod 664 /destination/db.sqlite3 && \
            chown 1000:1000 /destination/db.sqlite3
        "

    echo "Database copied successfully!"
else
    echo "No existing database found, will create new one."
fi

# Start the containers
echo "Starting containers..."
docker-compose up --build -d

echo "Migration complete!"
echo "Your database is now stored in a Docker volume with proper permissions."