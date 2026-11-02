# UP Gunvatta Yatra portal

A single-file monitoring portal (`index.html`) for the UP GY programme. Open it in a
browser; it needs internet only for fonts and the d3 map library.

## Sections

The main pages cover only the 63 UP GY yatras in the 4-team route plan
(`data/Gunvatta_Yatra_UP_Route_Plan.xlsx`, 23 Oct 2026 – 19 Mar 2027). Anything earlier lives
on the Past yatras page.

| Section | What it shows |
|---|---|
| Overview | Route strip (four team lanes, reserve slots, skipped festival weeks), KPIs, calendar with holidays, district map (status, team or NABH gap), next-up queue, the selected yatra's full plan detail, and team progress |
| Yatras | All 63 yatras with team, leg, CRM status and readiness, sortable and searchable |
| Teams | Each team's route in order (from, km, calendar caution, earlier visit), editable member name and home base, yatras per month |
| Districts | Map plus all 75 districts: PM-JAY universe, NABH, gap, UP GY yatra date and results |
| Lead funnel | Registered → attended → potential leads → won for UP GY yatras, every CRM status, leads by district |
| Readiness | Shared tracker per yatra following the weekly rhythm: CMO letter (T-30), target list (T-15), venue and AV (T-10), NABH faculty (T-7), CMO SPOC (Monday before); late items flagged; SPOC, venue, faculty names and notes |
| Calendar and risks | How the plan works, the Friday calendar, notes and risks, weekly rhythm, UP holidays |
| Data checks | UP GY problems (yatra held without a CRM event, CRM event not in the planner, date mismatch, missing attendance) and clean-up items for past records |
| Past yatras | CRM events before 23 Oct 2026, attendance by month, delivery-approach comparison (QCI team view only) and the (VF) district baseline |

"View as: District CMO" hides the delivery-approach comparison and partner details,
in line with the dashboard spec.

## Readiness tracker

The tracker saves to the published artifact's shared database (`readiness/<yatra id>`,
e.g. `readiness/T2-C1-L3`, and `teams/<T1..T4>` for member names), so it works only in the published portal on claude.ai. Anyone
with Contributor access or above can edit; Viewers see it read-only. Each record keeps
who changed it last and when.

## Refreshing the data

The data is embedded in `index.html`. Rebuild it with:

```bash
python3 portal/build_data.py            # live pull from Freshworks (~9 min, ~860 API calls)
python3 portal/build_data.py --cached   # reuse the last pull (after editing the page or planner)
python3 portal/build_data.py --no-crm   # planner only
```

Sources: `data/Gunvatta_Yatra_UP_Route_Plan.xlsx`, `data/Planned_Yatras_All_Phases.xlsx`, Freshworks CRM (credentials as in
`freshworks_mcp/README.md`) and `up_districts.geojson` (simplified 2011 census
district boundaries). Only aggregate counts are taken from the CRM.

## Rules applied

- A CRM event is any distinct Event Name with Board = NABH, Event Type = Yatra /
  Gunvatta Mohotsav / Gunvatta Yatra, and either state field = Uttar Pradesh. Events
  whose text state names another state are dropped; `NABH_ADDITIONAL_Y` is excluded.
- UP GY = the 63 planned yatras from the joint Lucknow launch on 23 Oct 2026; earlier yatras are history.
- Hospital figures (PM-JAY, NABH, gap, baseline) come from `data/Planned_Yatras_All_Phases.xlsx`,
  the (VF) Final Sheet copy; the builder stops if the route plan's districts are not exactly the 75.
- Potential leads = Hot + Warm + Application in progress. Won = CRM "Won" +
  "Application submitted". Close rate = Won ÷ (Hot + AIP + Won).
- Gap = PM-JAY universe − NABH total, floored at 0. The map colours by absolute gap.
- A planned yatra is linked to a CRM event in one of its districts dated within 3 days of
  the plan date. CRM events from 23 Oct 2026 that match no planned yatra are listed in
  Data checks; events before 23 Oct 2026 go to Past yatras only.

## Logos

`portal/assets/` holds the logos embedded in the page header (resized copies; the page
itself carries them as data URIs). QCI and NABH come from nabh.co (`qci-full-logo.png`,
`cropped-nabh-logo-1.png`).
The Ayushman Bharat PM-JAY logo (`pmjay-logo.png`) was supplied by Rachit on 14 Oct 2026 and sits
beside the SACHIS label. A separate SACHIS logo can replace or join it when supplied.
