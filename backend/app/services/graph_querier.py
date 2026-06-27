from collections import deque
from datetime import datetime
from typing import List, Dict, Any, Optional

def query_impacted_stocks(db_module, start_entity_id: str, context_date: Optional[datetime] = None, max_depth: int = 4) -> List[Dict[str, Any]]:
    """
    Search the knowledge graph for paths from start_entity_id to Stock/Company entities.
    Uses BFS to traverse up to max_depth.
    Returns a list of reasoning paths.
    """
    if not context_date:
        context_date = datetime.now()

    # Pre-fetch all active entities and relations to memory for faster BFS?
    # Or query step by step? Query step by step is safer if graph is huge, but fetching all might be fine for MVP.
    # Let's query step by step using a single query to get all active edges first, as the graph is likely small in MVP.
    
    # Get all valid relations
    relations_query = """
        SELECT relation_id, source_entity_id, target_entity_id, relation_type, weight, confidence
        FROM kg_relations
        WHERE status IN ('active', 'validated')
          AND (valid_from IS NULL OR valid_from <= ?)
          AND (valid_to IS NULL OR valid_to >= ?)
    """
    
    edges = db_module.rows(relations_query, (context_date, context_date))
    
    # Build adjacency list
    adj = {}
    edge_details = {}
    for edge in edges:
        src = edge["source_entity_id"]
        tgt = edge["target_entity_id"]
        if src not in adj:
            adj[src] = []
        if tgt not in adj: # Graph could be undirected conceptually, but we have directed edges. E.g. downstream/upstream.
            adj[tgt] = []
            
        # For impact reasoning, we might want to traverse both ways depending on relation type,
        # but usually it's "source -> target" or "target -> source". Let's assume we can traverse undirected for now
        # or directed? The schema says "direction: directed".
        # If a commodity is used by a company, the edge might be Company -> uses -> Commodity, so we must traverse backward!
        adj[src].append({"to": tgt, "edge": dict(edge), "dir": "forward"})
        adj[tgt].append({"to": src, "edge": dict(edge), "dir": "backward"})
        
        edge_details[edge["relation_id"]] = dict(edge)

    # Pre-fetch entities
    entities_query = "SELECT entity_id, entity_type, name, metadata_json FROM kg_entities WHERE status='active'"
    entities_raw = db_module.rows(entities_query)
    entity_map = {}
    for e in entities_raw:
        ed = dict(e)
        if isinstance(ed.get("metadata_json"), str):
            import json
            ed["metadata_json"] = json.loads(ed["metadata_json"])
        entity_map[e["entity_id"]] = ed
        
    if start_entity_id not in entity_map:
        return []
        
    found_paths = []
    
    # BFS
    # Queue stores: (current_entity_id, path_nodes, path_edges)
    from collections import deque
    queue = deque([(start_entity_id, [start_entity_id], [])])
    visited_paths = set()
    found_paths = []

    while queue:
        curr, path_nodes, path_edges = queue.popleft()
        
        curr_entity = entity_map.get(curr)
        if not curr_entity:
            continue
            
        # If we reached a Stock or Company (and it's not the start node)
        if curr_entity["entity_type"] in ["Stock", "Company"] and len(path_nodes) > 1:
            stock_symbol = curr_entity.get("metadata_json", {}).get("stock_code", curr)
            found_paths.append({
                "stock_or_company_id": curr,
                "stock_symbol": stock_symbol,
                "nodes": [entity_map[n] for n in path_nodes],
                "edges": path_edges,
                "path_length": len(path_edges)
            })
            # We don't stop, we can continue to find other stocks, but maybe we shouldn't traverse *through* a stock to another stock.
            continue
            
        if len(path_edges) >= max_depth:
            continue
            
        # Traverse neighbors
        if curr in adj:
            for neighbor in adj[curr]:
                nxt = neighbor["to"]
                edge = neighbor["edge"]
                
                # Prevent cycles in the current path
                if nxt in path_nodes:
                    continue
                    
                queue.append((
                    nxt,
                    path_nodes + [nxt],
                    path_edges + [edge]
                ))

    return found_paths
