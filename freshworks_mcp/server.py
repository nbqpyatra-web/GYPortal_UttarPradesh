#!/usr/bin/env python3
"""Freshworks CRM (Freshsales) MCP server for Claude Code.

A dependency-free MCP server speaking JSON-RPC over stdio. It exposes tools for
searching and managing contacts, accounts, deals, notes and tasks through the
Freshworks CRM REST API.

Configuration (environment variables):
  FRESHWORKS_DOMAIN     e.g. "yourcompany.myfreshworks.com" (required unless
                        FRESHWORKS_BASE_URL is set)
  FRESHWORKS_API_KEY    API key from Profile Settings -> API Settings (required)
  FRESHWORKS_BASE_URL   optional full API base, e.g.
                        "https://yourcompany.freshsales.io/api" for legacy accounts
  FRESHWORKS_READ_ONLY  set to "1" to disable every tool that writes data

Any of these may also be put in freshworks_mcp/.env (KEY=value lines, gitignored);
real environment variables take precedence.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "freshworks-crm", "version": "1.0.0"}

ENTITY_PATHS = {
    "contact": "contacts",
    "sales_account": "sales_accounts",
    "deal": "deals",
}
TARGETABLE_TYPES = {
    "contact": "Contact",
    "sales_account": "SalesAccount",
    "deal": "Deal",
}


class FreshworksError(Exception):
    pass


def load_env_file():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip().upper(), value.strip().strip("'\"")
            if not os.environ.get(key):
                os.environ[key] = value


def base_url():
    explicit = os.environ.get("FRESHWORKS_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    domain = os.environ.get("FRESHWORKS_DOMAIN", "").strip()
    if not domain:
        raise FreshworksError(
            "FRESHWORKS_DOMAIN is not set (e.g. yourcompany.myfreshworks.com)."
        )
    domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    domain = domain.split("/")[0]  # accept "x.myfreshworks.com/crm/sales" too
    return f"https://{domain}/crm/sales/api"


def api(method, path, params=None, body=None):
    key = os.environ.get("FRESHWORKS_API_KEY", "").strip()
    if not key:
        raise FreshworksError("FRESHWORKS_API_KEY is not set.")
    url = f"{base_url()}/{path.lstrip('/')}"
    if params:
        clean = {k: v for k, v in params.items() if v is not None and v != ""}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Token token={key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {"status": resp.status}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:2000]
        raise FreshworksError(f"HTTP {e.code} for {method} {path}: {detail}")
    except urllib.error.URLError as e:
        raise FreshworksError(f"Could not reach {url}: {e.reason}")


def entity_path(entity):
    if entity not in ENTITY_PATHS:
        raise FreshworksError(f"entity must be one of {sorted(ENTITY_PATHS)}")
    return ENTITY_PATHS[entity]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def t_search(a):
    return api("GET", "search", {
        "q": a["query"],
        "include": a.get("include", "contact,sales_account,deal"),
        "per_page": a.get("per_page", 25),
    })


def t_lookup(a):
    return api("GET", "lookup", {
        "q": a["value"],
        "f": a.get("field", "email"),
        "entities": a.get("entities", "contact,sales_account,deal"),
    })


def t_list_views(a):
    return api("GET", f"{entity_path(a['entity'])}/filters")


def t_list_records(a):
    return api("GET", f"{entity_path(a['entity'])}/view/{a['view_id']}", {
        "page": a.get("page", 1),
        "per_page": a.get("per_page", 25),
        "sort": a.get("sort"),
        "sort_type": a.get("sort_type"),
    })


def t_get_record(a):
    return api("GET", f"{entity_path(a['entity'])}/{a['id']}", {
        "include": a.get("include"),
    })


def t_create_record(a):
    entity = a["entity"]
    return api("POST", entity_path(entity), body={entity: a["fields"]})


def t_update_record(a):
    entity = a["entity"]
    return api("PUT", f"{entity_path(entity)}/{a['id']}",
               body={entity: a["fields"]})


def t_add_note(a):
    return api("POST", "notes", body={"note": {
        "description": a["description"],
        "targetable_type": TARGETABLE_TYPES[a["entity"]],
        "targetable_id": a["id"],
    }})


def t_create_task(a):
    task = {
        "title": a["title"],
        "due_date": a["due_date"],
        "targetable_type": TARGETABLE_TYPES[a["entity"]],
        "targetable_id": a["id"],
    }
    for opt in ("description", "owner_id"):
        if a.get(opt) is not None:
            task[opt] = a[opt]
    return api("POST", "tasks", body={"task": task})


def t_list_tasks(a):
    return api("GET", "tasks", {
        "filter": a.get("filter", "open"),
        "include": "targetable,owner",
        "page": a.get("page", 1),
    })


def t_get_selector(a):
    return api("GET", f"selector/{a['name']}")


def t_get_fields(a):
    return api("GET", f"settings/{entity_path(a['entity'])}/fields")


def t_api_request(a):
    method = a.get("method", "GET").upper()
    if method != "GET" and read_only():
        raise FreshworksError("Server is in read-only mode; only GET is allowed.")
    return api(method, a["path"], a.get("params"), a.get("body"))


ENTITY_PROP = {
    "type": "string",
    "enum": sorted(ENTITY_PATHS),
    "description": "CRM entity: contact, sales_account (company) or deal.",
}

TOOLS = [
    {
        "name": "search",
        "description": "Full-text search across Freshworks CRM contacts, accounts and deals.",
        "write": False, "fn": t_search,
        "schema": {"type": "object", "required": ["query"], "properties": {
            "query": {"type": "string", "description": "Search text (name, email, phone, ...)."},
            "include": {"type": "string", "description": "Comma-separated: contact,sales_account,deal,user."},
            "per_page": {"type": "integer"},
        }},
    },
    {
        "name": "lookup",
        "description": "Exact lookup of records by a field value, e.g. a contact by email.",
        "write": False, "fn": t_lookup,
        "schema": {"type": "object", "required": ["value"], "properties": {
            "value": {"type": "string"},
            "field": {"type": "string", "description": "Field to match: email, name, mobile_number, or a custom field name. Default email."},
            "entities": {"type": "string", "description": "Comma-separated: contact,sales_account,deal."},
        }},
    },
    {
        "name": "list_views",
        "description": "List saved views (filters) for an entity. Use a view id with list_records.",
        "write": False, "fn": t_list_views,
        "schema": {"type": "object", "required": ["entity"], "properties": {"entity": ENTITY_PROP}},
    },
    {
        "name": "list_records",
        "description": "List contacts, accounts or deals in a saved view, paginated.",
        "write": False, "fn": t_list_records,
        "schema": {"type": "object", "required": ["entity", "view_id"], "properties": {
            "entity": ENTITY_PROP,
            "view_id": {"type": "integer"},
            "page": {"type": "integer"},
            "per_page": {"type": "integer"},
            "sort": {"type": "string", "description": "Field to sort by, e.g. updated_at."},
            "sort_type": {"type": "string", "enum": ["asc", "desc"]},
        }},
    },
    {
        "name": "get_record",
        "description": "Fetch one contact, account or deal by id.",
        "write": False, "fn": t_get_record,
        "schema": {"type": "object", "required": ["entity", "id"], "properties": {
            "entity": ENTITY_PROP,
            "id": {"type": "integer"},
            "include": {"type": "string", "description": "Related data, e.g. sales_accounts,deals,notes,tasks,owner."},
        }},
    },
    {
        "name": "get_fields",
        "description": "List the fields (including custom fields) configured for an entity.",
        "write": False, "fn": t_get_fields,
        "schema": {"type": "object", "required": ["entity"], "properties": {"entity": ENTITY_PROP}},
    },
    {
        "name": "get_selector",
        "description": "Get dropdown values such as owners, deal_stages, deal_pipelines, territories, lead_sources, contact_statuses, industry_types.",
        "write": False, "fn": t_get_selector,
        "schema": {"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}},
    },
    {
        "name": "list_tasks",
        "description": "List tasks: open, due_today, due_tomorrow, overdue or completed.",
        "write": False, "fn": t_list_tasks,
        "schema": {"type": "object", "properties": {
            "filter": {"type": "string", "enum": ["open", "due_today", "due_tomorrow", "overdue", "completed"]},
            "page": {"type": "integer"},
        }},
    },
    {
        "name": "create_record",
        "description": "Create a contact, account or deal. fields example for a contact: {\"first_name\": \"A\", \"last_name\": \"B\", \"email\": \"a@b.com\"}; a deal needs name and amount; an account needs name.",
        "write": True, "fn": t_create_record,
        "schema": {"type": "object", "required": ["entity", "fields"], "properties": {
            "entity": ENTITY_PROP,
            "fields": {"type": "object", "description": "Field values; custom fields go under custom_field."},
        }},
    },
    {
        "name": "update_record",
        "description": "Update fields on an existing contact, account or deal.",
        "write": True, "fn": t_update_record,
        "schema": {"type": "object", "required": ["entity", "id", "fields"], "properties": {
            "entity": ENTITY_PROP,
            "id": {"type": "integer"},
            "fields": {"type": "object"},
        }},
    },
    {
        "name": "add_note",
        "description": "Add a note to a contact, account or deal.",
        "write": True, "fn": t_add_note,
        "schema": {"type": "object", "required": ["entity", "id", "description"], "properties": {
            "entity": ENTITY_PROP,
            "id": {"type": "integer"},
            "description": {"type": "string"},
        }},
    },
    {
        "name": "create_task",
        "description": "Create a task linked to a contact, account or deal.",
        "write": True, "fn": t_create_task,
        "schema": {"type": "object", "required": ["entity", "id", "title", "due_date"], "properties": {
            "entity": ENTITY_PROP,
            "id": {"type": "integer"},
            "title": {"type": "string"},
            "due_date": {"type": "string", "description": "ISO 8601, e.g. 2026-10-15T10:00:00+05:30."},
            "description": {"type": "string"},
            "owner_id": {"type": "integer"},
        }},
    },
    {
        "name": "api_request",
        "description": "Call any Freshworks CRM API endpoint not covered by other tools. path is relative to the API base, e.g. 'appointments' or 'contacts/123/activities'.",
        "write": False, "fn": t_api_request,
        "schema": {"type": "object", "required": ["path"], "properties": {
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "path": {"type": "string"},
            "params": {"type": "object"},
            "body": {"type": "object"},
        }},
    },
]


def read_only():
    return os.environ.get("FRESHWORKS_READ_ONLY", "").strip().lower() in ("1", "true", "yes")


def available_tools():
    return [t for t in TOOLS if not (t["write"] and read_only())]


# ---------------------------------------------------------------------------
# JSON-RPC / MCP plumbing
# ---------------------------------------------------------------------------

def handle(msg):
    method = msg.get("method")
    params = msg.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": [
            {"name": t["name"], "description": t["description"], "inputSchema": t["schema"]}
            for t in available_tools()
        ]}
    if method == "tools/call":
        tool = next((t for t in available_tools() if t["name"] == params.get("name")), None)
        if tool is None:
            return tool_result(f"Unknown or disabled tool: {params.get('name')}", True)
        try:
            result = tool["fn"](params.get("arguments") or {})
            return tool_result(json.dumps(result, indent=2))
        except (FreshworksError, KeyError) as e:
            return tool_result(f"Error: {e}", True)
    raise LookupError(method)


def tool_result(text, is_error=False):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    load_env_file()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            send({"jsonrpc": "2.0", "id": None,
                  "error": {"code": -32700, "message": "Parse error"}})
            continue
        if "id" not in msg:  # notification
            continue
        try:
            send({"jsonrpc": "2.0", "id": msg["id"], "result": handle(msg)})
        except LookupError:
            send({"jsonrpc": "2.0", "id": msg["id"],
                  "error": {"code": -32601, "message": f"Method not found: {msg.get('method')}"}})
        except Exception as e:  # keep the server alive on unexpected errors
            send({"jsonrpc": "2.0", "id": msg["id"],
                  "error": {"code": -32603, "message": str(e)}})


if __name__ == "__main__":
    main()
