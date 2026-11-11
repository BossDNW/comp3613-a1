# Assignment 2 Testing

## Test Planning

### User Acceptance Test Plan

These acceptance tests follow the Assignment 1 wireframes in `docs/wireframes/`.

| Test Case | Pre-conditions | Test Steps | Test Criteria / Expected Result | Success |
|---|---|---|---|---|
| Search & Filter Accommodation — Student | The application is available. The student is signed in, and at least two accommodation listings with different locations or attributes are available. | 1. Open the accommodation search page. 2. Enter a search location and select one or more available filters. 3. Submit the search. 4. Review the results and open a listing's details. | The results page shows listings matching the search and selected filters. The detail page shows the selected accommodation's information, images, amenities, and landlord, with a way to return to results. | Pass |
| Request Accommodation Booking — Student | The student is signed in. An available listing can be opened and has dates that allow a valid booking request. | 1. Open the listing details and choose Request Booking. 2. Enter a move-in date, optional move-out date, occupant count, and optional message. 3. Send the request. 4. Open My Requests and review the new request. | A confirmation is shown after submission. The request appears in the student's dashboard with Pending status and the submitted request details. The dashboard provides access to view a request; the wireframe also shows update/cancel controls for pending requests and a read-only accepted-request state. | Pass |
| Manage Listings & Booking Requests — Landlord | The landlord is signed in. The account has at least one listing and a booking request associated with one of its listings. | 1. Open the landlord listing dashboard. 2. Review listing and request counts and recent requests. 3. Open a request and accept or reject it. 4. Return to the dashboard and open Add Listing or Edit Listing. 5. Enter listing information and submit. | The dashboard presents the landlord's listings and request statuses. A pending request can be accepted or rejected and the resulting status is reflected in the dashboard. The landlord can submit a new listing or save changes to an existing listing. | Pass |

#### UAT Results

All 3 planned UAT workflows were manually executed and passed.

### Unit Test Plan

Unit tests exercise service methods and functions in isolation. Repository dependencies are mocked with `MagicMock`; the unit tests do not connect to or require a database.

| Unit Test | Module Tested | Expected Output |
|---|---|---|
| `test_search_normalizes_appartment_to_apartment` | `app.services.listing_service.ListingService.search_listings` | Normalizes the misspelled search phrase and passes the normalized location and default filters to the repository. |
| `test_search_extracts_exact_bedroom_count` | `app.services.listing_service.ListingService.search_listings` | Removes the exact-bedroom phrase from the location and passes the exact bedroom count to the repository. |
| `test_search_passes_other_filters_to_repository` | `app.services.listing_service.ListingService.search_listings` | Forwards the normalized location and supplied price, bedroom, bathroom, furnishing, and availability filters. |
| `test_listing_details_returns_none_when_listing_missing` | `app.services.listing_service.ListingService.listing_details` | Returns `None` when the repository cannot find an available listing. |
| `test_listing_details_returns_related_data` | `app.services.listing_service.ListingService.listing_details` | Returns the listing, landlord, photos, and amenities, retrieving related records through the repository. |
| `test_landlord_cannot_submit_booking_request` | `app.services.booking_request_service.BookingRequestService.require_booking_student` | Raises `PermissionError` for a landlord account. |
| `test_missing_user_cannot_submit_booking_request` | `app.services.booking_request_service.BookingRequestService.require_booking_student` | Raises `PermissionError` when the user does not exist. |
| `test_move_in_before_available_date_is_invalid` | `app.services.booking_request_service.BookingRequestService._validate_request` | Raises `ValueError` when the requested move-in date precedes the listing's available date. |
| `test_move_out_must_be_after_move_in` | `app.services.booking_request_service.BookingRequestService._validate_request` | Raises `ValueError` when the move-out date is not after the move-in date. |
| `test_occupants_must_be_at_least_one` | `app.services.booking_request_service.BookingRequestService._validate_request` | Raises `ValueError` when the occupant count is below one. |
| `test_valid_booking_request_is_created` | `app.services.booking_request_service.BookingRequestService.create_booking_request` | Creates and returns a pending request with the supplied student, listing, occupant, and date data. |
| `test_non_pending_request_cannot_be_updated` | `app.services.booking_request_service.BookingRequestService.update_booking_request` | Raises `ValueError` when attempting to update a non-pending request. |
| `test_pending_request_can_be_cancelled` | `app.services.booking_request_service.BookingRequestService.cancel_booking_request` | Cancels a pending request through the repository and returns the request. |
| `test_non_landlord_is_rejected` | `app.services.landlord_management_service.LandlordManagementService.require_landlord` | Raises `PermissionError` for a non-landlord account. |
| `test_missing_user_is_rejected` | `app.services.landlord_management_service.LandlordManagementService.require_landlord` | Raises `PermissionError` when the account does not exist. |
| `test_dashboard_calculates_totals` | `app.services.landlord_management_service.LandlordManagementService.dashboard` | Returns the total listings, pending requests, and accepted requests counts from repository data. |
| `test_update_listing_fails_if_listing_not_owned` | `app.services.landlord_management_service.LandlordManagementService.update_listing` | Raises `LookupError` when the landlord does not own the requested listing. |
| `test_invalid_booking_decision_is_rejected` | `app.services.landlord_management_service.LandlordManagementService.decide_booking_request` | Raises `ValueError` for an unsupported booking decision. |
| `test_non_pending_booking_request_cannot_be_decided` | `app.services.landlord_management_service.LandlordManagementService.decide_booking_request` | Raises `ValueError` when attempting to decide a request that is not pending. |
| `test_valid_pending_request_can_be_accepted` | `app.services.landlord_management_service.LandlordManagementService.decide_booking_request` | Accepts a valid pending request and asks the repository to persist the accepted status. |

### Integration Test Plan

Integration tests use a per-test, in-memory SQLite database (`sqlite://`) with a `StaticPool`. The fixture creates the SQLModel schema for each test and drops it afterward. Tests use actual models, repositories, services, and database sessions to verify persistence and interactions.

| Test | Dependencies | Description |
|---|---|---|
| `test_user_is_saved_and_retrieved_from_database` | In-memory SQLite test database, `User` model, `UserRepository` | Saves a user, commits and refreshes it, then retrieves it by ID and verifies its username and email. |
| `test_listing_is_saved_and_found_by_search` | In-memory SQLite test database, `User` and `Listing` models, `ListingRepository`, `ListingService` | Persists users and a listing, searches through the service/repository, and verifies the matching listing is returned. |
| `test_booking_request_is_created_and_persisted` | In-memory SQLite test database, user/listing/booking request models, their repositories, `BookingRequestService` | Creates a booking request through the service and verifies the request and its student, listing, message, and pending status are persisted. |
| `test_booking_request_can_be_cancelled_and_change_persists` | In-memory SQLite test database, user/listing/booking request models, their repositories, `BookingRequestService` | Creates and cancels a request through the service, then reloads it and verifies its status is `cancelled`. |
| `test_student_dashboard_reads_booking_requests_from_database` | In-memory SQLite test database, user/listing/booking request models, their repositories, `BookingRequestService` | Creates two requests and verifies the student dashboard's total, pending, accepted, and row values reflect database records. |
| `test_inactive_listing_is_not_returned_in_student_search` | In-memory SQLite test database, user/listing models, `ListingRepository`, `ListingService` | Persists an inactive listing and verifies student search does not return it. |

## Test Implementation

### Unit Tests

The existing files under `tests/unit/` contain 20 passing unit tests:

| Pytest file | Tests | Coverage |
|---|---:|---|
| `tests/unit/test_listing_service.py` | 5 | Listing search normalization and filter forwarding; listing details and related data. |
| `tests/unit/test_booking_request_service.py` | 8 | Student authorization, request date and occupant validation, request creation, update restrictions, and cancellation. |
| `tests/unit/test_landlord_management_service.py` | 7 | Landlord authorization, dashboard counts, listing ownership, and booking decision validation and acceptance. |

### Integration Tests

The existing file `tests/integration/test_accommodation_workflows.py` contains 6 passing integration tests covering user persistence, listing search, booking-request creation and cancellation, student dashboard reads, and filtering inactive listings.

### API Tests

The following REST API routes are currently implemented for Postman testing:

| Method and route | Current behavior |
|---|---|
| `GET /api/listings` | Searches listings. Optional query parameters include `location`, `max_price`, `bedrooms`, `bathrooms`, `furnished`, and `available_from`. |
| `GET /api/listings/{listing_id}` | Returns listing details, landlord information, photos, and amenities; returns 404 if the listing is not found. |
| `POST /api/listings/{listing_id}/requests` | Creates a booking request for the authenticated user. The request body includes `move_in_date`, optional `move_out_date`, `occupants`, and optional `message`; successful creation returns 201. |
| `GET /api/requests` | Returns the authenticated student's booking-request dashboard. |

The Postman collection was completed and exported to `postman/COMP3613_A2.postman_collection.json`. The full collection run completed with **17 tests passed, 0 failed, 0 skipped, and 0 errors**.

Tested API outcomes:

| Request or outcome | Result |
|---|---:|
| `GET /api/listings` | 200 |
| `GET /api/listings/{listing_id}` | 200 |
| Missing listing | 404 |
| Unauthenticated booking request | 401 |
| Successful login | 303 |
| Authenticated booking request | 201 |
| Invalid booking request | 422 |
| `GET /api/requests` | 200 |

## Verification

The existing suite was run with `python -m pytest -q tests\unit tests\integration`: **26 passed** (20 unit and 6 integration). The run also emitted 41 deprecation warnings.
