
"""Simple memory module for LLM agents.

Provides an in-memory MemoryStore that stores conversation turns and user
profiles, optional embeddings (via Azure OpenAI) and simple similarity
retrieval for memory-based prompts.

This is intentionally lightweight and dependency-free by default. If you
want vector similarity using OpenAI embeddings, pass an embedding function
when constructing MemoryStore.
"""

from typing import List, Dict, Optional, Callable, Tuple
import time
import math
import os


def _cosine_similarity(a: List[float], b: List[float]) -> float:
	if not a or not b or len(a) != len(b):
		return 0.0
	dot = sum(x * y for x, y in zip(a, b))
	na = math.sqrt(sum(x * x for x in a))
	nb = math.sqrt(sum(y * y for y in b))
	if na == 0 or nb == 0:
		return 0.0
	return dot / (na * nb)


class MemoryStore:
	"""In-memory store for conversation history and user profiles.

	Args:
		embedding_fn: optional callable(text: str) -> List[float] to compute embeddings.
		embedding_dim: optional embedding dimension (for validation).
	"""

	def __init__(self, embedding_fn: Optional[Callable[[str], List[float]]] = None, embedding_dim: Optional[int] = None):
		self.embedding_fn = embedding_fn
		self.embedding_dim = embedding_dim
		self.conversations: Dict[str, List[Dict]] = {}
		self.profiles: Dict[str, Dict] = {}
		# vector index: list of (id, owner, text, embedding, timestamp)
		self.vectors: List[Tuple[str, str, str, Optional[List[float]], float]] = []

	# Conversation operations
	def add_conversation_turn(self, convo_id: str, role: str, text: str, timestamp: Optional[float] = None):
		"""Add a message turn to a conversation and index it for retrieval.

		role: 'user'|'assistant'|'system'
		"""
		if timestamp is None:
			timestamp = time.time()
		turn = {"role": role, "text": text, "timestamp": timestamp}
		self.conversations.setdefault(convo_id, []).append(turn)

		emb = None
		if self.embedding_fn:
			try:
				emb = self.embedding_fn(text)
				if self.embedding_dim and len(emb) != self.embedding_dim:
					# don't store invalid dims
					emb = None
			except Exception:
				emb = None

		self.vectors.append((f"turn:{convo_id}:{len(self.conversations[convo_id])-1}", convo_id, text, emb, timestamp))

	def get_conversation(self, convo_id: str, limit: Optional[int] = None) -> List[Dict]:
		msgs = self.conversations.get(convo_id, [])
		return msgs[-limit:] if limit else msgs[:]

	# Profile operations
	def add_user_profile(self, user_id: str, profile: Dict):
		"""Store or update a user profile dictionary."""
		self.profiles[user_id] = {**self.profiles.get(user_id, {}), **profile}

	def get_user_profile(self, user_id: str) -> Dict:
		return self.profiles.get(user_id, {})

	# Retrieval
	def query_memory(self, query: str, owner: Optional[str] = None, top_k: int = 5) -> List[Dict]:
		"""Return top_k memory items relevant to the query.

		If embeddings are available, use cosine similarity. Otherwise fall back
		to simple substring scoring across stored texts.
		"""
		results = []
		query_emb = None
		if self.embedding_fn:
			try:
				query_emb = self.embedding_fn(query)
			except Exception:
				query_emb = None

		for vid, owner_id, text, emb, ts in self.vectors:
			if owner and owner != owner_id:
				continue
			score = 0.0
			if query_emb and emb:
				score = _cosine_similarity(query_emb, emb)
			else:
				# crude substring / token overlap heuristic
				q = query.lower()
				t = text.lower()
				score = 1.0 if q in t else 0.0
				# small boost for partial word overlaps
				if score == 0.0:
					common = sum(1 for w in set(q.split()) if w in t)
					score = common / max(1, len(q.split())) * 0.1

			if score > 0:
				results.append({"id": vid, "owner": owner_id, "text": text, "score": score, "timestamp": ts})

		results.sort(key=lambda r: r["score"], reverse=True)
		return results[:top_k]

	def build_memory_prompt(self, convo_id: str, query: str, k: int = 5) -> str:
		"""Build a short prompt snippet of relevant memories to include in an LLM prompt.

		Returns a string that can be prefixed to the LLM input.
		"""
		items = self.query_memory(query, owner=convo_id, top_k=k)
		parts = []
		for it in items:
			t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(it["timestamp"]))
			parts.append(f"[{t}] {it['text']}")
		if not parts:
			return ""
		header = "Relevant past conversation snippets:\n"
		return header + "\n".join(parts)


### Optional: simple Azure OpenAI embeddings helper
try:
	from openai import OpenAI

	def make_azure_embedding_fn(api_key: Optional[str] = None, endpoint: Optional[str] = None, deployment: Optional[str] = None, api_version: str = "2023-07-01-preview") -> Callable[[str], List[float]]:
		"""Return a callable that computes embeddings via Azure OpenAI (using openai package).

		Usage:
			emb_fn = make_azure_embedding_fn(api_key, endpoint, deployment)
			store = MemoryStore(embedding_fn=emb_fn)
		"""
		# configure OpenAI
		if api_key:
			os.environ.setdefault("OPENAI_API_KEY", api_key)
		if endpoint:
			os.environ.setdefault("OPENAI_API_BASE", endpoint)
		def emb(text: str) -> List[float]:
			# This implementation expects the OpenAI python package to be configured for Azure.
			from openai import Embedding
			# If the package does not support Azure directly, users can implement their own wrapper.
			resp = Embedding.create(input=text, engine=deployment)
			return resp["data"][0]["embedding"]

		return emb
except Exception:
	# openai not available; skip helper
	def make_azure_embedding_fn(*a, **k):
		raise RuntimeError("openai package not available in this environment")


if __name__ == "__main__":
	# Simple self-test / demonstration
	print("Running memory module demo...")
	store = MemoryStore()
	cid = "session1"
	store.add_conversation_turn(cid, "user", "Hi, my name is Alice and I like chess.")
	store.add_conversation_turn(cid, "assistant", "Nice to meet you, Alice. I can help with chess puzzles.")
	store.add_conversation_turn(cid, "user", "Remind me later about the chess tournament.")

	store.add_user_profile("alice", {"name": "Alice", "likes": ["chess", "tea"]})

	q = "What does the user like?"
	print("Querying memory for:", q)
	hits = store.query_memory(q, owner=cid, top_k=5)
	print("Hits:", hits)
	prompt = store.build_memory_prompt(cid, q)
	print("Memory prompt:\n", prompt)
