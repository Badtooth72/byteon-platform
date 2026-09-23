# Byteon service boundaries

NGINX is the only public entry point. Auth owns LDAP login, Redis sessions,
student profiles and cross-activity reporting. Each activity owns its game
rules and authoritative progress writes.

## Python service structure

- Route modules translate HTTP requests and responses.
- Auth clients resolve identity through Auth's `/api/session-user` endpoint.
- Repositories contain MongoDB reads and writes.
- Services contain marking, feedback and other application rules.
- Pure validation and scoring functions are tested without databases or HTTP.

New game code should not read another service's Redis session directly, trust
identity headers from a browser, or accept a final leaderboard score from the
browser. It should ask Auth for identity and calculate authoritative results in
its own service.
