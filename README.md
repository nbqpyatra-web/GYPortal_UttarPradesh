# UP-GY

Working repo for the Uttar Pradesh Gunvatta Yatra (UP GY), QCI-NBQP's NABH certification
drive for PM-JAY empanelled hospitals under SACHIS circular ABPMJAY/UP-GY/2026-27/161.

| Folder / file | What it holds |
|---|---|
| `portal/` | The monitoring portal, live at https://gyportaluttarpradesh-portal.vercel.app/ (Vercel deploys `main`): `index.html` (single-file dashboard), `build_data.py` (rebuilds its data from the route plan, hospital figures and Freshworks CRM), `up_districts.geojson` (district map), `assets/` (QCI, NABH and Ayushman Bharat PM-JAY logos). See [portal/README.md](portal/README.md). |
| `data/` | `Gunvatta_Yatra_UP_3Team_Plan.xlsx` (current plan: 56 yatras by three teams, 4 Nov 2026 – 30 Apr 2027), `plan_extras.json` (holidays, weekly rhythm, risks), `Planned_Yatras_All_Phases.xlsx` (used for its hospital figures) and `Gunvatta_Yatra_UP_Route_Plan.xlsx` (superseded 4-team plan, kept for reference). |
| `freshworks_mcp/` | MCP server that connects Claude Code to Freshworks CRM. See [freshworks_mcp/README.md](freshworks_mcp/README.md) for setup. |
| `.mcp.json` | Registers the Freshworks server with Claude Code. |
| `CLAUDE.md` | Project context, locked data definitions, schedule and working conventions. |
| `.claude/skills/frontend-design/` | Design skill used when building or restyling the portal. |

The Freshworks API key is never committed: it lives in the gitignored `freshworks_mcp/.env`
or in environment variables.
