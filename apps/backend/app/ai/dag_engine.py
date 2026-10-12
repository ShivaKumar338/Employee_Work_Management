"""
DAG Workflow Engine
Critical path analysis, dependency resolution, bottleneck detection.
"""
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class DAGNode:
    id: str
    title: str
    estimated_hours: float
    dependencies: List[str]
    status: str = "todo"
    ai_risk_score: float = 0.0


class DAGEngine:
    """
    Directed Acyclic Graph execution engine for task workflow management.
    """

    def __init__(self, nodes: List[Dict]):
        self.nodes: Dict[str, DAGNode] = {}
        self.adj: Dict[str, List[str]] = defaultdict(list)  # task -> dependents
        self.rev_adj: Dict[str, List[str]] = defaultdict(list)  # task -> dependencies

        for node_data in nodes:
            node = DAGNode(
                id=node_data["id"],
                title=node_data.get("title", ""),
                estimated_hours=node_data.get("estimated_hours", 0),
                dependencies=node_data.get("dependencies", []),
                status=node_data.get("status", "todo"),
                ai_risk_score=node_data.get("ai_risk_score", 0),
            )
            self.nodes[node.id] = node
            for dep_id in node.dependencies:
                self.adj[dep_id].append(node.id)
                self.rev_adj[node.id].append(dep_id)

    def validate(self) -> Dict:
        """Validate the DAG for cycles and missing dependencies."""
        errors = []
        warnings = []

        # Check for missing dependency references
        for node_id, node in self.nodes.items():
            for dep_id in node.dependencies:
                if dep_id not in self.nodes:
                    errors.append(f"Task '{node.title}' depends on non-existent task ID: {dep_id}")

        # Cycle detection (DFS)
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for neighbor in self.adj.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    errors.append(f"Cycle detected involving task: {self.nodes[node_id].title}")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def topological_sort(self) -> List[str]:
        """Return tasks in execution order (Kahn's algorithm)."""
        in_degree = {node_id: len(deps) for node_id, node in self.nodes.items()
                     for deps in [node.dependencies]}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            for neighbor in self.adj.get(node_id, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def critical_path(self) -> Tuple[List[str], float]:
        """
        Find the critical path (longest path by estimated_hours).
        Returns (path_node_ids, total_hours).
        """
        order = self.topological_sort()
        earliest = {nid: 0.0 for nid in self.nodes}

        for node_id in order:
            node = self.nodes[node_id]
            for dep_id in node.dependencies:
                earliest[node_id] = max(
                    earliest[node_id],
                    earliest.get(dep_id, 0) + self.nodes[dep_id].estimated_hours
                )

        # Find the endpoint with max earliest finish
        end_node = max(self.nodes.keys(), key=lambda nid: earliest[nid] + self.nodes[nid].estimated_hours)
        total_hours = earliest[end_node] + self.nodes[end_node].estimated_hours

        # Backtrack to find critical path
        path = []
        current = end_node
        while current:
            path.append(current)
            node = self.nodes[current]
            # Find which dependency we came from
            prev = None
            max_time = -1
            for dep_id in node.dependencies:
                finish = earliest.get(dep_id, 0) + self.nodes[dep_id].estimated_hours
                if finish > max_time:
                    max_time = finish
                    prev = dep_id
            current = prev

        path.reverse()
        return path, total_hours

    def get_blocked_tasks(self) -> List[Dict]:
        """Identify tasks blocked by incomplete dependencies."""
        blocked = []
        for node_id, node in self.nodes.items():
            if node.status in ("todo", "in_progress"):
                blocking_deps = [
                    dep_id for dep_id in node.dependencies
                    if self.nodes.get(dep_id) and self.nodes[dep_id].status != "done"
                ]
                if blocking_deps:
                    blocked.append({
                        "task_id": node_id,
                        "task_title": node.title,
                        "blocked_by": [
                            {"id": d, "title": self.nodes[d].title} for d in blocking_deps
                        ]
                    })
        return blocked

    def bottleneck_prediction(self) -> List[Dict]:
        """Find tasks that are dependencies for many others (high fan-out = bottlenecks)."""
        fan_out = {nid: len(self.adj.get(nid, [])) for nid in self.nodes}
        bottlenecks = [
            {
                "task_id": nid,
                "task_title": self.nodes[nid].title,
                "dependent_count": count,
                "status": self.nodes[nid].status,
                "risk_level": "high" if count >= 3 else "medium",
            }
            for nid, count in fan_out.items()
            if count >= 2
        ]
        return sorted(bottlenecks, key=lambda x: x["dependent_count"], reverse=True)

    def get_ready_tasks(self) -> List[str]:
        """Return task IDs that can start immediately (all deps complete)."""
        ready = []
        for node_id, node in self.nodes.items():
            if node.status == "todo":
                all_deps_done = all(
                    self.nodes.get(dep_id) and self.nodes[dep_id].status == "done"
                    for dep_id in node.dependencies
                )
                if all_deps_done:
                    ready.append(node_id)
        return ready

    def analyze(self) -> Dict:
        """Full DAG analysis report."""
        validation = self.validate()
        if not validation["valid"]:
            return {"error": "Invalid DAG", "details": validation}

        critical_path_ids, critical_hours = self.critical_path()
        blocked = self.get_blocked_tasks()
        bottlenecks = self.bottleneck_prediction()
        ready = self.get_ready_tasks()

        # Mark critical path nodes
        for node_id in critical_path_ids:
            if node_id in self.nodes:
                self.nodes[node_id].ai_risk_score = max(self.nodes[node_id].ai_risk_score, 60)

        return {
            "validation": validation,
            "critical_path": {
                "task_ids": critical_path_ids,
                "task_titles": [self.nodes[nid].title for nid in critical_path_ids if nid in self.nodes],
                "total_hours": critical_hours,
                "total_days": critical_hours / 8,
            },
            "blocked_tasks": blocked,
            "bottlenecks": bottlenecks,
            "ready_to_start": ready,
            "completion_stats": {
                "total": len(self.nodes),
                "done": sum(1 for n in self.nodes.values() if n.status == "done"),
                "in_progress": sum(1 for n in self.nodes.values() if n.status == "in_progress"),
                "blocked": len(blocked),
                "todo": sum(1 for n in self.nodes.values() if n.status == "todo"),
            },
        }
