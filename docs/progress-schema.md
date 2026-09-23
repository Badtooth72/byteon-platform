# Byteon progress schema

Progress remains embedded under each user document in `auth_db.users`.
New records carry `schema_version: 1`; readers continue to accept older records.

Each activity owns its authoritative write path:

| Activity | Writer | Marking |
|---|---|---|
| Coding Challenges | Coding service | AI verdict and server score policy |
| Conversion Game | Conversion service | Server-held questions and answers |
| Logic Gate Quiz | Auth compatibility API | Browser score pending replacement game |
| Wordsearch | Auth compatibility API | Browser progress pending integration |
| Flashcards | Flashcard service | Set ownership and activity data |

Common fields are `schema_version`, `score`, `date`, and optional `level` and
`submission`. Services may add activity-specific fields. Scores used for a
leaderboard must be written by the activity's authoritative service.
