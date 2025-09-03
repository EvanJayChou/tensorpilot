# TensorPilot: Multi-Agentic AI System for Complex Mathematical Reasoning

This open-sourced research project investigates the use of multi-agent frameworks for agent orchestration and task delegation. Each agent is integrated into an AutoGen Group Chat, where each agent leverages different math engines, APIs, visualization tools, etc. to analyze and compute college-level mathematic questions ranging from calculus, linear algebra, and differential equations.

**Key Highlights**

- Agentic RAG is incorporated and fetches documents from a global dataset including math proofs and formula sheets
- Math agents converse with each other to break down and solve a user query
- Memory retrievals based on previously solved problems further contextualize the RAG agent
- Deployed into Azure, using Cognitive Search, AI Search, and other services including Kubernetes

## Tools and Software

- LangChain/LangGraph
- ReAct
- Azure
    - Key Vault
    - Cognitive Search
    - Kubernetes
- Terraform

## Benchmarks

*To be announced...*

## Contributing

- Fork the repository
- Create an Azure account
- Follow steps in the terraform/README.md to set up Azure services and resource group through Infrastructure as Code (IaC)

---

## Credits

**Developed by**: Evan Chou

**Associated with**: AI Club at Pasadena City College
