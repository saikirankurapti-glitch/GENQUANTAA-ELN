# Functional Specification: Instrument Management Module

## 1. Purpose
The **Instrument Management Module** tracks, reserves, calibrates, and maintains high-value laboratory instruments (e.g. Mass Spectrometers, HPLC systems, NMR Spectrometers, Centrifuges, Bioreactors, Thermal Cyclers) used in scientific experiments and protocol execution.

## 2. Key Features
* **Instrument Lifecycle & Status:** Track operational status (`OPERATIONAL`, `MAINTENANCE`, `CALIBRATION_DUE`, `OUT_OF_SERVICE`) and availability status (`AVAILABLE`, `RESERVED`, `IN_USE`).
* **Calibration Management:** Log calibration events (`InstrumentCalibration`) with certificate numbers, results (`PASSED`, `FAILED`), and automatic next due date tracking.
* **Maintenance History:** Log preventive and corrective maintenance activities (`InstrumentMaintenance`) with vendor/engineer tracking.
* **Time-Slot Reservations:** Reserve instrument time slots (`InstrumentReservation`) tied to specific Experiments, preventing overlapping scheduling conflicts.
* **Usage History:** Audit logs of instrument run-time operations (`InstrumentUsage`) linked to Experiments and Protocols.
* **Document Attachments:** Store manuals, calibration certificates, and service reports (`InstrumentAttachment`).

## 3. Inputs & Outputs
* **Inputs:** `InstrumentCreate`, `InstrumentUpdate`, `InstrumentCalibrationCreate`, `InstrumentMaintenanceCreate`, `InstrumentReservationCreate`, `InstrumentFilter`.
* **Outputs:** `InstrumentRead`, `InstrumentDetail`, `InstrumentSummary`, `InstrumentCalibrationRead`, `InstrumentMaintenanceRead`, `InstrumentReservationRead`, `InstrumentUsageRead`, `InstrumentListResponse`.

## 4. Business Rules
1. `instrument_code`, `serial_number`, and `asset_tag` must be globally unique per tenant.
2. Only `OPERATIONAL` and `AVAILABLE` instruments can be reserved or used.
3. Overlapping time slot reservations for the same instrument are strictly prevented.
4. Instruments with overdue or failed calibrations cannot be reserved for active experiment runs.
5. Reservation end time must be greater than start time (`end_time > start_time`).

## 5. Workflow
```
[REGISTER INSTRUMENT] ---> [CALIBRATE / MAINTAIN] ---> [RESERVE FOR EXPERIMENT] ---> [LOG USAGE RUN]
```

## 6. Acceptance Criteria
1. Instrument code, serial number, and asset tag uniqueness must be enforced.
2. Reservation conflict checking must reject overlapping time intervals.
3. Calibration overdue status must be dynamically evaluated.
