# ByteOn Computer Science Word Search

A Flask-based word search game for OCR J277 and general computer science vocabulary.

## Included features

- OCR-style computer science term bank split by topic
- Mixed-topic mode or single-topic mode
- Easy / Medium / Hard / Expert difficulties
- Word list modes: terms, clues, obscured
- Hint, give up, new game, print
- Local stats and achievement badges using browser storage
- Optional session-user badge if deployed behind your existing auth service

## Files

- `app.py` - Flask app and puzzle generation API
- `puzzle_data.py` - term bank and clues
- `templates/index.html` - main page
- `static/style.css` - styling
- `static/app.js` - gameplay logic
- `compose-snippet.yml` - Docker Compose block to merge into your stack
- `nginx-location.conf` - reverse proxy location block

## Local run

```bash
pip install -r requirements.txt
python app.py
```

Then browse to:

```text
http://localhost:5006
```

## Docker Compose

Add the contents of `compose-snippet.yml` into your main compose file.

## Nginx

Add the contents of `nginx-location.conf` into the relevant server block, then reload nginx.

Suggested URL:

```text
https://your-domain.example/cs-wordsearch/
```

## Optional dashboard link

In your auth app, add something like this to `AVAILABLE_ACTIVITIES`:

```python
"cs_wordsearch": {
    "name": "CS Word Search",
    "link": "/cs-wordsearch/"
}
```

## Notes

- The app stores stats in the browser with `localStorage`.
- It does not require MongoDB.
- It can still sit nicely inside your existing ByteOn stack and read `/api/session-user` if that endpoint exists.
