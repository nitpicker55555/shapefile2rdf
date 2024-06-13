import chromadb,time,os
# Example setup of the client to connect to your chroma server
from dotenv import load_dotenv
load_dotenv()
from rag_model_openai import get_embedding


os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")

client = chromadb.HttpClient(host="localhost", port=8000)

collection = client.get_or_create_collection("buildings_name_vec")
import chromadb.utils.embedding_functions as embedding_functions
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ['OPENAI_API_KEY'],
                model_name="text-embedding-3-small"
            )
while True:

    text_str=input(":")
    start_time=time.time()
    results = collection.query(
        query_embeddings=list(get_embedding(text_str)),
        n_results=30,

        # where={"metadata_field": "is_equal_to_this"}, # optional filter
        # where_document={"$contains":text_str}  # optional filter
    )
    total_time=time.time()-start_time
    print(total_time)
    print(results)