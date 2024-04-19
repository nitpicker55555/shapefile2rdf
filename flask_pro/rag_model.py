from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")  # Print the device being used

# Load the pre-trained sentence transformer model to the specified device
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2').to(device)


def calculate_similarity(words, key_word):
    words=list(words)
    # Check if a GPU is available and select the appropriate device

    # Include the key_word in the list of words to encode
    words_with_key = words + [key_word]

    # Compute embeddings for all words including the key_word
    embeddings = model.encode(words_with_key, convert_to_tensor=True, show_progress_bar=True)

    # Extract the embedding for the key_word
    key_word_embedding = embeddings[-1].unsqueeze(0)

    # Compute the cosine similarity between the key_word and all other words
    similarities = cosine_similarity(embeddings[:-1].cpu().numpy(), key_word_embedding.cpu().numpy())

    # Flatten the similarity array to get a list of similarity scores
    similarity_scores = similarities.flatten()

    # Create a dictionary to store the similarities, only include words with similarity > 0.7
    similarity_dict = {word: float(similarity) for word, similarity in zip(words, similarity_scores) if
                       similarity > 0.7}
    sorted_items = sorted(similarity_dict.items(), key=lambda x: x[1],reverse=True)
    sorted_dict_by_values = {k: v for k, v in sorted_items}
    return sorted_dict_by_values


# Example usage
# words = ['good for agriculture','not good for agriculture','bad for agriculture']
# key_word = "negative for farmland"
# similarity_scores = calculate_similarity(words, key_word)
# print(similarity_scores)
