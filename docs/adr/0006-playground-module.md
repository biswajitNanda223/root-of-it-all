# ADR 0006 - Playground as an optional, isolated module
Status: accepted
**Context** We want runnable examples of every FastAPI feature without polluting the service. **Decision** Keep them in
`app/playground`, mounted by a single `register(app)`; settings forbid it in production; tests cover it. **Consequences**
Extra code to maintain, but it is dead-simple to remove or copy from.
