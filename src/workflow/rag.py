"""Agentic RAG manager - supports global and per-user document stores.

Uses MemoryStore from src.workflow.memory to store docs and perform retrieval.
This file provides RAGManager which merges global and user-specific retrievals
and builds a combined context snippet for LLM prompts.
"""

from typing import List, Dict, Optional, Any, Callable
import os
import importlib.util
import pathlib


def _load_memorystore_class() -> type:
    """Dynamically load MemoryStore class from src/workflow/memory.py by path.

    This avoids import path issues when running as a script or as a package.
    """
    base = pathlib.Path(__file__).resolve().parent
    candidate = base.parent / 'workflow' / 'memory.py'
    if not candidate.exists():
        # Try alternate location if repository layout differs
        candidate = base.parent.parent / 'src' / 'workflow' / 'memory.py'
    if not candidate.exists():
        raise ImportError(f"Memory module not found at expected locations: {candidate}")
    spec = importlib.util.spec_from_file_location('memory_module', str(candidate))
    mod = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError('Could not load memory module loader')
    loader.exec_module(mod)
    if not hasattr(mod, 'MemoryStore'):
        raise ImportError('MemoryStore not found in memory module')
    return getattr(mod, 'MemoryStore')


MemoryStore = _load_memorystore_class()


class RAGManager:
    def __init__(self, embedding_fn: Optional[Callable[[str], List[float]]] = None, embedding_dim: Optional[int] = None):
        # Global store holds documents for all users
        self.global_store = MemoryStore(embedding_fn=embedding_fn, embedding_dim=embedding_dim)
        # Per-user stores
        self.user_stores = {}  # type: Dict[str, Any]

    def _get_user_store(self, user_id: str) -> Any:
        if user_id not in self.user_stores:
            self.user_stores[user_id] = MemoryStore(embedding_fn=self.global_store.embedding_fn, embedding_dim=self.global_store.embedding_dim)
        return self.user_stores[user_id]

    def add_global_document(self, doc_id: str, text: str, timestamp: Optional[float] = None):
        # store under a special convo id 'global'
        self.global_store.add_conversation_turn('global', 'system', f"{doc_id}: {text}", timestamp=timestamp)

    def add_user_document(self, user_id: str, doc_id: str, text: str, timestamp: Optional[float] = None):
        store = self._get_user_store(user_id)
        store.add_conversation_turn(f'user:{user_id}', 'system', f"{doc_id}: {text}", timestamp=timestamp)

    def retrieve(self, query: str, user_id: Optional[str] = None, top_k_global: int = 3, top_k_user: int = 3) -> List[Dict]:
        """Retrieve merged results from global and user stores, sorted by score.

        Returns a list of dicts with fields: id, owner, text, score, timestamp, source
        where source is 'global' or 'user'.
        """
        results = []
        ghits = self.global_store.query_memory(query, owner='global', top_k=top_k_global)
        for r in ghits:
            r['source'] = 'global'
            results.append(r)

        if user_id:
            store = self._get_user_store(user_id)
            uhits = store.query_memory(query, owner=f'user:{user_id}', top_k=top_k_user)
            for r in uhits:
                r['source'] = 'user'
                results.append(r)

        # de-duplicate by text, prefer user over global if same text
        seen_texts = set()
        merged = []
        for r in sorted(results, key=lambda x: x['score'], reverse=True):
            t = r['text']
            if t in seen_texts:
                continue
            seen_texts.add(t)
            merged.append(r)

        return merged

    def build_rag_context(self, query: str, user_id: Optional[str] = None, k_global: int = 3, k_user: int = 3) -> str:
        hits = self.retrieve(query, user_id=user_id, top_k_global=k_global, top_k_user=k_user)
        if not hits:
            return ""
        parts = []
        for h in hits:
            parts.append(f"[{h['source'].upper()}] {h['text']}")
        header = "Relevant documents (RAG):\n"
        return header + "\n".join(parts)


if __name__ == '__main__':
    print('RAGManager demo')
    mgr = RAGManager()
    mgr.add_global_document('doc1', 'This is a global guide about Python programming.')
    mgr.add_global_document('doc2', 'Deployment steps for Azure resources.')

    mgr.add_user_document('alice', 'alice_note1', 'Alice likes chess and tea.')
    mgr.add_user_document('alice', 'alice_note2', 'Alice works at Contoso.')

    q = 'Tell me about Alice\'s interests and relevant deployment steps.'
    ctx = mgr.build_rag_context(q, user_id='alice')
    print(ctx)
