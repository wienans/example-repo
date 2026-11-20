# ADR-0004 Fixed-point arithmetic

- Status: accepted
- Date: 2026-11-18

## Context

{need}`SYS-007` asks for the same outputs on every target. Many small MCUs have no FPU, so `float` there runs in a software library with data-dependent timing. Where an FPU exists, rounding can still differ from the host build that the unit tests run on.

## Decision

Use integer arithmetic in every layer above the HAL port.

- Speeds are `int32_t` rpm, currents are `int32_t` mA, and duty is `int16_t` permille.
- PI gains are Q8 integers. A gain of 256 means 1.0. `pi_step` multiplies in 32 bits and shifts right by 8.
- The integral term is clamped so it can never push the output past its limits ({need}`SWR-PI-002`). This also bounds every intermediate value.

`tools/check_layers.py` rejects `float` and `double` outside `src/hal/port/` ({need}`SWR-DET-001`). The host port may use `double` for its plant model, because the plant stands in for physics, not for firmware.

## Consequences

- Unit tests compare exact integers, with no tolerance.
- Q8 gives gain steps of 1/256. That is fine enough for this speed loop. A loop that needs finer gains would move to Q16 and widen the products to `int64_t`.
- Each new physical quantity needs its unit stated in its type name and its Doxygen comment.
