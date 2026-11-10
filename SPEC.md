# SPEC: IITGN Lost and Found

## Users

- **Admin:** the security guard who stores found items and returns them to owners.
- **Student:** anyone at IITGN with an `@iitgn.ac.in` email.

## User quote

> "When a student loses something, they mail the security office. When something comes in, we send one mail to the whole IITGN community saying 'lost and found on <date>'. If it matches what a student reported, we mail them, ask a few questions if it is valuable, and return it. Everything happens over mail."
> Security guard, IITGN security office *(paraphrased; replace with exact words)*

## Statements

Each statement has at least one automated test that names its ID.

### Access

- **S1.** People sign in with their Google account; the app has no passwords. Only verified `@iitgn.ac.in` Google accounts that IITGN's Google Workspace manages (hosted domain `iitgn.ac.in`) can sign up or log in. Other accounts are rejected, including a personal Google account made with an IITGN address.
- **S2.** A user whose email is in `ADMIN_EMAILS` (set in `.env`) or was added by an admin (S28) is an admin. Every other user is a student.
- **S3.** A student gets 403 on every admin page and admin API route.
- **S23.** A visitor who is not logged in sees only the login and sign-up pages. Every other page sends them to the login page, and every other API route returns 401.
- **S24.** The login page has two options, "Sign in as student" and "Sign in as admin". Choosing admin with an email not in `ADMIN_EMAILS` is rejected, and an admin email is rejected on the student option. The choice never grants a role.
- **S28.** An admin can add another `@iitgn.ac.in` email as an admin, and remove admins added this way, except themselves. Emails in `ADMIN_EMAILS` are permanent admins and can only be changed in `.env`.

### Found items

- **S4.** An admin can add a found item with a category, title, date found, general area, and private details: exact location, description and an optional photo. A photo must be an image of at most 5 MB; anything else is rejected.
- **S5.** A new found item has status `AVAILABLE`.
- **S6.** A logged-in user can see a list of every `AVAILABLE` found item, newest first, with its title, category, date found, where it was found (general area) and who to contact: the security office (`SECURITY_CONTACT`), never an admin's own email.
- **S7.** Students never see a found item's private details (exact location, description, photo) anywhere in the app or its API.
- **S31.** The date found and the date lost cannot be after today. The date pickers do not offer future dates, and the API rejects them.
- **S32.** Sending the same lost report or found item again within 2 minutes (a double click, or a retry on a slow connection) does not create a copy. The one already saved is returned, and nobody is notified twice. The form's button is disabled while it saves.

### Lost reports

- **S11.** A student can file a lost report with a category, title, date lost, place lost and private identifying details.
- **S12.** A student can see only their own lost reports. Opening another student's report returns 403 or 404.
- **S25.** A student's lost report shows every `AVAILABLE` found item that matches it by at least 60% (S13), best match first, with the match percentage, where it was found (general area) and who to meet. It never shows private details. If there are none, the page says no such item is here yet and that they will be notified.
- **S33.** A student can add an optional photo to a lost report, with the same limits as a found item's photo (S4). Like the identifying details, only that student and admins can see it; admins see it next to the report when it matches a found item.

### Matching

- **S13.** A lost report and a found item get a match score from 0 to 100% using only the item's public fields: same category (40), shared words in the title and category (up to 30; the item's category counts as a word only when the report's category is different, so a report titled just "Electronics" does not match every electronics item), shared words in the place lost and general area (up to 15), and how soon after the lost date the item was found (up to 15). Items found one day before the lost date still get full date points, since students often get the date off by one; items found earlier get nothing for date. A score of 60% or more is a match.
- **S26.** When an admin adds a found item, every student with a lost report that matches it gets an in-app notification. No one else does.

### Approval and handover

Students do not claim items in the app. They see a match, go to the security office, and the guard checks them in person.

- **S14.** Students cannot claim items through the app.
- **S16.** On a found item's page, an admin sees the students whose lost reports match it, with their identifying details, next to the item's private details. After checking a student in person, the admin can approve them, or approve any `@iitgn.ac.in` email. The item becomes `CLAIMED`. Only `AVAILABLE` items can be approved, and admins cannot be approved.
- **S17.** Approval creates a 6-digit pickup code that only the approved student can see. It is emailed to them (so someone approved by email who has not signed in yet still gets it) and shown on their Pickup codes page; it never appears to admins or in an in-app notification. If the email fails, the approval still stands.
- **S18.** An admin can cancel an approval until its code is used. The item goes back to `AVAILABLE` and the student is notified in the app and by email.
- **S19.** An item becomes `RETURNED` only when the correct pickup code is entered. A wrong code is rejected and the status does not change. After 5 wrong codes for one approval, every code is refused, even the right one, until the admin cancels the approval and approves the student again, which sends a new code.
- **S20.** A pickup code works only once.
- **S27.** An approval is tied to the student's lost report: the one the admin approved from, or else the student's best open matching report. The report then shows as approved, and once the item is collected it shows as **Closed** with the collection date. A cancelled approval reopens it. Approved and closed reports get no more matches, suggestions or notifications.

### Records

- **S21.** Every handover is logged with the item, student, admin, date and time.
- **S22.** Returned items are no longer shown as matches.
