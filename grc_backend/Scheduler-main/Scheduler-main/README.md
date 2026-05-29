# Scheduler Microservice

Generic scheduler service in **Python** with **MySQL** and **REST API**. Others can integrate by creating schedules via API; when a schedule is due, the service POSTs to your **callback URL** with an optional payload.

## Setup

1. **Python 3.8+** and **MySQL** installed.
2. Create a `.env` from `.env.example` and set your MySQL credentials:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=scheduler_db
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the service (creates DB/tables on first run, starts API and background runner):
   ```bash
   python main.py
   ```
5. Open **http://localhost:8000** for the UI, or call the API directly.

## API (integration)

- **POST /api/schedules** – Create schedule (body: `name`, `schedule_type`, optional `scheduled_at`, `cron_expression`, `hour`, `minute`, `day_of_week`, `day_of_month`, `callback_url`, `payload`).
- **GET /api/schedules** – List all schedules.
- **GET /api/schedules/{id}** – Get one schedule.
- **PATCH /api/schedules/{id}** – Update (e.g. `is_active`, `name`, `callback_url`, `payload`).
- **DELETE /api/schedules/{id}** – Delete schedule.
- **GET /api/schedules/{id}/runs** – List run history for a schedule.

**Schedule types:** `one_minute`, `one_week`, `exact_date`, `daily`, `monthly`, `recurring` (weekly), `every_minute`, `cron` (5-field expression).

When a schedule is due, the runner **POSTs** to `callback_url` with JSON body = `payload` (or `{}`). Your app can use this webhook to run the actual job.

## Database

**MySQL** stores:

- **schedules** – name, schedule_type, cron_expression, scheduled_at, next_run_at, last_run_at, is_active, callback_url, payload (JSON).
- **schedule_runs** – schedule_id, started_at, finished_at, status, response_summary, error_message.

Tables are created automatically on first run via `database.init_db()`.
