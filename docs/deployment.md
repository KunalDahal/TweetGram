# Deployment

Deployment target is Docker Compose on a VPS, with the bot and MongoDB running as containers.

1. Copy `.env.example` to `.env` and fill in values.
2. Keep `MONGODB_URI=mongodb://mongo:27017` so the bot connects to the Compose MongoDB service.
3. Build and run with Docker Compose from the repository root:

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

Do not run multiple replicas until distributed worker leases are implemented.
