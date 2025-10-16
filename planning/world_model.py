from typing import Any, Dict
from tools.code_graph import CodeGraph


def build_world_model(graph: CodeGraph) -> Dict[str, Any]:
    # Minimal pass-through for now
    return {"graph_root": graph.root}
