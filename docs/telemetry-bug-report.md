# Telemetry bug report and fix record

## Reported behavior

Some site visits and telemetry records had no useful client IP address, and the admin view did not show general site access. Session-end events were often lost during page unload. Question revisit telemetry could also mark the next question as revisited instead of the question actually revisited.

## Root causes

- Only authentication and session events stored an IP. Question and behavior telemetry omitted it, and page/resource requests were not recorded.
- The server always recorded the direct TCP peer address, which is the reverse proxy address when deployed behind a proxy.
- `beforeunload` used a regular asynchronous fetch, which browsers may cancel while closing or navigating away.
- Question navigation set the revisit flag on the destination when leaving a previously visited question.
- Telemetry write exceptions were swallowed by some endpoints while they returned success, so failed writes looked successful to the browser.
- The admin API accepted an email address as proof of administrator identity, and IP data was not available in the audit screen.

## Fixes

- Persist page and test data access in `site_access_events`, and include the server-derived address on login, session, question, and behavior telemetry.
- Resolve forwarded client addresses only when the direct peer matches `TRUSTED_PROXY_CIDRS`; ignore forwarded headers from untrusted peers.
- Add signed, expiring administrator API tokens and require them for protected admin data and access changes.
- Send page-exit events with `pagehide` and `sendBeacon`, with a keepalive fetch fallback and duplicate-send guard.
- Mark revisit telemetry on the question being re-entered, report failed writes to the client, and return an error when telemetry persistence fails.
- Add an admin-only site access/IP table and escape its request-derived values before rendering.
- Migrate existing question and behavior telemetry tables by adding nullable IP columns.

## Deployment notes

Set `TRUSTED_PROXY_CIDRS` to the exact proxy IP addresses or CIDR ranges used by the deployment. The default trusts only loopback. Without correct proxy configuration, the app records the immediate peer address (often the proxy) because forwarded headers cannot be trusted from arbitrary clients.

Set a long random `ADMIN_API_TOKEN_SECRET` and keep it stable across restarts and server workers so administrator sessions remain valid. Tokens expire after 12 hours. Previously cached admin sessions must sign in again to receive a token.

Site access records include visitor IP, requested page/resource, browser user-agent, and UTC timestamp in the SQLite database. Restrict database and administrator access to authorized operators.
