# ByteOn Flashcards

The home page separates **Play** (`/flashcards/play`) from **Make** (`/flashcards/make`). Play lists the signed-in user's decks separately from decks shared with everyone. New decks are personal until their owner enables sharing in the editor.

Card images are optional. The editor offers only the local illustrations in `static/stock/`; neither uploads nor pasted images are accepted. The save API validates image values against this gallery. Older unrestricted images remain in stored decks but are hidden in play, view, print and edit views until replaced with an approved illustration.

Environment variables: `MONGO_URI`, `FLASHCARD_DB`, `FLASHCARD_COLLECTION`, `AUTH_API_BASE`, `URL_PREFIX`, `PORT`, `MIN_FLASHCARDS`, and `BYTEON_SESSION_SECRET`.
