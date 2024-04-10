# Use official PostgreSQL image as base image
FROM postgres:latest

# Copy the script into the container
COPY scripts.sql /docker-entrypoint-initdb.d/

# Set environment variables
ENV POSTGRES_USER=idrl_user
ENV POSTGRES_PASSWORD=idrl_2024
ENV POSTGRES_DB=idrl_db
