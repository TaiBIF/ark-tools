# ark-tools
A simple ark resolver for pid.biodiv.tw

Inspired from [internetarchive/arklet: ARK minter, binder, resolver](https://github.com/internetarchive/arklet)

## Depends

Flask, SQLite3

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
