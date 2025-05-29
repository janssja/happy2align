import os
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

class VectorStore:
    def __init__(self, api_key=None):
        """Initialiseer de Pinecone vectorstore."""
        self.api_key = api_key or os.getenv('PINECONE_API_KEY', 'your-api-key')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'your-openai-api-key'))
        self.index_name = "happy2align"
        self.dimension = 1536  # OpenAI embeddings dimensie
        
        # Initialiseer Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Creëer index als deze nog niet bestaat
        self._create_index_if_not_exists()
        
        # Haal de index op
        self.index = self.pc.Index(self.index_name)
    
    def _create_index_if_not_exists(self):
        """Creëer een Pinecone index als deze nog niet bestaat."""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-west-2")
            )
    
    def _get_embedding(self, text):
        """Genereer een embedding voor de gegeven tekst met OpenAI."""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    def store(self, user_id, session_id, content, content_type="requirement"):
        """Sla content op in de vectorstore."""
        # Genereer een unieke ID
        vector_id = f"{user_id}-{session_id}-{content_type}-{hash(content)}"
        
        # Genereer embedding
        embedding = self._get_embedding(content)
        
        # Sla op in Pinecone
        self.index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "content_type": content_type,
                        "content": content,
                        "timestamp": str(self.openai_client.embeddings.create)
                    }
                }
            ]
        )
        
        return vector_id
    
    def search(self, query, user_id=None, session_id=None, content_type=None, top_k=5):
        """Zoek naar vergelijkbare content in de vectorstore."""
        # Genereer embedding voor de query
        query_embedding = self._get_embedding(query)
        
        # Bouw filter op basis van parameters
        filter_dict = {}
        if user_id:
            filter_dict["user_id"] = user_id
        if session_id:
            filter_dict["session_id"] = session_id
        if content_type:
            filter_dict["content_type"] = content_type
        
        # Voer zoekopdracht uit
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        # Verwerk resultaten
        processed_results = []
        for match in results.matches:
            processed_results.append({
                "id": match.id,
                "score": match.score,
                "content": match.metadata["content"],
                "content_type": match.metadata["content_type"],
                "user_id": match.metadata["user_id"],
                "session_id": match.metadata["session_id"]
            })
        
        return processed_results
    
    def delete(self, vector_id=None, user_id=None, session_id=None):
        """Verwijder vectoren uit de vectorstore."""
        if vector_id:
            # Verwijder specifieke vector
            self.index.delete(ids=[vector_id])
        elif user_id and session_id:
            # Verwijder alle vectoren voor een specifieke sessie
            self.index.delete(
                filter={
                    "user_id": user_id,
                    "session_id": session_id
                }
            )
        elif user_id:
            # Verwijder alle vectoren voor een specifieke gebruiker
            self.index.delete(
                filter={
                    "user_id": user_id
                }
            )
