# SSE Streaming Debug Guide

This guide documents a recurrent streaming failure observed after merging the
workflow timeline updates. The issue manifested as the frontend's EventSource
repeatedly reporting `SSE connection error: MessageEvent`, while the backend
kept emitting heartbeat events indefinitely. Understanding the root cause and
resolution here should help future debugging efforts.

## Symptoms

- Browser consoles flooded with `SSE connection error: MessageEvent`.
- Workflow visualisation stayed stuck on "Connecting to workflow stream…" and
  never rendered node progress.
- Backend logs (`backend.log`) showed continuous `SSE yielding event #n:
  StreamEventType.HEARTBEAT` lines without corresponding node events.
- API health checks (`/api/chat/async`) succeeded, but `/api/streams/{id}`
  returned a 404 when invoked immediately after the async enqueue.

## Root Cause

The SSE endpoint (`stream_workflow_progress`) queried the database for the
requested decision set exactly once before establishing the EventSource
connection. Under load (or with the streaming test graph), the worker would
enqueue a job and briefly delay persistence of the `decision_sets` row. The
SSE handler executed first, failed to find the decision set, and returned a
404. On the frontend, each 404 triggered a reconnection attempt, but by then
the server had no active clients, so only heartbeats were emitted.

## Resolution

The initial fix introduced a fixed retry loop; however, it was still possible
to hit the failure path on slower runs. The final solution is time-based and
more resilient:

1. `stream_workflow_progress` now records the current loop via
   `asyncio.get_running_loop()` (avoids deprecated `get_event_loop()` usage) and
   keeps polling for the decision set until either it appears or a configurable
   timeout elapses.
2. The loop checks every `STREAM_DECISION_SET_RETRY_DELAY` seconds (default
   0.2s) and stops after `STREAM_DECISION_SET_MAX_WAIT` seconds (default 6s).
3. When a retry succeeds, we log diagnostic metadata (attempt count and wait
   duration) so we can monitor for slow persistence trends.
4. If the timeout is exceeded, we still return a 404, but the warning message
   now includes timing details, making the failure mode obvious in logs.

With the time-based loop in place, the frontend’s EventSource no longer sees
early 404s, and streaming resumes immediately once the worker emits events.

### Relevant Code Changes

- `api/main.py` — `get_workflow_plan` and `stream_workflow_progress` now share
  the execution plan helper. The SSE endpoint loops while awaiting the
  decision set, logging a warning only if the retries are exhausted.
- `libs/graph.py` — Added `get_execution_plan()` metadata so the frontend can
  render the timeline.

### Configuration

Two environment variables govern the retry window (defaults shown):

```
STREAM_DECISION_SET_RETRY_DELAY=0.2   # seconds between checks
STREAM_DECISION_SET_MAX_WAIT=6.0      # total seconds to wait before failing
```

Increase `STREAM_DECISION_SET_MAX_WAIT` if you observe longer persistence
delays, or lower `STREAM_DECISION_SET_RETRY_DELAY` for more aggressive polling


## Verification Steps

1. Trigger an async chat: `curl -X POST http://localhost:8000/api/chat/async …`
2. Immediately curl the stream endpoint: `curl -N` on
   `/api/streams/{decision_set_id}`. You should now see `node-start` and other
   events instead of a 404.
3. Refresh the frontend and confirm the workflow timeline transitions from
   "Connecting" to live statuses without console errors.

## Future Considerations

- If the retry window is not sufficient, consider moving the SSE subscription
  setup to JobService so the decision set always exists before the HTTP
  handler runs.
- Monitor heartbeats: a healthy connection should deliver node events between
  heartbeats. Continuous heartbeats with no other activity is a signal to
  revisit this guide.
