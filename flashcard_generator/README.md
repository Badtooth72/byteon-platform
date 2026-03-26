ByteOn Flashcards - complete updated package

What is included
- clear card types: Standard, Quiz, Fill in the blanks, Diagram / image prompt
- quiz answer matching with alternatives and keyword groups
- cloze checking is not case sensitive
- minimum set size reduced to 5
- one-card-at-a-time play mode
- flip animation for Standard and Diagram cards
- light / dark theme toggle persisted in localStorage
- image paste / upload zones in the editor
- auth lookup via /api/session-user on the auth container
- URL prefix support for /flashcards

Environment variables
- MONGO_URI=mongodb://mongo:27017/
- FLASHCARD_DB=auth_db
- FLASHCARD_COLLECTION=flashcard_sets
- AUTH_API_BASE=http://auth:5002
- URL_PREFIX=/flashcards
- FLASHCARD_SECRET_KEY=change-me
- PORT=5005
- MIN_FLASHCARDS=5

Expected reverse proxy behaviour
Preferred nginx block:

location = /flashcards {
    return 301 /flashcards/;
}

location /flashcards/ {
    proxy_pass http://flashcard_generator:5005/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Prefix /flashcards;
}
