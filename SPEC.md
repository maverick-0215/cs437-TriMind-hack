# SPEC: IITGN Lost and Found

## Users

- **Admin:** the security guard who stores found items and returns them to owners.
- **Student:** anyone at IITGN with an `@iitgn.ac.in` email.

## User quote

> "When a student loses something, they mail the security office. When something comes in, we send one mail to the whole IITGN community saying 'lost and found on <date>'. If it matches what a student reported, we mail them, ask a few questions if it is valuable, and return it. Everything happens over mail."
> — Security guard, IITGN security office *(paraphrased; replace with exact words)*

## Statements

Each statement has at least one automated test that names its ID.

### Access

- **S1.** Only `@iitgn.ac.in` emails can sign up or log in. Other emails are rejected.
- **S2.** A user whose email is in `ADMIN_EMAILS` (set in `.env`) is an admin. Every other user is a student.
- **S3.** A student gets 403 on every admin page and admin API route.
- **S23.** A visitor who is not logged in sees only the login and sign-up pages. Every other page sends them to the login page, and the items API returns 401.

### Found items

- **S4.** An admin can add a found item with a category, title, date found, general area, and private details: exact location, description and an optional photo.
- **S5.** A new found item has status `AVAILABLE`.

### Found-items list

- **S6.** A logged-in user can see the category, title, date found and general area of every `AVAILABLE` item, newest first.
- **S7.** The found-items list and its API never show private details.
- **S8.** A logged-in user can filter the list by category.
- **S9.** A logged-in user can filter the list by a date-found range.
- **S10.** A logged-in user can search the list by keyword. The search matches title or category and ignores case.

### Lost reports

- **S11.** A student can file a lost report with a category, title, date lost, place lost and private identifying details.
- **S12.** A student can see only their own lost reports. Opening another student's report returns 403 or 404.

### Matching

- **S13.** When an admin adds a found item, the app suggests every unlinked lost report with the same category and a lost date on or before the found date.
- **S14.** An admin can link any lost report to any found item, even if their categories differ.
- **S15.** When a lost report is linked, only the student who filed it gets an in-app notification.

### Claims and handover

- **S16.** A student can claim an `AVAILABLE` item by describing its identifying features. The item becomes `CLAIMED`, and the admin sees the claim next to the item's private details.
- **S17.** When an admin approves a claim, the app creates a 6-digit pickup code that only the claiming student can see.
- **S18.** When an admin rejects a claim, the item goes back to `AVAILABLE` and the student gets an in-app notification.
- **S19.** An item becomes `RETURNED` only when the correct pickup code is entered. A wrong code is rejected and the status does not change.
- **S20.** A pickup code works only once.

### Records

- **S21.** Every handover is logged with the item, student, admin, date and time.
- **S22.** Returned items do not appear on the found-items list.
