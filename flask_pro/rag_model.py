from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")  # Print the device being used

# Load the pre-trained sentence transformer model to the specified device
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2').to(device)


def calculate_similarity(words, key_word,mode=None):
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
    similarity_dict = {}
    similarity_dict_all = {}
    for word, similarity in zip(words, similarity_scores):
        similarity_dict_all[word] = float(similarity)
        if similarity > 0.95:
            similarity_dict = {word: float(similarity)}
            break
        elif similarity > 0.6:
            similarity_dict[word] = float(similarity)
    if mode=='print':
        sorted_items_all = sorted(similarity_dict_all.items(), key=lambda x: x[1], reverse=True)
        print(sorted_items_all)

    # sorted_items = sorted(similarity_dict.items(), key=lambda x: x[1],reverse=True)
    # sorted_dict_by_values = {k: v for k, v in sorted_items}

    filtered_items = {k: v for k, v in similarity_dict.items() if v > 0.8}
    sorted_items = sorted(filtered_items.items(), key=lambda x: x[1], reverse=True)
    sorted_dict_by_values = {k: v for k, v in sorted_items}
    return sorted_dict_by_values

#
# # Example usage
# words = ['water','riverbank']
# key_word = "lake"
# similarity_scores = calculate_similarity(words, key_word,'print')
# print(similarity_scores)
