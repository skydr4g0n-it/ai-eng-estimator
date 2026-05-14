## ADDED Requirements

### Requirement: Server-Sent Events streaming endpoint

The system SHALL expose `POST /api/v1/estimate/stream` accepting a transcription and optional `model` and `max_tokens` overrides. The handler SHALL return a Server-Sent Events stream where each token chunk is emitted as an event of type `token`, followed by a terminal `done` event, and SHALL emit an `error` event with a string detail if streaming fails.

#### Scenario: Happy-path stream completes

- **WHEN** a client consumes the SSE stream for a valid transcription and the model produces text
- **THEN** the client receives one or more `token` events with incremental text, then a `done` event whose data marks completion, and the connection ends cleanly

#### Scenario: Mid-stream failure becomes error event

- **WHEN** chunk retrieval raises an exception after some tokens were already sent
- **THEN** the stream emits an `error` event with a descriptive message and terminates without claiming success in the `done` event

### Requirement: Static SSE demo asset

The system SHALL serve a small static HTML demo page from the HTTP application (mounted under a `/static` URL prefix) that demonstrates consuming the streaming endpoint in a browser-compatible way, without introducing a Streamlit or chat UI dependency.

#### Scenario: Demo asset reachable

- **WHEN** a browser or HTTP client requests the documented static path for the SSE demo file
- **THEN** the server returns `200` with `text/html` content suitable for initiating an `EventSource` or `fetch`-based stream against the streaming API
