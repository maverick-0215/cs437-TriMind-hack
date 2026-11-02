# SPEC: IITGN Lost and Found (core)

## Users

- **Security staff (admin):** the guard at the IITGN security office who stores found items and returns them to owners.
- **Student:** any IITGN community member with an `@iitgn.ac.in` email.

## User quote

> "When a student loses something, they mail the security office. When something comes in, we send one mail to the whole IITGN community saying 'lost and found on <date>'. If it matches what a student reported, we mail them, ask a few questions if it is valuable, and return it. Everything happens over mail."
> — Security guard, IITGN security office *(paraphrased; replace with exact words)*

## Statements

- **S1.** Only an `@iitgn.ac.in` email can log in. Any other domain is rejected, and a student account gets 403 on every admin page.
- **S2.** An admin can add a found item with category, title, date found, general area, and private details (exact location, description, optional photo). The item starts with status `AVAILABLE`.
- **S3.** Anyone can open the found-items page and see every `AVAILABLE` item's category, title, date found and general area, newest first.
- **S4.** The found-items page and its API never return an item's private details (exact location, description or photo).
- **S5.** Anyone can filter found items by category and date range, and search by keyword (case-insensitive, on title and category).
- **S6.** A logged-in student can file a lost report with category, title, date lost, place lost and private identifying details, and can see only their own reports.
- **S7.** When a found item is added, the app suggests every open lost report with the same category and a lost date on or before the found date. The admin can also link any report to any item manually.
- **S8.** When a lost report is linked to a found item, only the student who filed it is notified. No other user is notified.
- **S9.** An admin can approve a student's claim on an item, which generates a one-time 6-digit pickup code shown only to that student. The item is marked `RETURNED` only when the correct code is entered, and each code works only once.
- **S10.** Every handover is logged with the item, the student, the admin and the date and time, and returned items no longer appear on the public found-items page.
