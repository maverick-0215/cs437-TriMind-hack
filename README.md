# CS437-TriMind-Hack

## G6: Lost and Found App

### Problem

Today, when someone hands in a found item, the security guard emails all college students, usually without photos, like *"Bottle found at library."* Students get so many of these mails that they start ignoring them, and the real owner often misses the one that matters. There is no way to report a lost item, so students have to keep checking mails or visit the security guard to ask. The guard also has no record of what is stored, how long it has been there, or who collected it, and has to judge ownership by guesswork.

### Features

- **Centralized Platform:** A single website/app where the admin enters each found item once, and students can view and search all currently found items instead of going through multiple emails.

- **Item Details & Privacy:** Students see only basic details and status (category, date found, and general area, like *"Bottle, found 3 Oct, Library area"*), while only authorized admins/security guards can access full descriptions, exact locations, and photos for verification.

- **Lost Item Reporting:** Students report lost items directly through the app with category, description, location, approximate time, and unique features (like a scratch or sticker) that only the admin can see. The report stays open and is checked against every new item that comes in.

- **Matching:** The app compares lost reports and found items in both directions, and the admin can also link them manually when descriptions don't match word for word.

- **Search & Filters:** Search and filter items by categories such as wallets, watches, umbrellas, cycles, electronics, etc., along with location and date.

- **Notifications:** Instead of mailing everyone, the app notifies only the student whose lost report matches a found item, or when the status of their reported item changes.

- **Security:** Login with college email or roll number, and claim verification where the admin compares the student's unique features with the actual item, plus a one-time pickup code at handover, so belongings reach the rightful owner.

- **Records:** Every item has a status, and every handover is logged with the name, date, and time. This saves the guard time and gives the college a clear record in case of disputes.

