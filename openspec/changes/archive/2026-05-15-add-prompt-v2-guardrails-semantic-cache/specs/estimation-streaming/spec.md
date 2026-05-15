## MODIFIED Requirements

### Requirement: Server-Sent Events streaming endpoint

The system SHALL expose `POST /api/v1/estimate/stream` accepting a transcription and optional `model` and `max_tokens` overrides. The endpoint SHALL also accept an optional `prompt_version` query parameter; omitted values SHALL use the configured default prompt version, and supported values SHALL include `v1` and `v2`. Unsupported prompt versions SHALL return HTTP 422 with a clear response body naming the unsupported version and supported versions before the stream is opened. The handler SHALL return a Server-Sent Events stream where each token chunk is emitted as an event of type `token`, followed by a terminal `done` event, and SHALL emit an `error` event with a string detail if streaming fails after the stream starts.

#### Scenario: Happy-path stream completes

- **WHEN** a client consumes the SSE stream for a valid transcription and supported prompt version and the model produces text
- **THEN** the client receives one or more `token` events with incremental text, then a `done` event whose data marks completion, and the connection ends cleanly

#### Scenario: Unsupported prompt version rejected before stream

- **WHEN** the client calls `POST /api/v1/estimate/stream?prompt_version=v999`
- **THEN** the API returns HTTP 422 with a response body that clearly states `v999` is unsupported and no SSE stream is opened

#### Scenario: Mid-stream failure becomes error event

- **WHEN** chunk retrieval raises an exception after some tokens were already sent
- **THEN** the stream emits an `error` event with a descriptive message and terminates without claiming success in the `done` event
