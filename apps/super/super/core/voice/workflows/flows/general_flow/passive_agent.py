from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from dataclasses import dataclass ,asdict
from typing import Optional
import os
from dotenv import load_dotenv
load_dotenv(verbose=True)
import requests

@dataclass
class PipelineTasks:
    assignee: str
    task_name: str
    task_description: str
    task_status: str
    task_result: Optional[str] = None

from langchain.tools import tool

class PassiveAgent:

    def __init__(self,handler):
        self.handler = handler
        self.fetch_docs_tool = self._create_fetch_docs_tool()
        self.handover_tool = self.handover_tool()

    @tool("handover_call", return_direct=True)
    def handover_tool(self):
        """Handover call top human agent or suppervisor"""
        self.handler._handover_call()

        return None

    def _create_fetch_docs_tool(self):
        """Create a single-input tool with handler captured in closure."""
        handler = self.handler

        @tool("fetch_docs", return_direct=True)
        def fetch_docs_tool(query: str):
            """Fetch documents related to a query."""
            import asyncio
            import nest_asyncio
            print(f"🔍 Fetching documents for: {query}")
            try:
                nest_asyncio.apply()
            except:
                pass
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                doc_list = loop.run_until_complete(handler.get_docs(query))
            finally:
                loop.close()

            # Convert SearchDoc objects to JSON-serializable dictionaries
            if doc_list:
                serialized_docs = []
                for doc in doc_list[:2]:
                    if hasattr(doc, 'to_dict'):
                        serialized_docs.append(doc.to_dict())
                    elif isinstance(doc, dict):
                        serialized_docs.append(doc)
                    else:
                        # Fallback: convert to string
                        serialized_docs.append(str(doc))
                return serialized_docs
            return []

        return fetch_docs_tool

    async def create_task_agent(self):
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Run the synchronous initialize_agent in a thread pool to avoid blocking the event loop
        import asyncio
        agent = await asyncio.to_thread(
            initialize_agent,
            llm=llm,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            tools=[self.fetch_docs_tool]
        )
        return agent


    async def run(self):
        import asyncio

        # Await the async agent creation
        agent = await self.create_task_agent()

        while True:
            # print(handler.task_queue[0] if handler.task_queue else None ,"task queue")
            pending_task = next(
                (t for t in self.handler.task_queue if  t.task_status == "pending"),
                None
            )
            # print(pending_task ,"pending tasks i m looking for ")
            if pending_task:
                # Run the synchronous agent.run in a thread pool to avoid blocking the event loop
                response = await asyncio.to_thread(agent.run, pending_task.task_description)
                if response:
                    # print(response, "updating task")
                    pending_task.task_result = response
                    pending_task.task_status = "done"

            # Yield control back to the event loop to prevent blocking
            await asyncio.sleep(0.1)

            if not self.handler.agent_running:
                break
