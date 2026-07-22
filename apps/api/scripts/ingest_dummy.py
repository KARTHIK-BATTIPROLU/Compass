import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

# Check if Gemini key is available
if not os.getenv("GEMINI_API_KEY"):
    print("Warning: GEMINI_API_KEY not found in environment. Ingestion might fail if not set.")

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

url = os.getenv("QDRANT_URL", "http://localhost:6333")
api_key = os.getenv("QDRANT_API_KEY")
client = QdrantClient(url=url, api_key=api_key)
collection_name = "curriculum"

dummy_data = [
    Document(
        page_content="Newton's First Law: An object at rest remains at rest, and an object in motion remains in motion at constant speed and in a straight line unless acted on by an unbalanced force.",
        metadata={"subject": "Physics", "class_level": "9th", "topic": "Laws of Motion"}
    ),
    Document(
        page_content="Newton's Second Law: The acceleration of an object depends on the mass of the object and the amount of force applied (F=ma).",
        metadata={"subject": "Physics", "class_level": "9th", "topic": "Laws of Motion"}
    ),
    Document(
        page_content="Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water. It involves chlorophyll and generates oxygen as a byproduct.",
        metadata={"subject": "Biology", "class_level": "10th", "topic": "Life Processes"}
    ),
    Document(
        page_content="The human heart has four chambers: two upper atria and two lower ventricles. The right atrium receives deoxygenated blood from the body, which is pumped to the lungs by the right ventricle.",
        metadata={"subject": "Biology", "class_level": "10th", "topic": "Life Processes"}
    )
]

def main():
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        print(f"Created collection {collection_name}")
    else:
        print(f"Collection {collection_name} already exists.")
        
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )
    
    print("Ingesting dummy curriculum data...")
    vector_store.add_documents(dummy_data)
    print("Ingestion complete!")

if __name__ == "__main__":
    main()
