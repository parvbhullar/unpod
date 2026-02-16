"""
Global Function Manager for Section-Based Flows

Manages global utility functions that can be called from any node.
Similar to ObjectionManager but for non-objection utilities.
"""

from typing import List, Callable
from pipecat_flows import NodeConfig, FlowsFunctionSchema


class GlobalFunctionManager:
    """
    Manages global utility functions that can be called from any node.

    Global functions include:
    - get_knowledge_base_info: Fetch docs from FAISS knowledge base
    - handover_call: Transfer call to human agent
    - end_call: Gracefully end the conversation (optional)
    """

    def __init__(
        self,
        get_docs_handler: Callable = None,
        handover_handler: Callable = None,
        end_call_handler: Callable = None
    ):
        self.get_docs_handler = get_docs_handler
        self.handover_handler = handover_handler
        self.end_call_handler = end_call_handler
        self.global_functions = []  # Cached function schemas

    def get_global_functions(self) -> List[FlowsFunctionSchema]:
        """
        Get function schemas for all global utility functions.

        Returns:
            List of FlowsFunctionSchema objects for global utilities
        """
        if self.global_functions:
            return self.global_functions

        # Create function schema for knowledge base retrieval
        if self.get_docs_handler:
            kb_function = FlowsFunctionSchema(
                name="get_knowledge_base_info",
                handler=self.get_docs_handler,
                description=(
                    "Fetch relevant information from the knowledge base using FAISS semantic search. "
                    "Use results to inform answers, but if details are missing or unclear, politely direct the caller "
                    "to the admissions office or official website for confirmation."
                ),
                properties={
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant documents"
                    },
                    "top_k": {
                        "type": "number",
                        "description": "Number of top results to return (default: 3)"
                    }
                },
                required=["query"]
            )
            self.global_functions.append(kb_function)

        # Create function schema for handover
        if self.handover_handler:
            handover_function = FlowsFunctionSchema(
                name="handover_call",
                handler=self.handover_handler,
                description="Transfer the call to a human agent when AI cannot help or user requests human assistance",
                properties={
                    "reason": {
                        "type": "string",
                        "description": "Reason for handover (e.g., 'complex query', 'user request', 'technical issue')"
                    }
                },
                required=[]
            )
            self.global_functions.append(handover_function)

        # Create function schema for end call (optional)
        if self.end_call_handler:
            end_call_function = FlowsFunctionSchema(
                name="end_call",
                handler=self.end_call_handler,
                description="Gracefully end the conversation after completing all tasks or if user wants to hang up",
                properties={
                    "reason": {
                        "type": "string",
                        "description": "Reason for ending call (e.g., 'task completed', 'user request', 'farewell')"
                    }
                },
                required=[]
            )
            self.global_functions.append(end_call_function)

        return self.global_functions

    def inject_global_functions_into_nodes(self, nodes: List[NodeConfig]) -> List[NodeConfig]:
        """
        Add global utility functions to all nodes.

        Args:
            nodes: List of NodeConfig objects

        Returns:
            Same list of nodes with global functions added
        """
        # Get global functions
        global_functions = self.get_global_functions()

        if not global_functions:
            # No global functions to inject
            return nodes

        # Add global functions to each node (supports NodeConfig or dict payloads)
        for idx, node in enumerate(nodes):
            if isinstance(node, dict):
                existing_functions = list(node.get("functions", []))
                existing_names = set()
                for func in existing_functions:
                    if hasattr(func, "name"):
                        name = getattr(func, "name", None)
                        if name:
                            existing_names.add(name)
                    elif isinstance(func, dict):
                        name = func.get("name")
                        if name:
                            existing_names.add(name)
                for global_func in global_functions:
                    if global_func.name not in existing_names:
                        existing_functions.append(global_func)
                        existing_names.add(global_func.name)
                node["functions"] = existing_functions
                nodes[idx] = node
            else:
                existing_functions = list(getattr(node, "functions", [])) if getattr(node, "functions", None) else []
                existing_names = {getattr(f, "name", None) for f in existing_functions if getattr(f, "name", None)}
                for global_func in global_functions:
                    if global_func.name not in existing_names:
                        existing_functions.append(global_func)
                        existing_names.add(global_func.name)
                node.functions = existing_functions

        return nodes

    def has_global_functions(self) -> bool:
        """Check if any global functions exist."""
        return (
            self.get_docs_handler is not None or
            self.handover_handler is not None or
            self.end_call_handler is not None
        )
