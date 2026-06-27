from typing import List, Dict, Any

def calculate_exposure(paths: List[Dict[str, Any]], depth_decay_factor: float = 0.8) -> List[Dict[str, Any]]:
    """
    Calculate exposure score for a list of reasoning paths.
    Exposure Score = ∏(edge_weight × edge_confidence) × (depth_decay_factor ^ (path_length - 1))
    """
    scored_paths = []
    
    for path in paths:
        edges = path["edges"]
        if not edges:
            continue
            
        path_score = 1.0
        path_confidence = 1.0
        
        for edge in edges:
            weight = edge.get("weight", 1.0)
            confidence = edge.get("confidence", 1.0)
            path_score *= weight
            path_confidence *= confidence
            
        # Apply depth decay
        path_length = path["path_length"]
        decay = depth_decay_factor ** (path_length - 1)
        
        final_exposure = path_score * decay
        
        scored_paths.append({
            "stock_or_company_id": path["stock_or_company_id"],
            "stock_symbol": path.get("stock_symbol"),
            "nodes": path["nodes"],
            "edges": edges,
            "path_length": path_length,
            "exposure_score": round(final_exposure, 4),
            "confidence": round(path_confidence, 4)
        })
        
    # If there are multiple paths to the same stock, we might want to aggregate them (e.g., take the max or sum).
    # For MVP, let's group by stock_or_company_id and take the max exposure path.
    aggregated = {}
    for sp in scored_paths:
        cid = sp["stock_or_company_id"]
        if cid not in aggregated:
            aggregated[cid] = sp
        else:
            if sp["exposure_score"] > aggregated[cid]["exposure_score"]:
                aggregated[cid] = sp
                
    return list(aggregated.values())
