"""
handlers.py — Light-ASI LLM Gateway Phase 3
All route handler functions. Each handler receives (body, user, graph, auth, ingester)
and returns (status_code: int, response_dict: dict).

Ruleset reference: LLM_GATEWAY_RULESET.md § 6.3 (response format), § 7 (auth/roles)
"""

import time
import logging

logger = logging.getLogger("light-asi.api.handlers")


# ─── Health ───────────────────────────────────────────────────────────────────

def handle_health(body, user, graph, auth, ingester):
    return 200, {
        "status": "ok",
        "nodes": len(graph._nodes),
        "semantic_map": graph.semantic_map.size,
        "ingester_running": ingester.is_running() if ingester else False,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ─── Auth ─────────────────────────────────────────────────────────────────────

def handle_create_token(body, user, graph, auth, ingester):
    """
    POST /auth/token  { "username": "...", "role": "..." }
    Creates a new user and returns their Bearer token.
    Only admin can create non-guest users.
    """
    username = body.get("username", "").strip()
    role     = body.get("role", "guest").strip()

    if not username:
        return 400, {"error": "username is required"}

    # Role escalation guard
    if user and user.role != "admin" and role not in ("guest", "user"):
        return 403, {"error": f"Role '{role}' requires admin privileges."}

    try:
        new_user = auth.create_user(username, role)
    except ValueError as e:
        return 409, {"error": str(e)}

    return 201, {
        "username": new_user.username,
        "role":     new_user.role,
        "token":    new_user.token,
        "expires_in": "24h (sliding)",
    }


def handle_list_users(body, user, graph, auth, ingester):
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    return 200, {"users": auth.list_users()}


# ─── Query ────────────────────────────────────────────────────────────────────

def handle_query(body, user, graph, auth, ingester):
    """
    POST /query  { "text": "...", "top_k": 3 }
    Full ruleset § 6.3 response format.
    """
    text  = body.get("text", "").strip()
    top_k = int(body.get("top_k", 3))

    if not text:
        return 400, {"error": "text is required"}

    # Enforce max query depth per role
    from engine.core.constants import ROLE_MAX_QUERY_DEPTH
    max_depth = ROLE_MAX_QUERY_DEPTH.get(user.role)
    if max_depth is not None:
        top_k = min(top_k, max_depth, len(graph._nodes))

    if not graph._nodes:
        return 503, {"error": "Graph not bootstrapped yet."}

    result = graph.query(text, top_k=max(1, top_k))
    result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return 200, result


# ─── Index ────────────────────────────────────────────────────────────────────

def handle_index(body, user, graph, auth, ingester):
    """
    POST /index  { "text": "...", "metadata": {} }
    """
    if user.role not in ("admin", "developer", "user"):
        return 403, {"error": "Insufficient privileges."}

    text     = body.get("text", "").strip()
    metadata = body.get("metadata", {})

    if not text:
        return 400, {"error": "text is required"}

    metadata["indexed_by"] = user.username
    hashes = graph.index_text(text, metadata=metadata)
    return 200, {
        "indexed_tokens": len(hashes),
        "semantic_map_size": graph.semantic_map.size,
    }


# ─── Stats ────────────────────────────────────────────────────────────────────

def handle_stats(body, user, graph, auth, ingester):
    s = graph.stats()
    s["users"] = len(auth.list_users())
    return 200, s


def handle_emerge(body, user, graph, auth, ingester):
    return 200, graph.emergence_status()


def handle_resonance(body, user, graph, auth, ingester):
    return 200, graph.resonance_tracker.report()


def handle_world(body, user, graph, auth, ingester):
    return 200, graph.world_status()


# ─── Ingestion ────────────────────────────────────────────────────────────────

def handle_ingest(body, user, graph, auth, ingester):
    """
    POST /ingest  — trigger one world-net ingestion cycle immediately.
    Admin/developer only.
    """
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    if not ingester:
        return 503, {"error": "WorldIngester not attached."}
    summary = ingester.run_once()
    return 200, summary


def handle_search(body, user, graph, auth, ingester):
    """
    POST /search  { "text": "...", "top_k": 5 }
    Search the semantic map directly.
    """
    text  = body.get("text", "").strip()
    top_k = int(body.get("top_k", 5))
    if not text:
        return 400, {"error": "text is required"}
    results = graph.semantic_map.search(text, top_k=top_k)
    return 200, {
        "query": text,
        "results": [
            {
                "source":    e.source,
                "title":     e.title,
                "snippet":   e.text[:200],
                "url":       e.url,
                "tags":      e.tags,
                "hash":      e.meaning_hash[:16] + "…",
            }
            for e in results
        ],
        "count": len(results),
        "semantic_map_size": graph.semantic_map.size,
    }


# ─── Backup ───────────────────────────────────────────────────────────────────

def handle_backup(body, user, graph, auth, ingester):
    if user.role != "admin":
        return 403, {"error": "Admin only."}
    summary = graph.backup()
    return 200, summary
