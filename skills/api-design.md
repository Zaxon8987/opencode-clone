name: api-design
description: REST/GraphQL API design, OpenAPI specs, versioning, error handling
instructions: |
  API design guidelines:
  1. Use consistent naming (plural nouns, kebab-case URLs)
  2. Version via URL prefix (/v1/, /v2/)
  3. Return standard HTTP status codes
  4. Consistent error format: {error: {code, message, details}}
  5. Paginate list endpoints (cursor or offset-based)
  6. Document with OpenAPI/Swagger
  7. Rate limit by API key/IP
  8. Validate all input at the boundary
