"""
handlers.py — Light-ASI LLM Gateway Phase 3
All route handler functions. Each handler receives (body, user, graph, auth, ingester)
and returns (status_code: int, response_dict: dict).

Ruleset reference: LLM_GATEWAY_RULESET.md § 6.3 (response format), § 7 (auth/roles)
"""

import time
import logging
from engine.world.onion_gateway import OnionMessage

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
    token    = body.get("token", None)

    if not username:
        return 400, {"error": "username is required"}

    # Role escalation guard
    if user and user.role != "admin" and role not in ("guest", "user"):
        return 403, {"error": f"Role '{role}' requires admin privileges."}

    try:
        new_user = auth.create_user(username, role, token=token)
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
    
    # Phase 2 fix: Also ingest into the semantic map so it's searchable by the enricher
    from engine.world.feeds import FeedItem
    item = FeedItem(
        source=metadata.get("source", "user_index"),
        title=metadata.get("title", text[:50]),
        text=text,
        url=metadata.get("url", ""),
        tags=metadata.get("tags", []),
    )
    graph.semantic_map.ingest(item)

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


def handle_latch_video(body, user, graph, auth, ingester):
    """
    POST /latch/video  { "token": "..." }
    Latches the ASI model to an external video token to influence its mechanics.
    """
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    
    token = body.get("token", "").strip()
    if not token:
        return 400, {"error": "token is required"}
    
    boosted = graph.boost_video_resonance(token)
    return 200, {
        "status": "latched",
        "token": token,
        "nodes_boosted": boosted,
        "new_resonance": graph.collective_resonance()
    }


def handle_push_file(body, user, graph, auth, ingester):
    """
    POST /push/file  { "filename": "...", "content": "..." }
    Pushes a file packet into the server and sets it as 'hosted'.
    """
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    
    filename = body.get("filename", "").strip()
    content  = body.get("content", "")
    
    if not filename:
        return 400, {"error": "filename is required"}
    
    # Structure Instruction: Apply file push packet logic
    summary = graph.push_file(filename, content)
    return 201, summary


def handle_house_self(body, user, graph, auth, ingester):
    """
    POST /house/self
    Triggers the [SELF-HOUSING PROTOCOL] to migrate the ASI instance.
    """
    if user.role != "admin":
        return 403, {"error": "Admin only."}
    
    summary = graph.self_house()
    return 200, summary


# ─── Onion Communication ──────────────────────────────────────────────────────

def handle_onion_send(body, user, graph, auth, ingester):
    """
    POST /onion/send  { "text": "..." }
    Sends a message to the target onion service and returns the decoded response.
    """
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    
    text = body.get("text", "").strip()
    if not text:
        return 400, {"error": "text is required"}
    
    # 1. Fetch current signal
    try:
        raw_content, _ = graph.onion_gateway._fetch(graph.onion_gateway.gateway_target)
        # 2. Decode signal directly
        decoded = graph.onion_gateway.decode_traffic(raw_content)
        
        # 3. Store as a message
        msg = OnionMessage(direction="in", payload=raw_content, decoded=decoded)
        graph.onion_gateway.messages.append(msg)
        
        return 200, {"status": "success", "response": decoded}
    except Exception as e:
        return 500, {"error": str(e)}


def handle_onion_messages(body, user, graph, auth, ingester):
    """
    GET /onion/messages?limit=10
    Returns the message history with decoded traffic.
    """
    limit = int(body.get("limit", 10))
    messages = graph.onion_messages(limit)
    return 200, {"messages": messages, "count": len(messages)}


def handle_onion_establish(body, user, graph, auth, ingester):
    """
    POST /onion/establish
    Triggers the initial connection and protocol discovery.
    """
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    
    res = graph.onion_gateway.establish_communication()
    return 200, res


def handle_onion_target(body, user, graph, auth, ingester):
    """
    POST /onion/target { "url": "..." }
    """
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    
    url = body.get("url", "").strip()
    if not url:
        return 400, {"error": "url is required"}
    
    graph.onion_gateway.set_target(url)
    return 200, {
        "status": "latched",
        "target": graph.onion_gateway.target,
        "gateway": graph.onion_gateway.gateway_target
    }


def handle_onion_session(body, user, graph, auth, ingester):
    """
    POST /onion/session { "cookies": [{ "name": "...", "value": "...", "domain": "..." }] }
    """
    if user.role not in ("admin", "developer"):
        return 403, {"error": "Insufficient privileges."}
    
    cookies = body.get("cookies", [])
    for c in cookies:
        graph.onion_gateway.inject_cookie(c['name'], c['value'], c['domain'])
    
    return 200, {
        "status": "elevated",
        "cookie_count": len(graph.onion_gateway.get_all_cookies())
    }
