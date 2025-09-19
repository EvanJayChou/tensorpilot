"""ReAct-style planner for math problems.

This planner decomposes math problems into step-by-step plans, consults the
RAG system for formulas/proofs, uses MemoryStore for conversation/user memory,
and calls MCP tools (symbolic/numeric) to verify or compute intermediate steps.
"""

from typing import List, Dict, Optional, Any
import importlib.util
import pathlib
import json
import time


def _load_module_from_repo(path_parts: List[str], attr: Optional[str] = None):
    base = pathlib.Path(__file__).resolve().parent
    candidate = base
    for p in path_parts:
        candidate = candidate / p
    if not candidate.exists():
        # try from repo root src/
        candidate = base.parent.parent / 'src'
        for p in path_parts:
            candidate = candidate / p
    if not candidate.exists():
        raise ImportError(f"Module not found: {'/'.join(path_parts)}")
    spec = importlib.util.spec_from_file_location('_mod', str(candidate))
    mod = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError('Could not load module loader')
    loader.exec_module(mod)
    if attr:
        return getattr(mod, attr)
    return mod


# Load RAGManager dynamically
RAGManager = _load_module_from_repo(['workflow', 'rag.py'], 'RAGManager')
# Load MemoryStore from memory module
MemoryStore = _load_module_from_repo(['workflow', 'memory.py'], 'MemoryStore')
# Load MCP tools module
MCP = _load_module_from_repo(['llm', 'mcp.py'])


class ReActPlanner:
    def __init__(self, embedding_fn: Optional[Any] = None, embedding_dim: Optional[int] = None):
        self.rag = RAGManager(embedding_fn=embedding_fn, embedding_dim=embedding_dim)
        self.memory = MemoryStore(embedding_fn=embedding_fn, embedding_dim=embedding_dim)

    def add_domain_doc(self, doc_id: str, text: str):
        self.rag.add_global_document(doc_id, text)

    def add_user_note(self, user_id: str, doc_id: str, text: str):
        self.rag.add_user_document(user_id, doc_id, text)

    def plan(self, problem: str, user_id: Optional[str] = None, verify: bool = True) -> Dict:
        """Produce a ReAct plan for solving `problem`.

        Steps:
        1. Retrieve relevant formulas and proofs from global/user RAG.
        2. Propose decomposition into subtasks.
        3. Optionally call MCP tools to compute/verify steps.
        4. Return structured plan with optional computed results.
        """
        start = time.time()
        rag_ctx = self.rag.build_rag_context(problem, user_id=user_id)

        # Very small heuristic decomposition: split into bullets by sentences and math tokens
        decomposition = self._decompose_problem(problem, rag_ctx)

        # Attempt to verify or compute using MCP tools
        results = []
        for step in decomposition:
            res = {"step": step, "verification": None}
            if verify:
                # try symbolic evaluation first
                try:
                    sym_result = MCP.sympy_eval(step)
                    res["verification"] = {"tool": "sympy", "result": sym_result}
                except Exception as e:
                    res["verification"] = {"tool": "sympy", "error": str(e)}
            results.append(res)

        out = {
            "problem": problem,
            "rag_context": rag_ctx,
            "plan": results,
            "duration": time.time() - start,
        }
        return out

    def _decompose_problem(self, problem: str, rag_ctx: str) -> List[str]:
        # naive decomposition: split sentences, keep math expressions together
        # Attempt to find math expressions between $...$ or numbers/operators
        import re
        sentences = re.split(r"(?<=[\.\?\!])\s+", problem)
        steps = []
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            # if contains equation-like patterns, treat as single step
            if re.search(r"[0-9=+\-*/^()]+", s):
                steps.append(s)
            else:
                # break longer sentences into smaller tasks by commas
                if ',' in s:
                    parts = [p.strip() for p in s.split(',') if p.strip()]
                    steps.extend(parts)
                else:
                    steps.append(s)
        # prepend RAG hints as the first step if available
        if rag_ctx:
            steps.insert(0, "Consult relevant formulas and proofs: " + (rag_ctx.replace('\n', ' | ')))
        return steps


if __name__ == '__main__':
    print('ReActPlanner demo')
    planner = ReActPlanner()
    # add some domain docs (e.g., formula sheet)
    planner.add_domain_doc('pythag', 'Pythagorean theorem: a^2 + b^2 = c^2')
    planner.add_domain_doc('area', 'Area of a circle: A = pi * r^2')

    problem = 'Find the hypotenuse of a right triangle with legs 3 and 4.'
    plan = planner.plan(problem, user_id='alice')
    print(json.dumps(plan, indent=2))
