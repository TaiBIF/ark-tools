# ark-tools
A simple ark resolver for pid.biodiv.tw

## What is an ARK?
See https://arks.org/

## Development
ark-tools is developed with Flask, PostgreSQL.

### Run with docker compose
```
docker-compose up
```

## Production Deployment

```
docker-compose -f compose.yml -f compose.prod.yml up
```