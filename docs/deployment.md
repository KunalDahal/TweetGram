# Deployment

Deployment target is one Docker container on a VPS using MongoDB Atlas.

1. Copy `.env.example` to `.env` and fill in values.
2. Allow the VPS IP address in MongoDB Atlas network access.
3. Build and run with Docker Compose from the repository root:

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

Do not run multiple replicas until distributed worker leases are implemented.
