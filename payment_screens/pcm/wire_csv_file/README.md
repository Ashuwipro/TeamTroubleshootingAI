# Wire CSV File Frontend Module

PCM-specific frontend module for the `Wire .CSV File` payment screen under `payment_screens/pcm/wire_csv_file`.

- `ui.js`: Builds and wires the `.CSV Wire Domestic` / wire CSV form UI.
- `actions.js`: Handles wire CSV preview/generate API requests.

These files are served by backend route `/payment-screens/pcm/wire_csv_file/<filename>` and loaded by `backend/static/index.html`.

