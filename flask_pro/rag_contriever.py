import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained('facebook/contriever')
model = AutoModel.from_pretrained('facebook/contriever')

# Move model to the device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)


def mean_pooling(token_embeddings, mask):
    token_embeddings = token_embeddings.masked_fill(~mask[..., None].bool(), 0.)
    sentence_embeddings = token_embeddings.sum(dim=1) / mask.sum(dim=1)[..., None]
    return sentence_embeddings


def find_similar_sentences(sentences, keyword, threshold=0.6):
    # Tokenize and encode the sentences and keyword
    inputs = tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
    keyword_inputs = tokenizer([keyword], padding=True, truncation=True, return_tensors='pt')

    # Move inputs to the device
    inputs = {key: value.to(device) for key, value in inputs.items()}
    keyword_inputs = {key: value.to(device) for key, value in keyword_inputs.items()}

    # Compute token embeddings
    outputs = model(**inputs)
    keyword_outputs = model(**keyword_inputs)

    # Perform mean pooling to get sentence embeddings
    sentence_embeddings = mean_pooling(outputs[0], inputs['attention_mask'])
    keyword_embedding = mean_pooling(keyword_outputs[0], keyword_inputs['attention_mask'])

    # Compute similarity scores
    similarity_scores = cosine_similarity(keyword_embedding.detach().cpu().numpy(),
                                          sentence_embeddings.detach().cpu().numpy())
    print(similarity_scores)
    # Filter and return sentences with similarity score greater than threshold
    similar_sentences = [sentences[i] for i, score in enumerate(similarity_scores[0]) if score > threshold]

    return similar_sentences

# Example usage
sentences = [
    "water",
    "riverbank",
    "reservoir"
]

keyword = "lake"

similar_sentences = find_similar_sentences(sentences, keyword)
print(similar_sentences)
