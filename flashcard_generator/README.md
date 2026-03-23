# ByteOn Flashcards (reconstructed build)

This is a rebuilt version of the flashcard generator app based on the requirements from the earlier chat.

## Included features

- J277 keyword picker grouped by topic
- Minimum 10 cards per set
- Card types:
  - Standard
  - Fill in the blanks / cloze
  - Diagram / image prompt
  - Table
  - Quiz
- Paste or upload images onto the front or back of a card
- Save sets to MongoDB
- Create share links for other ByteOn users
- View mode and play/flip mode
- Print layout with **4 cards per A4 page** and matching answer backs on reverse pages

## Environment variables

- `MONGO_URI` - MongoDB connection string. Default: `mongodb://mongo:27017/`
- `FLASHCARD_DB` - database name. Default: `auth_db`
- `FLASHCARD_COLLECTION` - collection name. Default: `flashcard_sets`
- `FLASHCARD_SECRET_KEY` - Flask secret key
- `AUTH_API_BASE` - optional auth service base URL, for example `http://auth:5002`

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then browse to:

```text
http://localhost:5010
```

## Docker example

```bash
docker build -t byteon-flashcards .
docker run -p 5010:5010   -e MONGO_URI=mongodb://host.docker.internal:27017/   -e FLASHCARD_DB=auth_db   -e AUTH_API_BASE=http://host.docker.internal:5002   byteon-flashcards
```

## Notes for ByteOn integration

This rebuild is designed to work in a few different ways:

1. **Standalone**: useful for local testing.
2. **Behind a reverse proxy**: if you inject a user header such as `X-Forwarded-User`.
3. **With your auth container**: set `AUTH_API_BASE` so the flashcard app can check `/api/session-user` using the incoming browser cookies.

## Suggested next steps

- Wire it into your docker compose stack
- Add teacher/admin moderation if you want to control which shared sets appear publicly
- Switch image storage to GridFS or object storage later if sets become very image-heavy


## Important for 502 errors

A 502 usually means your reverse proxy cannot get a healthy response from the flashcard container. Check these first:

- The container must be listening on port `5010`.
- Your proxy target must point to the flashcard container on port `5010`, not port 80.
- `MONGO_URI` must resolve from inside the container. In your existing stack that should usually be `mongodb://mongo:27017/auth_db`.
- Test health directly with `/healthz`.

Example compose service:

```yaml
  flashcards:
    build: ./flashcards
    container_name: flashcards
    restart: always
    environment:
      - MONGO_URI=mongodb://mongo:27017/auth_db
      - FLASHCARD_DB=auth_db
      - FLASHCARD_COLLECTION=flashcard_sets
      - AUTH_API_BASE=http://auth:5002
      - FLASHCARD_SECRET_KEY=replace-me
    depends_on:
      - mongo
      - auth
    expose:
      - "5010"
    networks:
      - app-network
```
