# LangGraph-style orchestration for math problem solving
from typing import Optional, Any
import json
import time

# Dynamic loaders to reuse local modules
import importlib.util
import pathlib


def _load(path_parts, attr=None):
	base = pathlib.Path(__file__).resolve().parent
	candidate = base
	for p in path_parts:
		candidate = candidate / p
	if not candidate.exists():
		candidate = base.parent.parent / 'src'
		for p in path_parts:
			candidate = candidate / p
	spec = importlib.util.spec_from_file_location('_mod', str(candidate))
	mod = importlib.util.module_from_spec(spec)
	loader = spec.loader
	loader.exec_module(mod)
	return getattr(mod, attr) if attr else mod


# Load components
RAGManager = _load(['workflow', 'rag.py'], 'RAGManager')
ReActPlanner = _load(['workflow', 'react.py'], 'ReActPlanner')
MemoryStore = _load(['memory', 'memory.py'], 'MemoryStore')


class LangGraphSystem:
	def __init__(self, embedding_fn: Optional[Any] = None, embedding_dim: Optional[int] = None):
		self.rag = RAGManager(embedding_fn=embedding_fn, embedding_dim=embedding_dim)
		self.memory = MemoryStore(embedding_fn=embedding_fn, embedding_dim=embedding_dim)
		self.planner = ReActPlanner(embedding_fn=embedding_fn, embedding_dim=embedding_dim)

	def ingest_domain_docs(self, docs: dict):
		for doc_id, text in docs.items():
			self.rag.add_global_document(doc_id, text)

	def solve(self, problem: str, user_id: Optional[str] = None, verify: bool = True):
		# Use planner to create a plan
		plan = self.planner.plan(problem, user_id=user_id, verify=verify)
		return plan


if __name__ == '__main__':
	print('LangGraphSystem demo')
	lg = LangGraphSystem()
	# ingest typical math docs
	lg.ingest_domain_docs({
		'pythag': 'Pythagorean theorem: a^2 + b^2 = c^2',
		'area': 'Area of a circle: A = pi * r^2',
		'deriv': 'Derivative rules: d/dx x^n = n x^(n-1)'
	})

	problem = 'Find the hypotenuse of a right triangle with legs 3 and 4.'
	res = lg.solve(problem, user_id='alice')
	print(json.dumps(res, indent=2))


# Optional: real langgraph integration wrapper
try:
	import langgraph

	class LangGraphWrapper:
		def __init__(self, embedding_fn: Optional[Any] = None, embedding_dim: Optional[int] = None):
			# create the underlying system
			self.system = LangGraphSystem(embedding_fn=embedding_fn, embedding_dim=embedding_dim)

			# if langgraph exposes Graph and Tool, register tools and build a graph
			GraphCls = getattr(langgraph, 'Graph', None)
			ToolCls = getattr(langgraph, 'Tool', None)
			MemoryCls = getattr(langgraph, 'Memory', None)

			self.graph = None
			if GraphCls and ToolCls:
				tools = []

				# RAG retrieval tool
				def rag_lookup(query: str, user_id: Optional[str] = None, top_k:int=5):
					return self.system.rag.retrieve(query, user_id=user_id, top_k_global=top_k, top_k_user=top_k)

				tools.append(ToolCls(name='rag_lookup', func=rag_lookup, description='Retrieve relevant documents from RAG'))

				# Register available MCP tools from the mcp module
				mcp_mod = _load(['llm', 'mcp.py'])
				mcp_tool_names = [n for n in dir(mcp_mod) if n.endswith('_eval') or n.endswith('_query') or n.endswith('_plot')]
				for name in mcp_tool_names:
					func = getattr(mcp_mod, name)
					# wrap to a uniform signature
					def make_tool(f):
						return lambda *a, **k: f(*a, **k)
					tools.append(ToolCls(name=name, func=make_tool(func), description=f'MCP tool: {name}'))

				# create graph with planner as agent if GraphCls expects an agent
				try:
					agent_obj = self.system.planner
					if MemoryCls:
						memory = MemoryCls()
						self.graph = GraphCls(agent=agent_obj, tools=tools, memory=memory)
					else:
						self.graph = GraphCls(agent=agent_obj, tools=tools)
				except Exception:
					# best-effort: instantiate Graph with agent only
					try:
						self.graph = GraphCls(agent=self.system.planner)
					except Exception:
						self.graph = None

		def ingest_domain_docs(self, docs: dict):
			self.system.ingest_domain_docs(docs)

		def solve(self, problem: str, user_id: Optional[str] = None, verify: bool = True):
			# Prefer running via langgraph graph if available
			if self.graph and hasattr(self.graph, 'run'):
				try:
					return self.graph.run(problem)
				except Exception:
					pass
			return self.system.solve(problem, user_id=user_id, verify=verify)

except Exception:
	# langgraph not available; don't raise -- fallback to LangGraphSystem
	LangGraphWrapper = LangGraphSystem
