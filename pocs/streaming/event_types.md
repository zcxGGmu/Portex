# Streaming Event Types (M0.2.3)

- Record Date: 2026-03-04
- Verification Command: `.venv/bin/python pocs/streaming/main.py --dry-run`
- Environment: local dry-run (no network/API key)

## Observed Event Types

- `agent_updated_stream_event`
- `response.created`
- `response.output_text.delta`
- `run_item_stream_event:message_output_created`
- `response.completed`

## Online Verification (when OPENAI_API_KEY is available)

```bash
OPENAI_API_KEY=<your-key> .venv/bin/python pocs/streaming/main.py --input "你好"
```
