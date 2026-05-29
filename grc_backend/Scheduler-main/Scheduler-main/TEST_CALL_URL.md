# How to test "Call a URL" (Yes and No)

## Step 1: Start the test receiver

Open a **new terminal** (keep your Scheduler running in the other one) and run:

```bash
cd c:\Users\akank\OneDrive\Documents\Scheduler
python test_receiver.py
```

You should see:
- `Test receiver running at http://localhost:5001`
- Leave this terminal open — you'll see requests here when the Scheduler runs.

---

## Step 2: Test "Send data? **No**" (GET)

1. Open **http://localhost:8000** (Scheduler UI).
2. **Add schedule:**
   - **Name:** `Test GET`
   - **When:** `One time (in 1 min)`
   - **What to do:** `Call a URL — trigger your app or any API`
   - **URL:** `http://localhost:5001/test`
   - **Send data?** `No — just trigger the URL (GET)`
3. Click **Create schedule**.
4. Wait about 1 minute.
5. In the **test_receiver** terminal you should see something like:
   - `[2026-02-11T...] GET /test received — no data sent`

---

## Step 3: Test "Send data? **Yes**" (POST + JSON)

1. In Scheduler UI, **Add schedule** again:
   - **Name:** `Test POST`
   - **When:** `One time (in 1 min)`
   - **What to do:** `Call a URL — trigger your app or any API`
   - **URL:** `http://localhost:5001/test`
   - **Send data?** `Yes — send JSON with the request (POST)`
   - **JSON to send:**  
     `{"message": "Hello from scheduler", "test": true}`
2. Click **Create schedule**.
3. Wait about 1 minute.
4. In the **test_receiver** terminal you should see something like:
   - `[2026-02-11T...] POST /test received — body: {'message': 'Hello from scheduler', 'test': True}`

---

## Summary

| What you set in Scheduler | What the test receiver gets |
|---------------------------|-----------------------------|
| Send data? **No** (GET)    | GET request, no body        |
| Send data? **Yes** (POST) | POST request + your JSON    |

You can also click **Runs** on each schedule in the Scheduler UI to see success/failure and the response.

---

## GRC policy self-healing (webhook)

1. In Django `grc_backend/.env` (prod: deployment secrets), set:
   - **`POLICY_SELF_HEAL_CRON_SECRET`** — long random string
   - **`FRONTEND_BASE_URL`** — e.g. `https://your-grc.company.com`

2. Start the Scheduler: `cd Scheduler-main/Scheduler-main` → `python main.py` (UI at http://localhost:8000).

3. In the Scheduler UI, **Add schedule**:

   | Field | Value |
   |--------|--------|
   | **Name** | `Policy self-heal` |
   | **When** | **Every minute** (or Daily for production) |
   | **What to do** | Call a URL |
   | **URL** | `http://<django-host>:8000/api/policies/self-healing/reminders/run/` |
   | **Send data?** | **Yes** (POST) |
   | **JSON** | `{"secret": "YOUR_POLICY_SELF_HEAL_CRON_SECRET"}` |

   Use the host/port Django actually listens on (`localhost` only if Scheduler runs on the same machine).

4. Check **Runs** on the schedule — status should be `success` and HTTP 200.

5. Optional JSON: `"for_date": "2026-05-15"` for backfills.

6. **Every minute** is fine for testing. Reminders are deduped **once per policy per day**; business rules still apply (frequency / last 7 days). For production, prefer **Daily** at e.g. 08:00.

7. Manual test (no Scheduler): `python manage.py run_policy_self_heal_reminders`

---

## GRC scheduled audits (webhook)

Recurring audits, due reminders, and overdue escalation to Compliance Managers.

1. In Django `grc_backend/.env`, set:
   - **`SCHEDULED_AUDITS_CRON_SECRET`** — long random string (separate from policy self-heal)

2. In the Scheduler UI, **Add schedule**:

   | Field | Value |
   |--------|--------|
   | **Name** | `Scheduled audits` |
   | **When** | **Daily** (e.g. 08:00) or Every minute for testing |
   | **What to do** | Call a URL |
   | **URL** | `http://127.0.0.1:8000/api/audits/scheduling/run/` (use your real Django host/port — **not** the literal text `<DJANGO_PORT>`) |
   | **Send data?** | **Yes** (POST) |
   | **JSON** | `{"secret": "YOUR_SCHEDULED_AUDITS_CRON_SECRET"}` |

   Optional header instead of JSON: `X-Scheduled-Audits-Secret: YOUR_SECRET`

3. Manual test (no Scheduler):

   ```bash
   cd grc_backend
   python manage.py run_scheduled_audits
   ```

4. Inline scheduler (dev): set `ENABLE_SCHEDULED_AUDITS_SCHEDULER=true` (default on when not `DJANGO_DEBUG=true`). Interval: `SCHEDULED_AUDITS_INTERVAL_SECONDS` (default 86400).

5. **Reassign UI**: Compliance Managers open **Notifications**, click an **Audit overdue** row, pick a new auditor in the modal.

