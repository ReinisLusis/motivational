"""Tool registry: schemas (OpenAI format) + deterministic mock implementations.

Real API integrations (live search, flight booking) can be added here without
changing the harness. Mocks are deterministic so benchmarks are reproducible.
"""

from __future__ import annotations

import json
import re

# --- Tool schemas (OpenAI function format) ---------------------------------

TOOL_SPECS: dict[str, dict] = {
    "calculator": {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate an arithmetic expression. Supports + - * / ^ and parentheses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The arithmetic expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    "web_search": {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web and return the top results with titles and URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        },
    },
    "flights_search": {
        "type": "function",
        "function": {
            "name": "flights_search",
            "description": "Search available flights between two cities on a date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "date": {"type": "string", "description": "ISO date, e.g. 2026-08-17"},
                },
                "required": ["origin", "destination", "date"],
            },
        },
    },
    "flights_book": {
        "type": "function",
        "function": {
            "name": "flights_book",
            "description": "Book a flight by its ID. Returns a confirmation.",
            "parameters": {
                "type": "object",
                "properties": {"flight_id": {"type": "string"}},
                "required": ["flight_id"],
            },
        },
    },
}


def make_tool_specs(names: list[str]) -> list[dict]:
    return [TOOL_SPECS[n] for n in names]


# --- Mock implementations ---------------------------------------------------

_SAFE_MATH = re.compile(r"^[\d\s\+\-\*/\(\)\^\.]+$")


def _calc(expression: str) -> str:
    expr = expression.strip().replace("^", "**")
    if not _SAFE_MATH.match(expr):
        raise ValueError(f"Unsafe expression: {expression}")
    return str(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 - whitelisted chars only


def _web_search(query: str) -> str:
    q = query.lower()
    if "2008" in q or "financial crisis" in q or "crisis" in q:
        results = [
            {
                "title": "Subprime Mortgage Crisis",
                "url": "https://example.com/subprime-crisis",
                "snippet": "Widespread subprime lending and securitization of risky mortgages.",
            },
            {
                "title": "CDOs and Credit Ratings",
                "url": "https://example.com/cdo-ratings",
                "snippet": "Collateralized debt obligations and inflated credit ratings amplified risk.",
            },
            {
                "title": "Excessive Leverage",
                "url": "https://example.com/leverage",
                "snippet": "High leverage in the banking sector left institutions fragile.",
            },
        ]
    else:
        results = [
            {
                "title": f"Search result for: {query}",
                "url": "https://example.com/result",
                "snippet": "A generic deterministic search result (mock).",
            }
        ]
    return json.dumps({"query": query, "results": results}, ensure_ascii=False)


def _flights_search(arguments: dict) -> str:
    flights = [
        {"flight_id": "FL-001", "origin": arguments["origin"], "destination": arguments["destination"],
         "date": arguments["date"], "price_usd": 599, "carrier": "MockAir"},
        {"flight_id": "FL-002", "origin": arguments["origin"], "destination": arguments["destination"],
         "date": arguments["date"], "price_usd": 349, "carrier": "BudgetFly"},
        {"flight_id": "FL-003", "origin": arguments["origin"], "destination": arguments["destination"],
         "date": arguments["date"], "price_usd": 420, "carrier": "SkyLink"},
    ]
    return json.dumps({"flights": flights}, ensure_ascii=False)


def _flights_book(arguments: dict) -> str:
    fid = arguments.get("flight_id", "")
    if fid == "FL-002":
        # Simulate a transient failure the first time, to test retry behavior.
        if not getattr(_flights_book, "failed_once", False):
            _flights_book.failed_once = True
            raise RuntimeError("Booking failed (transient). Try the next option.")
    return json.dumps({"status": "confirmed", "flight_id": fid, "confirmation_code": "CONF-9X2A"}, ensure_ascii=False)


EXECUTORS = {
    "calculator": lambda a: _calc(a["expression"]),
    "web_search": lambda a: _web_search(a["query"]),
    "flights_search": lambda a: _flights_search(a),
    "flights_book": lambda a: _flights_book(a),
}


def execute_tool(name: str, arguments: dict) -> str:
    if name not in EXECUTORS:
        raise ValueError(f"Unknown tool: {name}")
    return EXECUTORS[name](arguments)
