import concurrent.futures
import json
import os

from openai import OpenAI

import numpy as np
import pandas as pd
from tqdm import tqdm
from geo_functions import *
from dotenv import load_dotenv
load_dotenv()
os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")

pd.set_option('display.max_rows', None)
client = OpenAI()


def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    try:
        embed = client.embeddings.create(input=[text], model=model).data[0].embedding
        return embed
    except Exception as e:
        raise Exception(text, 'embedding get error', e)

def get_embeddings_dict(words,file_path, model="text-embedding-3-small"):
    def process_word(word):
        return word, get_embedding(word, model)

    embeddings_dict = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_word = {executor.submit(process_word, word): word for word in words}
        for future in tqdm(concurrent.futures.as_completed(future_to_word), total=len(words), desc="Processing words"):
            word = future_to_word[future]
            try:
                word, embed = future.result()
                embeddings_dict[word] = embed
            except Exception as e:
                print(f"Error processing word {word}: {e}")
    save_embeddings_to_jsonl(embeddings_dict,file_path)

    return embeddings_dict
#
def save_embeddings_to_jsonl(embeddings_dict, file_path):
    with open(f"{file_path}.jsonl", 'w') as f:
        for word, embedding in embeddings_dict.items():
            json_record = json.dumps({word: list(embedding)})
            f.write(json_record + '\n')
get_embeddings_dict(ids_of_attribute('points','name'),'points_name')
# get_embeddings_dict(ids_of_attribute('lines','name'),'lines_name')
# get_embeddings_dict(ids_of_attribute('land','name'),'land_name')
# get_embeddings_dict(ids_of_attribute('buildings','name'),'buildings_name')