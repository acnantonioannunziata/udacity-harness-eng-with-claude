---
description: Conventions for co-located test files
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
---

# Test file rules

Loads for all co-located test files.

- Every new feature requires at least one success-path test.
- Every new feature requires at least one failure-path test.
- Prefer explicit assertions over broad truthy assertions.
- Keep test setup close to the test that uses it.
- Use deterministic data builders instead of copying large JSON fixtures.
- Do not use snapshot tests for API responses.
- Do not use snapshot tests for React component rendering.
- Do not use arbitrary `setTimeout` delays in tests.
- Mock repository boundaries rather than individual database driver calls.
- Co-located files such as `Cart.test.tsx` should verify observable behavior rather than internal implementation details.
- API tests should exercise handler contracts and response shapes rather than private helper functions.