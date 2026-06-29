# API Design

PersonaAI uses explicit API versioning from the first backend phase.

## Versioning

- Root health endpoint: `GET /health`
- Versioned v1 health endpoint: `GET /api/v1/health`
- Reserved v2 namespace: `/api/v2`

New public endpoints should be added under `backend/app/api/v1/routes/` and registered in `backend/app/api/v1/router.py`. Future breaking API changes should go into `v2` instead of changing existing v1 contracts.

## Response Envelope

Successful endpoints return the shared `ApiResponse` schema:

```json
{
  "success": true,
  "message": "Health check successful",
  "data": {}
}
```

Errors return the shared `ErrorResponse` schema with a stable `error` code, optional details, and `request_id` for tracing.

## Request IDs

Every request receives:

- `X-Request-ID`
- `X-Correlation-ID`
- `X-Process-Time`

Clients may provide `X-Request-ID` and `X-Correlation-ID`; otherwise the API generates them.
