"""
Centralized LLM Client for Happy2Align
Handles all OpenAI API calls with consistent timeout and fallback logic
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, BaseMessage
from openai import AsyncOpenAI, OpenAI
import time
import httpx
from agents.config import (
    OPENAI_API_KEY, PRIMARY_MODEL, FALLBACK_MODEL,
    DEFAULT_TEMPERATURE, FALLBACK_TEMPERATURE,
    MODEL_TIMEOUT, FALLBACK_TIMEOUT, REQUEST_TIMEOUT
)

logger = logging.getLogger(__name__)

class LLMClient:
    """Centralized LLM client with consistent timeout and fallback handling"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance"""
        if cls._instance is None:
            cls._instance = super(LLMClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the LLM client"""
        if self._initialized:
            return
            
        # LangChain clients met aangepaste HTTP client configuratie
        self.primary_llm = ChatOpenAI(
            model_name=PRIMARY_MODEL,
            openai_api_key=OPENAI_API_KEY,
            request_timeout=MODEL_TIMEOUT,
            max_retries=2,
            http_client=httpx.Client(  # Gebruik sync client voor LangChain
                timeout=MODEL_TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        )
        
        self.fallback_llm = ChatOpenAI(
            model_name=FALLBACK_MODEL,
            openai_api_key=OPENAI_API_KEY,
            request_timeout=FALLBACK_TIMEOUT,
            max_retries=1,
            http_client=httpx.Client(  # Gebruik sync client voor LangChain
                timeout=FALLBACK_TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        )
        
        # Direct OpenAI clients met aangepaste HTTP client configuratie
        self.async_client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            http_client=httpx.AsyncClient(  # Gebruik async client voor directe OpenAI calls
                timeout=MODEL_TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        )
        self.sync_client = OpenAI(api_key=OPENAI_API_KEY)
        
        self._initialized = True
        
    async def call_async(self, 
                        messages: Union[List[BaseMessage], List[Dict[str, str]]], 
                        use_fallback: bool = True,
                        **kwargs) -> str:
        """
        Async call to LLM with automatic fallback
        
        Args:
            messages: List of messages (LangChain format or dict format)
            use_fallback: Whether to use fallback model on failure
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Response text from the LLM
        """
        start_time = time.time()
        
        # Convert dict messages to LangChain format if needed
        if messages and isinstance(messages[0], dict):
            messages = self._convert_to_langchain_messages(messages)
        
        # Try primary model first
        try:
            logger.info(f"Calling {PRIMARY_MODEL} with timeout {MODEL_TIMEOUT}s")
            
            response = await asyncio.wait_for(
                self.primary_llm.ainvoke(messages, **kwargs),
                timeout=MODEL_TIMEOUT
            )
            
            elapsed = time.time() - start_time
            logger.info(f"{PRIMARY_MODEL} responded in {elapsed:.2f}s")
            return response.content.strip()
            
        except asyncio.TimeoutError:
            logger.warning(f"{PRIMARY_MODEL} timed out after {MODEL_TIMEOUT}s")
            if not use_fallback:
                raise TimeoutError(f"Model {PRIMARY_MODEL} timed out after {MODEL_TIMEOUT}s")
                
        except Exception as e:
            logger.error(f"Error with {PRIMARY_MODEL}: {str(e)}")
            if not use_fallback:
                raise
        
        # Fallback to faster model
        if use_fallback:
            try:
                logger.info(f"Falling back to {FALLBACK_MODEL} with timeout {FALLBACK_TIMEOUT}s")
                
                response = await asyncio.wait_for(
                    self.fallback_llm.ainvoke(messages, **kwargs),
                    timeout=FALLBACK_TIMEOUT
                )
                
                elapsed = time.time() - start_time
                logger.info(f"{FALLBACK_MODEL} responded in {elapsed:.2f}s (total time)")
                return response.content.strip()
                
            except asyncio.TimeoutError:
                logger.error(f"Both models timed out!")
                raise TimeoutError("Beide AI modellen deden er te lang over. Probeer het later opnieuw.")
                
            except Exception as e:
                logger.error(f"Fallback model also failed: {str(e)}")
                raise Exception(f"Beide modellen faalden: {str(e)}")
    
    def call_sync(self, 
                  messages: Union[List[BaseMessage], List[Dict[str, str]]], 
                  use_fallback: bool = True,
                  **kwargs) -> str:
        """
        Synchronous call to LLM with automatic fallback
        
        Args:
            messages: List of messages (LangChain format or dict format)
            use_fallback: Whether to use fallback model on failure
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Response text from the LLM
        """
        # Create new event loop for sync call
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If there's already a running loop, create a new one
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.call_async(messages, use_fallback, **kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self.call_async(messages, use_fallback, **kwargs))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.call_async(messages, use_fallback, **kwargs))
    
    async def call_openai_direct_async(self, 
                                      messages: List[Dict[str, str]], 
                                      model: Optional[str] = None,
                                      use_fallback: bool = True,
                                      **kwargs) -> str:
        """
        Direct async OpenAI API call with fallback
        
        Args:
            messages: List of messages in OpenAI format
            model: Model to use (defaults to PRIMARY_MODEL)
            use_fallback: Whether to use fallback model on failure
            **kwargs: Additional arguments for the API
            
        Returns:
            Response text from the model
        """
        if model is None:
            model = PRIMARY_MODEL
            
        start_time = time.time()
        
        # Try primary model
        try:
            logger.info(f"Direct OpenAI call to {model} with timeout {MODEL_TIMEOUT}s")
            
            response = await asyncio.wait_for(
                self.async_client.chat.completions.create(
                    model=model,
                    messages=messages,
                ),
                timeout=MODEL_TIMEOUT
            )
            
            elapsed = time.time() - start_time
            logger.info(f"{model} responded in {elapsed:.2f}s")
            return response.choices[0].message.content.strip()
            
        except asyncio.TimeoutError:
            logger.warning(f"Direct call to {model} timed out")
            if not use_fallback or model == FALLBACK_MODEL:
                raise TimeoutError(f"Model {model} timed out after {MODEL_TIMEOUT}s")
                
        except Exception as e:
            logger.error(f"Direct call to {model} failed: {str(e)}")
            if not use_fallback or model == FALLBACK_MODEL:
                raise
        
        # Fallback
        if use_fallback and model != FALLBACK_MODEL:
            logger.info(f"Falling back to {FALLBACK_MODEL}")
            return await self.call_openai_direct_async(messages, FALLBACK_MODEL, False, **kwargs)
    
    def call_openai_direct_sync(self, 
                               messages: List[Dict[str, str]], 
                               model: Optional[str] = None,
                               use_fallback: bool = True,
                               **kwargs) -> str:
        """
        Direct sync OpenAI API call with fallback
        
        Args:
            messages: List of messages in OpenAI format
            model: Model to use (defaults to PRIMARY_MODEL)
            use_fallback: Whether to use fallback model on failure
            **kwargs: Additional arguments for the API
            
        Returns:
            Response text from the model
        """
        if model is None:
            model = PRIMARY_MODEL
            
        start_time = time.time()
        
        # Try primary model
        try:
            logger.info(f"Direct sync OpenAI call to {model}")
            
            response = self.sync_client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=MODEL_TIMEOUT,
            )
            
            elapsed = time.time() - start_time
            logger.info(f"{model} responded in {elapsed:.2f}s")
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Direct sync call to {model} failed: {str(e)}")
            if not use_fallback or model == FALLBACK_MODEL:
                raise
        
        # Fallback
        if use_fallback and model != FALLBACK_MODEL:
            logger.info(f"Falling back to {FALLBACK_MODEL}")
            return self.call_openai_direct_sync(messages, FALLBACK_MODEL, False, **kwargs)
    
    async def create_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        Create embeddings using OpenAI
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            List of embedding values
        """
        try:
            response = await self.async_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding creation failed: {str(e)}")
            raise
    
    def create_embedding_sync(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        Create embeddings using OpenAI (sync version)
        
        Args:
            text: Text to embed
            model: Embedding model to use
            
        Returns:
            List of embedding values
        """
        try:
            response = self.sync_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding creation failed: {str(e)}")
            raise
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """Convert dict messages to LangChain format"""
        langchain_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                langchain_messages.append(SystemMessage(content=content))
            elif role == 'user':
                langchain_messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                # For assistant messages, we can use HumanMessage as placeholder
                # or implement AIMessage if needed
                langchain_messages.append(HumanMessage(content=f"Assistant: {content}"))
                
        return langchain_messages
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of both models"""
        results = {
            "primary_model": PRIMARY_MODEL,
            "fallback_model": FALLBACK_MODEL,
            "primary_available": False,
            "fallback_available": False,
            "embedding_available": False
        }
        
        # Test primary model
        try:
            test_msg = [HumanMessage(content="test")]
            await asyncio.wait_for(
                self.primary_llm.ainvoke(test_msg),
                timeout=MODEL_TIMEOUT
            )
            results["primary_available"] = True
        except Exception as e:
            logger.error(f"Primary model {PRIMARY_MODEL} is not available")
            logger.error(f"Error: {e}")
            pass
            
        # Test fallback model
        try:
            test_msg = [HumanMessage(content="test")]
            await asyncio.wait_for(
                self.fallback_llm.ainvoke(test_msg),
                timeout=FALLBACK_TIMEOUT
            )
            results["fallback_available"] = True
        except Exception as e:
            logger.error(f"Fallback model {FALLBACK_MODEL} is not available")
            logger.error(f"Error: {e}")
            pass
            
        # Test embeddings
        try:
            await self.create_embedding("test")
            results["embedding_available"] = True
        except:
            pass
            
        return results

    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup HTTP clients"""
        await self.cleanup()
    
    async def cleanup(self):
        """Cleanup HTTP clients"""
        if hasattr(self.primary_llm, 'http_client'):
            await self.primary_llm.http_client.aclose()
        if hasattr(self.fallback_llm, 'http_client'):
            await self.fallback_llm.http_client.aclose()
        if hasattr(self.async_client, 'http_client'):
            await self.async_client.http_client.aclose()

# Singleton instance
llm_client = LLMClient()