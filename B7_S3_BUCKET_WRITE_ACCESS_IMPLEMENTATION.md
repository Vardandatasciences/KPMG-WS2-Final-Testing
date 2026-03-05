## B7 – S3 Bucket Write Access – Implementation Plan

This document describes **how we will change configuration and code** in `grc_backend` (and related microservices) to properly secure **S3 bucket write access**, mapping back to section 7 (“S3 Bucket Write Access”) of `SECURITY_REMEDIATION_PLAN 1.md`.

---

## 1. Goals Recap (B7)

- **Private by default**: No public write access to any bucket used by the product (including report exports, uploads, and attachments).
- **Least‑privilege IAM**: Application roles/keys have only the minimal actions on the specific buckets and prefixes they need.
- **Controlled URL exposure**: Clients receive only **read‑only, time‑limited URLs** (typically pre‑signed) and never raw credentials or write‑capable URLs.
- **Environment isolation**: Separate buckets and/or prefixes per environment (dev/stage/prod) and per major feature where necessary.
- **Full observability**: Logging, versioning, and (where appropriate) object‑lock to detect and recover from misuse or accidental overwrites.

---

## 2. Backend & Infrastructure Changes – S3 Buckets and IAM

### 2.1 Bucket layout and naming

- **Action**:
  - Define a **canonical set of buckets** in infrastructure (Terraform/CloudFormation/manual, depending on current practice):
    - `grc-<env>-uploads` – user‑initiated uploads (evidence documents, policy files, etc.).
    - `grc-<env>-exports` – generated reports/exports.
  - For each bucket:
    - Disable **public access** at the account and bucket level (`Block Public Access` = on).
    - Require **bucket‑level policies** that:
      - Deny `s3:PutObject`, `s3:DeleteObject`, and `s3:PutObjectAcl` from `Principal: *` unless coming from:
        - Specific IAM roles used by the backend/microservices.
        - Explicitly trusted internal services.

- **Why**:
  - Prevents accidental “open write” buckets, which are a common source of defacement and data tampering.

### 2.2 IAM roles and permissions for the backend

- **Action**:
  - Introduce **dedicated IAM roles** (or users with access keys, if roles are not yet used) for:
    - `GRC_APP_BACKEND_ROLE` – used by the main Django backend.
    - `GRC_S3_MICROSERVICE_ROLE` – used by `RenderS3Client` / S3 upload microservice.
  - Attach restrictive inline or managed policies, for example:
    - Backend:
      - `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` on:
        - `arn:aws:s3:::grc-<env>-uploads/*`
        - `arn:aws:s3:::grc-<env>-exports/*`
      - No `s3:DeleteObject` unless strictly required (and then only on narrow prefixes).
    - Microservice:
      - If it only writes and returns links, allow `s3:PutObject` on specific prefixes.
      - Prefer not to grant `s3:DeleteObject` or `s3:PutBucketPolicy`.
  - Remove any legacy IAM users/keys that currently have `s3:*` or broad `*` permissions on `*`.

- **Why**:
  - Enforces least privilege and ensures that even if a key leaks, damage is confined to specific buckets/prefixes.

### 2.3 Bucket policy – explicit denies for public write

- **Action**:
  - For each bucket, add a **defense‑in‑depth bucket policy**:
    - Deny any `PutObject` or `PutObjectAcl` operation if:
      - `Principal` is `*` (anonymous/public).
      - ACL being set includes a public grant (`AllUsers` or `AuthenticatedUsers`).
  - Example structure (conceptual, to be applied via IaC):
    - Effect: `Deny`
    - Principal: `*`
    - Action: `s3:PutObject`, `s3:PutObjectAcl`
    - Condition: `StringEquals` on `s3:x-amz-acl` matching public values.

- **Why**:
  - Prevents accidental introduction of public‑write ACLs from application code or the console.

---

## 3. Backend Code Changes – `boto3` Usage and URL Generation

The remediation plan currently notes `backend/settings.py` and `grc_backend/grc/routes/Global/s3_fucntions.py` / `s3_fucntions_old.py` as key touchpoints.

### 3.1 Centralized S3 client factory

- **Action**:
  - Introduce a small S3 utility module, e.g. `grc_backend/grc/utils/s3_client.py`:
    - Provides functions:
      - `get_s3_client()`: returns a `boto3.client("s3")` configured with region, credentials from environment/role, and reasonable timeouts.
      - Optionally `get_s3_resource()` for higher‑level operations, but keep most operations via the client.
  - Migrate existing S3 helpers (`s3_fucntions.py`, S3 microservice clients) to use this shared factory instead of creating clients ad‑hoc.

- **Why**:
  - Ensures consistent configuration (timeouts, retries, encryption defaults) and makes it easy to layer in future security checks.

### 3.2 Safe upload helper – no public ACLs

- **Action**:
  - In `s3_fucntions.py`, define a canonical upload function (refining the current `upload_to_s3`):
    - Accepts `file_content`, `file_name`, `content_type`, and `bucket` (or uses a default from settings).
    - Calls `s3_client.put_object` or `upload_fileobj` with:
      - `Bucket` set to `AWS_BUCKET_UPLOADS` or `AWS_BUCKET_EXPORTS` as appropriate.
      - `ServerSideEncryption` (e.g. `AES256` or `aws:kms`) enabled by default.
      - **No explicit ACL** unless strictly needed; rely on bucket policy and IAM.
    - Does **not** generate or expose write‑capable URLs.
  - Remove any instances where:
    - `ACL="public-read"` or similar is set for uploads, unless there is a deliberate and documented need.
    - Objects are uploaded to a **publicly writable** bucket.

- **Why**:
  - Keeps write operations strictly within the backend trust boundary and avoids accidental public object exposure.

### 3.3 Read‑only pre‑signed URLs for clients

- **Action**:
  - For user downloads (evidence files, reports, etc.), switch to **pre‑signed `GET` URLs**:
    - Create a helper, e.g. `generate_presigned_get_url(key: str, expires_in: int = 900) -> str`.
    - Use it in relevant views (`export_*`, document download endpoints) instead of returning raw S3 paths.
  - Ensure:
    - The pre‑signed URLs are **GET‑only**, no upload permission.
    - Expiration is short (e.g. 5–15 minutes).
    - Keys are constructed from server‑side identifiers (not user‑supplied paths).

- **Why**:
  - Client never receives credentials or a URL that permits writes. Even compromised links are bounded in time and scope.

### 3.4 Deprecation of direct public URLs

- **Action**:
  - Where code currently returns `https://{bucket}.s3.{region}.amazonaws.com/{file}`:
    - Replace with pre‑signed `GET` URLs.
    - Audit any consumers (frontend, external integrations) and adjust them to handle expiring URLs.

- **Why**:
  - Eliminates reliance on public buckets and discourages long‑lived unauthenticated access paths.

---

## 4. S3 Microservice (`RenderS3Client`) Hardening

### 4.1 Authentication and authorization

- **Action**:
  - Ensure the S3 microservice:
    - Authenticates requests from the backend (e.g. via an internal token, mTLS, or restricted network + shared secret).
    - Authorizes **which tenant/user** is allowed to write to which prefix (e.g. per‑tenant folders).
  - Avoid exposing any endpoint that:
    - Accepts arbitrary bucket names or keys from untrusted clients.
    - Returns pre‑signed **PUT** URLs to the browser unless:
      - The prefix is fully controlled.
      - The URL has tight size/content restrictions (and even then, prefer backend‑mediated uploads).

- **Why**:
  - Prevents the microservice from becoming a generic “open S3 proxy” that attackers can abuse to write arbitrary data.

### 4.2 Prefix and path constraints

- **Action**:
  - Standardize on per‑tenant and per‑feature prefixes, e.g.:
    - `tenant-{tenant_id}/evidence/…`
    - `tenant-{tenant_id}/exports/…`
  - Server‑side code:
    - Computes prefixes from authenticated context (tenant ID, user ID, feature).
    - Does **not** allow client‑controlled path traversal (`../`) or raw keys.

- **Why**:
  - Limits blast radius per tenant and prevents overwriting unrelated data.

---

## 5. Frontend Changes – Consumption Only

Even though S3 write access is a backend concern, frontend patterns can increase or decrease risk.

### 5.1 No direct S3 writes from the browser (by default)

- **Action**:
  - Review any Vue components or utilities that:
    - Directly post to S3 endpoints.
    - Use pre‑signed **PUT** URLs for uploads.
  - Unless there is a strong, documented requirement:
    - Prefer routing all uploads through backend endpoints which then write to S3.
  - If browser‑direct uploads are required for performance:
    - Ensure pre‑signed `PUT` URLs are generated **only** by authenticated backend endpoints.
    - Limit accepted content types, max size, and prefix via backend validation.

- **Why**:
  - Keeps trust decisions and access control in the backend, not in JavaScript running in the user’s browser.

### 5.2 Handling expiring download links

- **Action**:
  - Update frontend download flows to:
    - Call backend APIs to obtain pre‑signed `GET` URLs.
    - gracefully handle expiration errors by:
      - Re‑requesting a new URL from the backend.
      - Showing a clear message if the file has been removed.

- **Why**:
  - Aligns UX with secure backend behavior (short‑lived URLs) without encouraging insecure workarounds.

---

## 6. Monitoring, Logging, and Recovery

### 6.1 S3 access logging and CloudTrail

- **Action**:
  - Enable S3 **server access logging** or CloudTrail data events for:
    - All buckets used by the application.
  - Forward logs to:
    - A dedicated logging bucket (separate from application data).
    - Central SIEM or log analytics if available.

- **Why**:
  - Provides an auditable trail of who wrote which objects and when, crucial for incident response.

### 6.2 Versioning and object lock (where appropriate)

- **Action**:
  - Enable **versioning** on `grc-<env>-uploads` and `grc-<env>-exports`.
  - For particularly sensitive data (e.g. long‑term evidence archives), consider:
    - S3 Object Lock in **compliance mode** with a defined retention period.

- **Why**:
  - Allows recovery from accidental overwrites/deletions and strengthens resilience against ransomware‑style attacks.

---

## 7. Testing Strategy

### 7.1 Infrastructure and IAM tests

- **Action**:
  - Validate via AWS CLI or IaC testing tools that:
    - Public access is blocked for all buckets.
    - Anonymous `PutObject` is denied.
    - Application roles cannot write outside their allowed prefixes.
  - Attempt controlled negative tests:
    - Anonymous write to each bucket → must fail.
    - Role write to an out‑of‑scope bucket/prefix → must fail.

### 7.2 Backend integration tests

- **Action**:
  - Add integration tests (or manual runbooks, if automated tests are not yet in place) for:
    - Upload endpoints:
      - Successful upload with valid auth and content.
      - Rejection of file types/size exceeding limits (if enforced in code).
    - Download endpoints:
      - Pre‑signed URL is returned and usable.
      - URL expires as expected.

### 7.3 Security review

- **Action**:
  - After implementation:
    - Run a focused security review to:
      - Confirm no buckets are left publicly writable.
      - Confirm no code path returns write‑capable URLs or raw S3 credentials to the browser.
      - Review logs for any anomalous write patterns.

---

## 8. Theoretical Summary – What We Gain

1. **Strong containment of write capabilities**  
   - Only authenticated backend and microservice roles can write, and only to narrowly defined prefixes.
2. **Elimination of public write vectors**  
   - Bucket policies and blocked public access prevent anonymous or overly broad writes, even if someone misconfigures ACLs.
3. **Safer client interaction with S3**  
   - Browsers and external clients see only short‑lived, read‑only URLs, so they cannot arbitrarily modify bucket contents.
4. **Improved resilience and auditability**  
   - Logging, versioning, and (where used) object lock make unauthorized or accidental writes detectable and recoverable.

