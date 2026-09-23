# Logic Lab

Logic Lab replaces the original five-page Logic Gate quiz at `/logic-gate-quiz/`.

## Learning path

1. Identify AND, OR and NOT gates.
2. Complete NAND and XOR truth tables.
3. Assemble multi-gate circuits from Boolean expressions.
4. Complete an eight-row GCSE-style truth table.

The interface supports pointer, touch and keyboard input. It uses responsive HTML controls rather than drag-only interactions.

## Marking and progress

The browser requests public challenge descriptions from `GET /api/logic-gates/challenges`. Correct answers and explanations remain in the Auth service.

Authenticated attempts are submitted to `POST /api/logic-gates/attempt`. The server validates the response, marks it deterministically and records both the latest result per challenge and the last 100 attempts. Existing Logic Gate progress records remain readable by the dashboard and leaderboard code.
