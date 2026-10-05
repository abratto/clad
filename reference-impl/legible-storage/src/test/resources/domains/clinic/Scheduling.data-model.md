# Scheduling — conceptual data model

## Step 2 — Draft fact model and population check

### Object types

- Entity: `Physician`
- Entity: `Patient`
- Entity: `Timeslot`
- Value: `AppointmentStatus`
- Value: `Int`

### Fact types

- `appt: (Physician, Patient, Timeslot) -> AppointmentStatus`
- `consultFee: (Physician, Patient) -> Int`

### Population check

- An appointment status is recorded per physician/patient/timeslot triple.

## Machine model

```
object-type Physician identified-by Physician
object-type Patient identified-by Patient
object-type Timeslot identified-by Timeslot
fact appt : ( Physician, Patient, Timeslot ) -> AppointmentStatus -- mandatory, in {booked, seen, cancelled}
fact consultFee : ( Physician, Patient ) -> Int -- optional
independent ReferralSource
```

## Modeling Notes

- The appointment is objectified as a three-component individual; `consultFee`
  is charged per physician/patient pair, independent of the timeslot.
