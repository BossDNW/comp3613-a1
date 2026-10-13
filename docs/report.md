# COMP 3613 Assignment 1

Draft this file with the Guide. **Update it after every phase milestone** before you pause. The use-case diagram is a UML PNG at `docs/diagrams/use-case.png`, linked from this file as `diagrams/use-case.png` (path relative to `docs/report.md`). The model diagram is Mermaid. **Embed wireframe images** as `wireframes/<file>` (files live in `docs/wireframes/`).

Do not put your student ID in this file if you will commit it. The PDF cover adds your name and ID at export time.

## Assigned project
Student Accommodation

## Three workflows

### 1. Search & Filter Accommodation (Student)

### 2. Request Accommodation Booking (Student)

### 3. Manage Listings & Booking Requests (Landlord)

## Use case diagram

![Use case diagram](diagrams/use-case.png)

Phase 2 notes: Student starts search/filter and booking requests. Landlord management covers listing creation, editing, and deactivation, plus viewing, approving, and rejecting booking requests. The former detail-view and review workflows are not included in the revised workflow list.

## Model diagram

First draft. Update this section in Phase 5 when polish revises the model, and note what changed.

```mermaid
erDiagram
  USER ||--o{ LISTING : owns
  USER ||--o{ BOOKING_REQUEST : submits
  LISTING ||--o{ BOOKING_REQUEST : receives
  LISTING ||--o{ LISTING_PHOTO : displays
  LISTING ||--o{ LISTING_AMENITY : includes
  AMENITY ||--o{ LISTING_AMENITY : applies_to

  USER {
    int id PK
    string full_name
    string email
    string password_hash
    string role
    bool is_verified
    datetime created_at
  }

  LISTING {
    int id PK
    int landlord_id FK
    string title
    string city
    string suburb
    string address
    decimal price_per_month
    text description
    int bedrooms
    int bathrooms
    bool furnished
    date available_from
    string status
    datetime created_at
  }

  LISTING_PHOTO {
    int id PK
    int listing_id FK
    string image_url
  }

  BOOKING_REQUEST {
    int id PK
    int listing_id FK
    int student_id FK
    date move_in_date
    date move_out_date
    int occupants
    string status
    text message
    datetime created_at
    datetime updated_at
  }

  AMENITY {
    int id PK
    string name
  }

  LISTING_AMENITY {
    int listing_id FK
    int amenity_id FK
  }
```

Phase 3 notes: A `User` can act as either a student or a landlord through the `role` field, while `is_verified` helps support trust in the accommodation marketplace. One landlord can own many listings, and each listing contains the fields needed for search and filter, such as location, price, bedrooms, bathrooms, furnishing, and vacancy date. Each student can submit many booking requests, and a landlord can approve, reject, or cancel them through a single request record. Amenity data is modelled through a join table so a listing can include multiple features without repeating columns. The earlier review/detail extension was removed from the model because the revised workflow list focuses on listing management and booking decisions rather than reviewing or browsing detailed listing pages.

Phase 5 wireframe revision: Added `ListingPhoto` because the search cards and accommodation details wireframe display listing photos and a gallery. Ratings/review counts remain out of scope by student choice; no review entity or review widgets are included.

Phase 5 booking revision: Added `BookingRequest.occupants` for the required number-of-occupants form field. Student-selected behavior: pending requests can be updated or cancelled; accepted requests are read-only. Move-in dates earlier than the listing's `available_from` are rejected. The landlord's decision actions remain part of the landlord workflow.

## Wireframes

### Search & Filter Accommodation (Student)

![Search & Filter Accommodation](wireframes/search-filter-accommodation.png)

### Request Accommodation Booking (Student)

![Request Accommodation Booking](wireframes/request-accommodation-booking.png)

### Manage Listings & Booking Requests (Landlord)

![Manage Listings & Booking Requests](wireframes/manage-listings-booking-requests.png)

## Theming

Branding preferences and how they were applied (landing / login / register).

- Colors: modern student-housing palette using a bright blue primary, soft white surfaces, and teal accent highlights.
- Type: clean sans-serif UI with strong, readable headings for a trustworthy academic-housing feel.
- Tone: clear, useful, and welcoming; focused on helping students quickly find and book suitable accommodation.
- Wordmark: Student Accommodation.

Applied to the public landing page and the auth screens with a blue/white card layout, softened gradients, and a more direct student-rental message.

## Implementation notes

One named workflow at a time. Include verify notes and polish / model revisions (Phase 5). Do not treat the first build as final.

### Search & Filter Accommodation (Student) — wireframe alignment pass

- Student chose separate search, filtered-results, and listing-details pages.
- Search fields follow the corrected selection: city/suburb location, maximum monthly price, move-in date, bedrooms, bathrooms, and furnished status. Keyword and minimum-price fields were removed.
- Search/result cards show the image area, title, location, monthly price, and a View Details action. The details page shows the image gallery, location, price, description, amenities, landlord panel, and booking action. Ratings and review counts were deliberately left out.
- The results route passes normalized filters to `ListingService`; repository methods own listing/photo/amenity data access. The detail service coordinates listing lookup and related data; missing listings return 404.
- Search polish: demo listings are restricted to Trinidad and locations around the UWI St. Augustine campus / other Trinidad communities. The location field now searches listing titles and location/details text token-by-token. Common misspelling `appartment` is normalized to `apartment`; phrases such as `1 bedroom apartment` also match the exact bedroom count stated in the phrase. The separate bedroom filter remains a minimum.
- Model revision: `ListingPhoto` belongs to one `Listing` through `listing_id`; the existing `Amenity` / `ListingAmenity` ERD structure is registered and read for the detail page.
- Styling polish: strengthened the marketplace navigation bar, made it sticky on desktop, increased contrast and separation between filter and results panels, and added clearer card borders/shadows. The shared stylesheet URL now has a version query so browsers request the updated CSS.
- Verification: student confirmed all three named workflows are working, including searching listings by listing title and Trinidad location.

### Request Accommodation Booking (Student)

- Implemented a listing-specific request form with required move-in date and occupant count plus optional move-out date and message.
- Successful submission creates a pending request, shows a confirmation page, and links to the student's request dashboard.
- The dashboard shows total, pending, and accepted counts plus the student's recent requests. Students can view their own request only; pending requests can be edited or cancelled, and non-pending requests are read-only.
- Service rules reject unavailable listings, move-in dates before the listing availability date, move-out dates that are not after move-in, and occupant counts below one.
- Persistence is in `BookingRequestRepository`; routes delegate to `BookingRequestService`. Request lookups are scoped to the authenticated student's ID.
- Runtime issue follow-up: removed duplicate service/repository method definitions that shadowed the validated create flow. Database recovery now retries a failed-schema request once and propagates a second failure instead of redirecting the same GET URL indefinitely. The local SQLite `bookingrequest` table was confirmed to contain only `id`; after the student's approval to reset local data, `python manage.py init` recreated the schema and demo data. The table now contains the full request schema (`listing_id`, `student_id`, dates, occupants, status, message, timestamps).
- Verification: Pylance and Python syntax checks pass; schema inspection confirms the booking request columns now exist. Student confirmed the booking workflow works.

<!-- student-build:code-check
workflow: Request Accommodation Booking (Student)
form: choice
layer: service
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Chose pending requests editable/cancellable and accepted requests read-only; identified service as coordinating request validity.
-->

<!-- student-build:code-check
workflow: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Student added BookingRequest ERD fields plus the occupant count from the wireframe.
-->

<!-- student-build:code-check
workflow: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Student implemented POST handler calling BookingRequestService; no persistence logic in the route.
-->

### Manage Listings & Booking Requests (Landlord)

- Landlord wireframe implemented from `wireframes/manage-listings-booking-requests.png`: dashboard totals, recent booking requests, listing rows, request detail with accept/reject, and add/edit/deactivate/reactivate listing paths.
- Listing creation and editing use the existing `Listing`, `ListingPhoto`, `Amenity`, and `ListingAmenity` ERD entities. The student selected direct image URL fields; photo URLs are validated and saved as `ListingPhoto.image_url`.
- Listing/request persistence is in `LandlordManagementRepository`; `LandlordManagementService` enforces landlord role, listing ownership, request ownership, validation, and pending-only accept/reject actions. Landlord routes call the service and contain no persistence queries.
- Landlord listings are restricted to Trinidad locations; their entered location is stored in the existing listing location fields. Deactivated listings are marked inactive and are excluded by student search.
- The seed command now adds a small set of amenities idempotently; run `python manage.py seed` to make the feature choices available without resetting existing data.
- Polish from student testing: landlord accounts cannot submit booking requests. The student-side action is hidden for landlords, and GET/POST request entry points enforce the role restriction.
- Verification: Pylance, syntax, and diff whitespace checks pass. Student confirmed the landlord dashboard, listing, and request flows work against the wireframe, and retested that landlords cannot see or directly access booking-request submission.

<!-- student-build:code-check
workflow: Manage Listings & Booking Requests (Landlord)
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.83
passed: yes
note: Student implemented a thin landlord dashboard route that calls LandlordManagementService and renders the dashboard.
-->

<!-- student-build:code-check
workflow: Manage Listings & Booking Requests (Landlord)
form: choice
layer: other
architecture_ok: yes
implement_confidence: 0.83
passed: yes
note: Selected image URL fields for listing photos.
-->

<!-- student-build:code-check
workflow: Manage Listings & Booking Requests (Landlord)
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.83
passed: yes
note: Added ListingPhoto.image_url to match the selected image URL input.
-->

### Account Profile

- The top-right person icon opens Profile Settings; the page supports a separate full/display name while keeping the username as the sign-in identifier.
- Password changes require the current password, a matching confirmation, and a minimum eight-character new password.
- Account deletion requires the current password, a checkbox confirmation, and a browser confirmation prompt. As selected by the student, deletion permanently removes the user's listings and the booking requests associated with the student or those listings.

- Profile updates and deletion are coordinated through `ProfileService` and persisted through `UserRepository`; routes do not contain SQL.
- Added an idempotent schema migration for the new `user.full_name` column so existing databases can retain their data.
- Applied the additive migration to the current local database and confirmed the `full_name` column exists.

<!-- student-build:code-check
workflow: Account Profile
form: choice
layer: service
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Chose separate display name, current-password verification for password changes and deletion, and deleting associated listings/requests.
-->

<!-- student-build:code-check
workflow: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Student added the separate full_name field to the User model.
-->

<!-- student-build:code-check
workflow: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Student completed the profile GET route to call ProfileService and render the profile template.
-->

<!-- student-build:code-check
workflow: Search & Filter Accommodation (Student)
form: choice
layer: other
architecture_ok: yes
implement_confidence: 0.85
passed: yes
note: Chose separate search, results, and details pages; chose ListingPhoto for multiple photos per listing; chose to omit reviews/ratings.
-->

<!-- student-build:code-check
workflow: Search & Filter Accommodation (Student)
form: mcq
layer: service
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Identified the service as coordinating listing lookup and missing-listing behavior.
-->

<!-- student-build:code-check
workflow: Search & Filter Accommodation (Student)
form: open
layer: service
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Explained that the route passes selected filters, the service coordinates filtering, and the repository handles database access.
-->

<!-- student-build:code-check
workflow: Search & Filter Accommodation (Student)
form: snippet
layer: model
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Student added ListingPhoto with a listing foreign key and image_url.
-->

<!-- student-build:code-check
workflow: Search & Filter Accommodation (Student)
form: snippet
layer: router
architecture_ok: yes
implement_confidence: 0.90
passed: yes
note: Student implemented filtered results by calling ListingService.search_listings; no persistence logic in the route.
-->

### Phase 5 polish and exit

- Student confirmed that Search & Filter Accommodation, Request Accommodation Booking, and Manage Listings & Booking Requests all work.
- Incorporated the reported landlord-role restriction: landlord accounts can manage requests but cannot submit booking requests.
- Updated the landing-page demo login text to show the landlord demo credentials.
- Phase 5 exit gate met; local workflow verification and student-directed polish are recorded above. Phase 6 deployment has not started.

## Deployed app

Phase 6. Public Render URL (not localhost). Markers open this to mark the three workflows.

https://

## Logins

Every account a marker needs, including extra users you added. Starter accounts:

- bob / bobpass — regular user
- landlord / landlordpass — landlord
- admin / adminpass — admin

## YouTube URL

## Session transcripts

Filled when the Guide builds the report: the agent writes each Guide chat to `docs/transcripts/<slug>.md` (Copilot Agent, Cursor, or OpenCode). `python manage.py report` packages them. Do not paste chats here during the build.

## Competency (student-judge)

Filled when the report is built. Guide runs student-judge, writes `docs/judge.md`, and export appends the scorecard here.

## Skill integrity

Filled by `python manage.py report`. Do not edit the course skills.
