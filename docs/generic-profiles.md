# Generic category profiles

`trongpok-analyze` uses the storage profile by default. Profiles supply the units, conversion factors, minimum delivered ratio, measured review roles, mismatch types and prompt guidance. The Q1–Q5 rule order, two-buyer requirement, 10-review minimum, confidence scoring and human verdict still run through the same rules. The cached storage replay produces the same 10 flag records and dashboard export as `prep/research` at `7f8f33c`.

## Power bank sample

The power bank profile is marked **pending human review**. These three listings are **Sample data**. They use saved synthetic findings that describe completed USB-tester discharges at the output port.

| Sample | Expected result |
|---|---|
| Two independent buyers measure below 50% of the advertised 20,000 mAh | RED Q3 |
| The tester reads about 65% and 10 matched text reviews are checked | GREEN Q5 |
| One buyer reports a shortfall without a measurement | YELLOW Q4 |

Run all three from the repository root.

```sh
uv run --locked trongpok-analyze \
  --profile power_bank --allow-draft \
  --findings-dir tests/fixtures/power_bank/findings \
  --output-dir .profile-sample-flags \
  tests/fixtures/power_bank/listings/*.json
```

The power bank example compares mAh and Ah. Wh requires a comparable voltage basis and is unresolved in this profile.

## Add a category

1. Add `profiles/<category>.json` with an ID matching its filename and a human review status. Use the storage or power bank profile as a starting point.
2. Set the advertised unit and give each supported unit a conversion factor into the same comparison unit. Include multiple measurement factors where a label has multiple readings. The rules use the largest factor before comparing the result to the advertised value. A result strictly below the tolerance counts as a measured shortfall.
3. Set the attribute, review roles, measured subset, mismatch types, normal reading and prompt traps. Check `load_profile("<category>")` and add sample cases for normal readings, measured shortfalls and unmeasured complaints.
4. For saved listings, provide `promise_value` in the profile's advertised unit and `measurement_text` on each option. Supply matching saved findings with exact quotes. A measured finding for a non-storage category needs an explicit supported unit in the quote. Choose the profile with `--profile`, or pass it to `build_flags(..., profile=load_profile("<category>"))`.

## Storage-only paths

The existing KB and its market and Mall lookups, brand-page capacities, live claim and review readers, image classification and re-read, evaluation, and web and Streamlit review flows still use the storage data contracts. Non-storage analysis uses saved listing and finding files, so Q1 and Q2 need a future category-specific reference adapter. The review and confidence prompt builders accept category profiles. The live `--read` pipeline still uses the storage schemas and reader cache.
