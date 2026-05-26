# API Security Controls Resolution Plan

## Overview
This document outlines the resolution steps for the API security observations raised by the KPMG test team.

---

## 1. Strengthen OAuth Redirect Validation

### Observation
OAuth redirect and callback endpoints have whitelist validation, but the validation logic can be strengthened to prevent open redirect vulnerabilities.

### Resolution Steps
1. **Strict URL parsing**: Parse the redirect URI and enforce exact-match host validation against an allowed list.
2. **Deny wildcards and partial matches**: Do not allow sub-domain wildcards or prefix-only matches.
3. **Reject non-HTTPS schemes**: Permit only `https://` for production redirects.
4. **Path verification**: Ensure the path and query of the redirect URI exactly match pre-registered values.
5. **Use framework helpers**: Prefer language/framework-level URL validation over custom regex when available.

### Validation
- Attempt redirection to an unregistered domain and confirm rejection.
- Attempt path/query manipulation and confirm rejection.

---

## 2. Implement REST API URL Versioning

### Observation
API versioning exists in product and contract models, but REST API URL versioning (e.g., `/api/v1/`, `/api/v2/`) is not implemented.

### Resolution Steps
1. **Define version prefix pattern**: Adopt `/api/v{number}/` as the standard URL prefix.
2. **Route registration**: Register all existing endpoints under a versioned path (e.g., `/api/v1/`).
3. **Backward compatibility**: Keep the current unversioned routes functional (or redirect to the latest version) for a deprecation period.
4. **Document versions**: Update API documentation and client SDKs to reference versioned URLs.

### Validation
- Verify that all endpoints are accessible under the versioned path.
- Confirm that version negotiation (URL path) is reflected in the response headers.

---

## 3. Implement Consistent Replay Attack Protection

### Observation
JWT expiration, refresh token rotation, and timestamp validation are in place, but explicit nonce-based replay protection and request signature verification are not consistently applied.

### Resolution Steps
1. **Nonce generation and storage**:
   - Clients include a unique `X-Request-Nonce` header per request.
   - Server maintains a short-lived nonce store (cache/tempoary table) to reject duplicates within a defined window.
2. **Request signature verification**:
   - Clients generate an HMAC-SHA256 signature over the request method, path, timestamp, nonce, and payload.
   - Server validates the signature using a shared secret or key derived per client.
3. **Enforcement scope**:
   - Apply nonce and signature checks to all state-changing endpoints (POST, PUT, PATCH, DELETE).
   - Apply to sensitive read endpoints where applicable.

### Validation
- Replay an identical request with the same nonce and confirm rejection.
- Tamper with a signed request payload and confirm signature validation failure.

---

## 4. Implement Automated Anomaly Detection and Alerting

### Observation
APIs are monitored and logged via middleware and audit logging, but automated anomaly detection and real-time alerting for abuse patterns are not implemented.

### Resolution Steps
1. **Define abuse patterns**:
   - High frequency of 401/403 responses from a single source.
   - Unusual request rate or volume spikes.
   - Repeated malformed payloads or non-standard HTTP methods.
2. **Integrate anomaly detection**:
   - Use a log aggregation or SIEM tool to apply threshold or ML-based anomaly rules on API logs.
   - Alternatively, implement a lightweight rate-limit anomaly module that flags deviations from baseline traffic.
3. **Real-time alerting**:
   - Configure alerts (email, webhook, or Slack/Teams) triggered by anomaly rule matches.
   - Set severity levels and escalation paths.
4. **Response automation**:
   - Optionally auto-block or throttle flagged IP ranges/clients pending review.

### Validation
- Simulate an abuse pattern and verify the alert is triggered within the target SLA.
- Verify that the anomaly event is recorded in the audit log with sufficient context.

---

## General Recommendations

- **Documentation**: Update the API security runbook to reflect each control.
- **Testing**: Add regression tests for redirect validation, versioning, replay protection, and alert triggers before deployment.
- **Review cadence**: Re-assess these controls quarterly or after major API releases.
