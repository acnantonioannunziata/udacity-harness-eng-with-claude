---
description: Conventions for Node.js API handlers
paths:
  - "src/api/**/*"
---

# API handler rules

Loads when editing files under `src/api/`.

- Every API file exports exactly one handler named `handler`.
- Use the signature `export async function handler(req, res)`.
- Validate request input before calling any service layer.
- Parse and validate request bodies before reading business fields.
- Repository imports are allowed only from `src/db/`.
- Do not import database drivers directly into API handlers.
- Never execute raw SQL inside API handler files.
- Convert domain exceptions into structured HTTP responses.
- Never return stack traces or internal exception messages to clients.
- Keep orchestration in the handler and move business logic into services.
- Return consistent JSON response shapes for both success and failure cases.
