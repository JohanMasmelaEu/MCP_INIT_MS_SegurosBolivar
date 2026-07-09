# Architecture Rules — Seguros Bolivar

## Consistency
- Replicate existing standard patterns before modifying code
- Never invent new patterns

## Layer Separation
- Presentation (Frontend): UI only, NEVER business logic
- Logic (Backend/API): Domain rules, calculations, validations
- Persistence (Data): Connection always via API, never direct from frontend

## Resilience
- Circuit breakers on all external calls
- Long-running tasks in background
- Rate limiting to protect core components

## Performance
- Frontend < 3s, internal APIs < 15s (reference targets)
- Connection pooling for DB and external services
- Cache frequently accessed configuration

## Observability
- Correlation-ID in every inter-service request
- Structured logs to centralized services

## API Contracts (API First)
- Version routes with prefix (/api/v1/...)
- OpenAPI spec as source of truth
- Backward compatibility during deprecation

## IT Governance
- Libraries from JFrog only
- Environments physically separated (Dev, Stage, Prod)
- Graceful shutdown implemented
- Only approved technology stack
