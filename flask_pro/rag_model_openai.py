import os

from openai import OpenAI

import numpy as np
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
import ast
load_dotenv()
pd.set_option('display.max_rows', None)

#
os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")
client = OpenAI()
def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding


def cosine_similarity(a, b):
   return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def build_vector_store(words_origin,label):
   words = [element for element in words_origin if element]
   vectors=[]
   for i in tqdm(words):
         vectors.append(get_embedding(i))

   data = {
       'label': words,
       'vector': [list(vector) for vector in vectors]
   }
   df = pd.DataFrame(data)

   # 保存为 CSV 文件
   df.to_csv(f'{label}_vectors.csv', index=False)
def calculate_similarity_openai(label,key_vector):
   df = pd.read_csv(f'{label}_vectors.csv')
   df['vector'] = df['vector'].apply(ast.literal_eval)

   df['cosine_similarity'] = df['vector'].apply(lambda v: cosine_similarity(np.array(v), key_vector))
   filtered_df = df[df['cosine_similarity'] > 0.6]

   sorted_df = filtered_df.sort_values(by='cosine_similarity', ascending=False)
   labels_list = sorted_df['label'].tolist()
   return labels_list

# template="""Hauptsächlich Braunerde aus sandigem Lehm (Oberschicht) über Kalkstein, ideal für Erdbeeranbau mit ausreichender Feuchtigkeit und reich an Kalium."""

# key_vector=get_embedding(template)
# print(calculate_similarity('soil', key_vector))
# df = pd.read_csv('soil_vectors.csv')
# print(df['label'][81])