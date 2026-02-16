import asyncio
import os
import sys
import json
import logging
from typing import Optional, Dict, Any, List

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from super.core.voice.managers.knowledge_base import KnowledgeBaseManager
    from super.core.voice.managers.context_processor import FAISSContextProcessor
    from super.core.voice.pipecat.handler import PipecatVoiceHandler
    
    # Try to import ModelConfig, but make it optional
    try:
        from super.core.voice.models.config import ModelConfig
    except ImportError:
        logger.warning("ModelConfig import failed, some features may be limited")
        ModelConfig = None
        
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error(f"Current Python path: {sys.path}")
    raise


class KnowledgeBaseTester:
    def __init__(self, session_id: str = "test_session_123"):
        self.session_id = session_id
        self.kb_manager = KnowledgeBaseManager(
            logger=logger,
            session_id=self.session_id,
            vector_count=1000,
            embedding_dim=384,
            use_redis=False  # Disable Redis for testing
        )

        # Test knowledge base configuration
        self.test_knowledge_bases = [

            {
                "name": "Vajiram_And_Ravi_Knowledge_base.docx",
                "token": "C1TU09CM2ZWD3HNOXHY70KCT"
            }
        ]

    async def initialize(self):
        """Initialize the knowledge base manager and preload test documents."""
        logger.info("Initializing KnowledgeBaseManager...")

        # Mock user state with test knowledge bases
        class MockUserState:
            def __init__(self, knowledge_bases):
                self.knowledge_base = knowledge_bases
                self.token = "USER_TOKEN_123"
                self.thread_id = "test_thread_123"  # Fixed: Use a static thread ID

        user_state = MockUserState(self.test_knowledge_bases)

        # Initialize context retrieval
        logger.info("Initializing FAISS context retrieval...")
        await self.kb_manager._init_context_retrieval()

        # Preload knowledge base documents
        logger.info("Preloading knowledge base documents...")
        success = await self.kb_manager._preload_knowledge_base_documents(user_state)

        if not success:
            logger.error("Failed to preload knowledge base documents")
            return False

        logger.info("Knowledge base initialization completed successfully")
        return True

    async def test_context_enhancement(self, query: str) -> str:
        """Test if the knowledge base enhances the context for a given query."""
        if not hasattr(self.kb_manager, '_context_retrieval'):
            logger.error("Context retrieval not initialized. Call initialize() first.")
            return ""

        logger.info(f"\nTesting query: '{query}'")

        # Add FAISS context to the query
        enhanced_content = await self.kb_manager._add_faiss_context_to_transcript(query)

        if enhanced_content == query:
            logger.warning("No context was added to the query")
        else:
            logger.info("Context was successfully added to the query")

        logger.info(f"Enhanced content:\n{enhanced_content}")
        return enhanced_content

    async def search_directly(self, query: str) -> Dict[str, Any]:
        """Search directly in the knowledge base using the get_docs method."""
        logger.info(f"\nSearching directly for: '{query}'")

        # Create a mock function call params object
        class MockFunctionCallParams:
            def __init__(self):
                self.arguments = {"query": query}

        params = MockFunctionCallParams()

        # Search in knowledge base
        results = await self.kb_manager.get_docs(
            params=params,
            query=query
        )

        logger.info(f"Search results: {json.dumps(results, indent=2)}")
        return results


async def main():
    # Initialize the tester
    tester = KnowledgeBaseTester()

    # Initialize knowledge base
    if not await tester.initialize():
        logger.error("Failed to initialize knowledge base")
        return

    # Test queries
    test_queries = [
        "How can I give feedback or complaints about the course?",
        "Who was the UPSC CSE 2024 topper from Vajiram & Ravi?",
        " Is there any discount if I take multiple courses together? "
    ]

    for query in test_queries:
        # Test context enhancement
        await tester.test_context_enhancement(query)

        # Test direct search
        await tester.search_directly(query)

    logger.info("\nTest completed successfully!")


if __name__ == "__main__":
    import json

    asyncio.run(main())
