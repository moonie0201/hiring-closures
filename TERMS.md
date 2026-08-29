# Terms — paid tiers

These terms apply to data delivered under a paid order. The free sample in `data/` is not
covered by them; it is dedicated to the public domain under [CC0 1.0](LICENSE).

This is not a copyright licence. We hold no copyright in the rows — they are facts, and
their arrangement is mechanical (*Feist v. Rural Telephone*, 499 U.S. 340 (1991)). What
this agreement rests on is stated honestly: **contract**, and the Korean database
producer's right under Articles 91, 93 and 95 of the Korean Copyright Act, which protects a
database made by a Korean national without any originality requirement. We do not assert a
right we do not hold.

## 1. Grant

A non-exclusive, non-transferable, non-sublicensable right to reproduce and use the
delivered files internally, including in derived analytics and internal products, for the
subscription term, and perpetually for files already delivered.

## 2. Not licensed

- Redistribution of the raw rows, in whole or in substantial part.
- Resale of the data, alone or bundled.
- Publication as a public dataset, under any licence.
- Use to construct a competing public closure dataset.

Derived aggregates and analyses you produce are yours to publish, provided they do not
reconstitute the raw rows.

## 3. Term

Monthly or annual, cancellable at any time with effect from the end of the paid period.
Files already delivered remain licensed after cancellation. There is no automatic price
change during a paid period.

## 4. No warranty of accuracy

The data is supplied **as observed**. A `removed` record means a job posting that was
returned by a company's public careers API on one day was no longer returned on a later
day. It is not a statement that anyone was hired, that a role was cancelled, or that anyone
lost a job. Postings also stop being returned for reasons we cannot observe, including
reposting under a new ID, board migrations, and provider outages.

Known limits are documented in the [README](README.md#limitations) and the
[coverage disclosures](PRICING.md#coverage-disclosures), and form part of these terms:
collection begins 2026-08-26; a day not collected is missing rather than zero; `days_open`
is a lower bound for postings already open on 2026-08-26 and for every Rippling posting.

No warranty of accuracy, completeness, fitness for a particular purpose, or continued
availability of any provider's public API is given. Liability is limited to the fees paid
in the twelve months preceding the claim.

## 5. No personal data supplied

We supply company-level observations. The data contains no names, no email addresses, no
phone numbers, no recruiter or candidate fields, and no job advertisement text. Job titles
and location strings are reproduced as the employer published them and are not scanned for
personal names.

You are the controller for anything you derive. If you believe a delivered row identifies
an individual, write to `mooniegilog@gmail.com` and it will be removed within 7 days and
blocked from future deliveries.

## 6. No job advertisement text

We do not collect, store, or sell job advertisement text. The body of a job ad is the
employer's own copyrighted work; we claim no rights in it and do not reproduce it. This is
not a configurable option.

## 7. Employer exclusion

An employer's exclusion request is honoured within 48 hours going forward: the board stops
being collected and its rows stop appearing in subsequent deliveries. Files already
delivered to you are outside our control, and we say so rather than promising a recall we
cannot perform.

## 8. Independence

This is an independent dataset. We are not affiliated with, endorsed by, or connected to
Greenhouse, Lever, Ashby, Recruitee, Rippling, Personio, or any employer named in it.

## 9. Governing law

Republic of Korea.

## 10. Contact

`mooniegilog@gmail.com`.
