from datetime import datetime
import json
import logging
import uuid

import fitz
import pandas as pd

# RAG Agent
from swarmauri.agents.concrete.RagAgent import RagAgent

# Conversations and messages
from swarmauri.conversations.concrete.SessionCacheConversation import (
    SessionCacheConversation,
)
from swarmauri.messages.concrete import SystemMessage, AgentMessage, HumanMessage

# Embedding Document
from swarmauri.documents.concrete.Document import Document

# LLMs
from swarmauri.llms.concrete.AnthropicModel import AnthropicModel
from swarmauri.llms.concrete import GeminiProModel
from swarmauri.llms.concrete import GroqModel
from swarmauri.llms.concrete import MistralModel
from swarmauri.llms.concrete import OpenAIModel

# utils
from swarmauri.utils.load_documents_from_json import load_documents_from_json_file
from swarmauri.utils.sql_log import sql_log

# Vector Stores
from swarmauri.vector_stores.concrete import (
    Doc2VecVectorStore,
    TfidfVectorStore,
    SqliteVectorStore,
)
from swarmauri_community.vector_stores.RedisVectorStore import RedisVectorStore
from swarmauri_community.vector_stores.DuckDBVectorStore import DuckDBVectorStore
from swarmauri_community.vector_stores.Neo4jVectorStore import Neo4jVectorStore
from swarmauri_community.vector_stores.PersistentChromaDBVectorStore import (
    PersistentChromaDBVectorStore,
)
from swarmauri_community.vector_stores.PersistentQdrantVectorStore import (
    PersistentQdrantVectorStore,
)
from swarmauri_community.vector_stores.PineconeVectorStore import PineconeVectorStore
from swarmauri_community.vector_stores.CloudQdrantVectorStore import (
    CloudQdrantVectorStore,
)
# from swarmauri_community.vector_stores.CloudWeaviateVectorStore import (
#     CloudWeaviateVectorStore,
# )

head = """<link rel="icon" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAABWFJREFUWEe1V2tsFFUU/s7M7KO77Ra2LRisUArasLjbLqVdaRfQkACCNISgUQJCiCHGfyaYEIMSfIQY/K3GEAUkqNHwUJ6JEoht7ZZuu92uaCktILUJpSy0233PzNU7SClNu9MWvX8ms+ec7/vOuefMvUsYxypxu2dYgHRLS8utcbhjrttdIMJiaG+p69HzJz0Hl8dTKMLYwRiIMeW11ov1hzLFlFZUbSQS93EfNZGaGwz6ujP56wpwOCoeM2abrhOREUBCluXKNv+vbaOBOssXOSVJagRgZgxJOZaaFQr5bj6SAB7sqvS+KoA+J4KJqawucLHWOxpoWaW3joiqOLmqsm3BptqDehXWrcB9gPlub6lkwGcEeAC8xxgjgmDhdgY1xp9E9A7AGmRZfj3U7AvqkWsx43G67+NaWLVeFMVvAIhjxCmKorwcbKr/fry4ExJQ5vFeI9CsTOCMsauBxtri/1yAy+WyCmZbhIgyimaMsd7ueHZPj1/bFr01gQqUG9yerBhAUmZQJrfIcQv8/rQe+YR7oKzS20ZET+tsQSjQWOscD7muAN7p5wOBXAuZp0GQ8g4fPrgjMhCpUWQZ4XAYf3Xf+8Y8XlgIu90OUZJgs9mOv7Jh00dGSehTTOgtLy4eICI2liBtC862tlrzJOtWEK0gYDZAFkbMAgYbANPwaWGMIRpPIJVKI3zrpjZH9vzpMBoNsGaZ+SgO5+LESRAGiFEMYDEGXCWiM32pyJcrSkuj1NDaUSgahJ8JeCpT2RRFwZ2BCG6F7yIWT2iuT0yza88bvWHtackyo8A+BVNtORDFsSZ1iKU9lZKXUdOlK98C9NJo5IqiIhKNItw/gP7IIFT1XiVzrBZMy5uKntbvtIxnuF7EzdthRKL3Gl8QCLk52bDn2pCTbYUoCKPmxsC+oabfO/t5qXlpeZaxRBLRWFwDG4zFwX/nyyBJGmC+PRdmkwn1F85i3ewTmu3otTVYtGQ5Eskk+sL9muC0LGs2LjDbmoUciwXZlixkmU1adbStYrhLvlBH/HLXdXMilYaqqg8pNRoMyM2xYootR8uaB3FBZ06dgDfvDJ51GTT/88E06u+swvKVq4Z8eAJ3ByLoj0SRSj88kYIgwGw0oGROUYIaQx117V1/VimqAk5oNhm1veSE/H14U8XjcXy1fz8W5Aewrpr35oN1pC6JQNiNjZu3wGw2Dxm4YC4gMhhDLJFAIpnS3kVBREnxrHpq/qOrRlXZsUznAgf5LRTCoQMHcPt2X6ZeRX5BATZt3oJ5DsfIiRgZx5iqrtVmpulS5xsA7QWYdroNX52dV3Dyhx/RFmzNSDzS6Corwws1NSgqmj2aEN6t2xc65nw6NLQNbV3TRUFdCyInAWZFUbs+2L3r3e4bNx6u9YRkADNnFiV37t71PhgVCwL/FqAtLUePP+N0aheVjGfB1g1L/YudxgXi6FOkK0VRgV+CqZYvvr6wYCznjAKSDav3GiVhuy5TBgdZVT82VJ58a1ICButWlVlNQjOf5smJYCwWVcqtS0+3TEoAD0o1rD5nkITnJiNAVtg5g+fEskyxupm5K6sXgoSGDNewsfAVQsrT7PP5H0kADy6tqN4jCMKOiVRBYezDYGPtTr0Y3Qr8CyCWVniPCgKt0QPkdsbYsUBj7XoAip7/eAXA4XAYXfMK9lU8KW1kY9wLiTHm75APtF8b3Ob/P65kPJven55fb7MIu0xGmv9gOhhLy2iLJtnuqUtPHtHLerh93BUYCdp1emXJJ8eS5xlAb9ZkLSlcferyRIjv+05aAAco8yz28UM94Kvl/5YmtR5JgKuy+m0wsODFuj2TYv8n6G+wcRzTJW9piwAAAABJRU5ErkJggg==" type="image/png">"""


class RagAssistant:
    def __init__(
        self,
        api_key: str,
        llm: str,
        vectorstore="Doc2Vec",
        model_name: str = None,
        system_context: str = "You are a helpful assistant.",
        # vector store params
        vector_store_db_path: str = "prompt_responses.db",
        vector_store_api_key: str = None,
        vector_store_url: str = None,
        vector_store_collection_name: str = None,
        vector_store_vector_size: int = None,
        vector_store_vectorizer: str = None,
    ):
        logging.info("Initializing... this will take a moment.")

        # Available LLMs
        self.available_llms = {
            "openai": OpenAIModel,
            "groq": GroqModel,
            "mistral": MistralModel,
            "gemini": GeminiProModel,
            "anthropic": AnthropicModel,
        }

        # Available vector_stores
        self.available_vector_stores = {
            "Doc2Vec": Doc2VecVectorStore,
            "TF-IDF": TfidfVectorStore,
            "SQLite": SqliteVectorStore,
            "Redis": RedisVectorStore,
            "Duckdb": DuckDBVectorStore,
            "Neo4j": Neo4jVectorStore,
            "Local_Chromadb": PersistentChromaDBVectorStore,
            "Local_Qdrant": PersistentQdrantVectorStore,
            "Cloud_Qdrant": CloudQdrantVectorStore,
            # "cloud_weaviate": CloudWeaviateVectorStore,
        }

        # initialize attr with params
        self.system_context = SystemMessage(content=system_context)
        self.api_key = api_key
        self.model_name = model_name

        # Vector Store params
        self.vector_store_db_path = vector_store_db_path
        self.vector_store_api_key = vector_store_api_key
        self.vector_store_url = vector_store_url
        self.vector_store_collection_name = vector_store_collection_name
        self.vector_store_vector_size = vector_store_vector_size
        self.vector_store_vectorizer = vector_store_vectorizer

        self.conversation = SessionCacheConversation(
            max_size=200, system_context=self.system_context
        )

        self.agent = None

        self.chat_idx = {}
        self.retrieval_table = []
        self.document_table = []

        # self.long_term_memory_df = None
        # self.last_recall_df = None

        self.set_llm(llm)

        self.long_term_memory_df = pd.DataFrame([])
        self.last_recall_df = pd.DataFrame([])

        self.model_name = model_name
        self.set_model(model_name)
        self.set_vector_store(vectorstore)
        self.set_llm(llm)
        self.set_model(model_name)

        self.initialize_agent()

        self.css = """
#chat-dialogue-container {
    min-height: 54vh !important;
}

#document-table-container {
    min-height: 80vh !important;
}

footer {
    display: none !important;
}
"""
        self.favicon_path = "./favicon-32x32.png"
        self._show_api_key = False
        self._show_provider_model = False
        self._show_system_context = False
        self._show_documents_tab = False
        self._init_file_path = None

    def initialize_agent(self):
        VS = self.vector_store
        self.agent = RagAgent(
            name="Rag",
            system_context=self.system_context,
            llm=self.llm,
            conversation=self.conversation,
            vector_store=VS,
        )
        return self.agent

    def get_llm_name(self):
        for llm_name, llm in self.available_llms.items():
            if isinstance(self.llm, llm):
                return llm_name

    def get_allowed_models(self):
        return self.llm.allowed_models

    def set_llm(self, llm: str, **kwargs):
        """Set the LLM to use for the assistant"""
        chosen_llm = self.available_llms.get(llm, None)

        if chosen_llm is None:
            raise ValueError(
                f"LLM '{llm}' is not supported. Choose from {self.available_llms.keys()}"
            )

        self.llm = chosen_llm(api_key=self.api_key, **kwargs)

        if self.agent is not None:
            self.agent.llm = self.llm

    def set_model(self, provider_model_choice: str):
        if provider_model_choice is None:
            return

        if provider_model_choice not in self.llm.allowed_models:
            raise ValueError(f"Invalid model choice: {provider_model_choice}")

        self.model_name = provider_model_choice
        self.llm.name = self.model_name

    def set_vector_store(self, vector_store: str, vector_store_kwargs: dict = {}):
        chosen_vector_store = self.available_vector_stores.get(vector_store, None)

        if chosen_vector_store is None:
            raise ValueError(
                f"vector_store '{vector_store}' is not supported. Choose from {self.available_vector_stores.keys()}"
            )
        self.vector_store = chosen_vector_store(**vector_store_kwargs)

    def load_json_from_file_info(self, file):
        self._load_and_filter_json(file.name)

    def _load_and_filter_json(self, filename):
        # Load JSON file using json library
        try:
            documents = []
            data = []

            with open(filename, "r") as f:
                data = json.loads(f.read())

            # Filter out invalid or empty documents
            for doc in data:
                if doc and isinstance(doc, str):  # Ensure valid content
                    documents.append(Document(content=doc))

            # documents = load_documents_from_json_file(filename)

            # empty existing documents first
            # self.agent.vector_store.documents = []

            self.vector_store.add_documents(documents)

            # self.long_term_memory_df = self.preprocess_documents(documents)
            # return self.long_term_memory_df
        except json.JSONDecodeError:
            # error_fn("Invalid JSON file. Please check the file and try again.")
            return "Invalid JSON file. Please check the file and try again."

    def preprocess_documents(self, documents):
        try:
            docs = [d.to_dict() for d in documents]
            for d in docs:
                metadata = d["metadata"]
                for each in metadata:
                    d[each] = metadata[each]
                del d["metadata"]
                del d["type"]
                del d["embedding"]
            df = pd.DataFrame.from_dict(docs)
            return df
        except Exception as e:
            # error_fn("preprocess_documents failed: {e}")
            logging.info(f"preprocess_documents: {e}")

    def save_df(self, df):
        documents = self.dataframe_to_documents(df)
        self.agent.vector_store.documents = []
        self.agent.vector_store.add_documents(documents)
        self.long_term_memory_df = self.preprocess_documents(documents)
        return self.long_term_memory_df

    def dataframe_to_documents(self, df):
        documents = []
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            id = row_dict.pop("id", "")
            content = row_dict.pop("content", "")
            metadata = row_dict  # remaining data becomes metadata

            # Convert the row to dictionary and create a DocumentBase instance

            document = Document(id=id, content=content, metadata=metadata)
            documents.append(document)
        return documents

    def clear_chat(self, chat_id):
        # We could clear, but if we create a new instance, we get a new conversation id
        try:
            del self.chat_idx[chat_id]
        except KeyError:
            pass
        return chat_id, "", [], []

    def chatbot_function(
        self,
        chat_id,
        message,
        api_key: str = None,
        model_name: str = None,
        system_context: str = None,
        fixed_retrieval: bool = True,
        top_k: int = 5,
        temperature: int = 1,
        max_tokens: int = 256,
        conversation_size: int = 2,
        session_cache_size: int = 2,
    ):
        try:
            if not chat_id:
                chat_id = str(uuid.uuid4())
            start_datetime = datetime.now()

            # Set additional parameters
            self.api_key = api_key
            self.set_model(model_name)

            # Set Conversation Size
            self.agent.system_context = system_context

            if chat_id not in self.chat_idx:
                self.chat_idx[chat_id] = SessionCacheConversation(
                    max_size=conversation_size,
                    system_message_content=system_context,
                    session_cache_max_size=session_cache_size,
                )

            self.agent.conversation = self.chat_idx[chat_id]

            # Predict
            try:
                response = self.agent.exec(
                    message,
                    top_k=top_k,
                    fixed=fixed_retrieval,
                    model_kwargs={"temperature": temperature, "max_tokens": max_tokens},
                )
            except Exception as e:
                logging.info(f"chatbot_function agent error: {e}")

            # Update Retrieval Document Table
            self.last_recall_df = self.preprocess_documents(self.agent.last_retrieved)

            # Get History

            history = [
                each["content"] for each in self.agent.conversation.session_to_dict()
            ]
            if len(history) > 0:
                history = [
                    (history[i], history[i + 1]) for i in range(0, len(history), 2)
                ]

            # SQL Log
            end_datetime = datetime.now()
            sql_log(
                self.agent.conversation.id,
                model_name,
                message,
                response,
                start_datetime,
                end_datetime,
            )

            return chat_id, "", self.last_recall_df, history
        except Exception as e:
            # error_fn(f"chatbot_function error: {e}")
            self.agent.conversation._history.pop(0)
            logging.info(f"chatbot_function error: {e}")
            return chat_id, "", [], history

    def chunk_pdf_by_page(self, file_path: str) -> list[str]:
        """
        Splits a PDF into chunks by page and returns the text as a list of strings.
        """
        try:
            doc = fitz.open(file_path)  # Open the PDF
            chunks = []

            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)  # Load a specific page
                text = page.get_text("text")  # Extract text from the page
                page_doc = Document(content=text)  # Create a Document object
                chunks.append(page_doc)  # Add the text to the list

            doc.close()  # Close the document after processing
            return chunks

        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []

    def load_pdf_from_file_info(self, file):
        pages = self.chunk_pdf_by_page(file.name)
        self.vector_store.add_documents(pages)
