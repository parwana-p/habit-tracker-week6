# Tasks

Complete **two** of these, each on its own branch + PR.

1. **Streak** — `GET /habits/{id}/streak` returns the current run of consecutive days
   (up to and including today) that have a check-in.
2. **Validation** — reject empty habit names and malformed `day` values on
   `POST /habits` / checkin with a 422/400 and a clear message.
3. **Weekly summary** — `GET /habits/{id}/summary` returns the count of check-ins in the
   last 7 days.
