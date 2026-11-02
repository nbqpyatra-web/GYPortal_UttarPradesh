# Freshworks CRM for Claude Code

A small MCP server that lets Claude Code read and update your Freshworks CRM
(Freshsales). It uses only the Python standard library, so there is nothing to install.
It is registered in [`.mcp.json`](../.mcp.json) at the repo root, so Claude Code finds it
automatically when you open this repo.

## 1. Get your credentials

1. Log in to Freshworks CRM.
2. Click your profile picture, then **Settings → API Settings**.
3. Copy your **API key**.
4. Note your **bundle domain** from the browser address bar, e.g. `yourcompany.myfreshworks.com`.

## 2. Provide them as environment variables

| Variable | Required | Example |
|---|---|---|
| `FRESHWORKS_DOMAIN` | yes | `yourcompany.myfreshworks.com` |
| `FRESHWORKS_API_KEY` | yes | your API key |
| `FRESHWORKS_BASE_URL` | no | `https://yourcompany.freshsales.io/api` for legacy accounts. Overrides the domain. |
| `FRESHWORKS_READ_ONLY` | no | `1` hides every tool that creates or changes data |

**Claude Code on the web (cloud sessions):** open the environment menu in the session
title bar, choose **Edit**, and add the variables above as environment variables or
secrets. Also make sure the environment's network access allows
`*.myfreshworks.com` (or `*.freshsales.io`). Start a new session for the change to apply.

**Claude Code on your own machine:**

```bash
export FRESHWORKS_DOMAIN=yourcompany.myfreshworks.com
export FRESHWORKS_API_KEY=xxxxxxxx
claude            # run from this repo; approve the "freshworks-crm" server when asked
```

Alternatively, put the same `KEY=value` lines in `freshworks_mcp/.env`, which is gitignored.
Don't commit your API key. `.mcp.json` only refers to it as `${FRESHWORKS_API_KEY}`.

## 3. Check it's working

In Claude Code, run `/mcp`. `freshworks-crm` should show as connected. Then try asking:

- "Find the contact with email priya@example.com in Freshworks"
- "Show my overdue Freshworks tasks"
- "List the deal stages and the open deals in the 'My Deals' view"
- "Add a note to deal 1234: client asked for revised pricing"
- "Create a follow-up task on contact 5678 for next Monday at 10am"

## Tools

| Tool | What it does |
|---|---|
| `search` | Full-text search across contacts, accounts and deals |
| `lookup` | Exact match on a field, e.g. a contact by email |
| `list_views` / `list_records` | Saved views, then the records in a view |
| `get_record` | One contact, account or deal, optionally with related data |
| `get_fields` | Field definitions, including custom fields |
| `get_selector` | Dropdown values: owners, deal_stages, territories, ... |
| `list_tasks` | Open, due today, overdue or completed tasks |
| `create_record` / `update_record` | Create or edit contacts, accounts and deals *(write)* |
| `add_note` / `create_task` | Log a note or a task against a record *(write)* |
| `api_request` | Any other endpoint of the [Freshworks CRM API](https://developers.freshworks.com/crm/api/). Only GET is allowed in read-only mode. |
