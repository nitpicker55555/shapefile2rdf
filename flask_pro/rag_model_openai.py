import json
import os

from openai import OpenAI

import numpy as np
import pandas as pd
from tqdm import tqdm
from geo_functions import *
from dotenv import load_dotenv
import ast
load_dotenv()
pd.set_option('display.max_rows', None)

#
os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")
client = OpenAI()
def get_embedding(text, model="text-embedding-3-small"):
   text = text.replace("\n", " ")
   try:
      embed=client.embeddings.create(input = [text], model=model).data[0].embedding
      return embed
   except Exception as e:
      raise Exception(text,'embedding get error',e)



def cosine_similarity(a, b):
   return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def build_vector_store(words_origin,label):
   words = [element for element in words_origin if element]
   vectors=[]
   with open(f'{label}_vectors.jsonl', 'a') as jsonl_file:
      for word in tqdm(words):
         vector = get_embedding(word)
         data = {'label': word, 'vector': list(vector)}
         jsonl_file.write(json.dumps(data) + '\n')
   # for i in tqdm(words):
   #       vectors.append(get_embedding(i))
   #
   # data = {
   #     'label': words,
   #     'vector': [list(vector) for vector in vectors]
   # }
   # df = pd.DataFrame(data)
   #
   # # 保存为 CSV 文件
   # df.to_csv(f'{label}_vectors.csv', index=False)
def calculate_similarity_openai(label,key_vector_template):
   key_vector = get_embedding(key_vector_template)
   df = pd.read_csv(f'{label}_vectors.csv')
   df['vector'] = df['vector'].apply(ast.literal_eval)

   df['cosine_similarity'] = df['vector'].apply(lambda v: cosine_similarity(np.array(v), key_vector))
   # print(df[['cosine_similarity', 'label']])

   filtered_df = df[df['cosine_similarity'] > 0.5]

   sorted_df = filtered_df.sort_values(by='cosine_similarity', ascending=False)
   labels_list = sorted_df['label'].tolist()
   return labels_list
# build_vector_store(ids_of_attribute('points','name'),'points_name')
# build_vector_store(ids_of_attribute('lines','name'),'lines_name')
# build_vector_store(ids_of_attribute('land','name'),'land_name')
# build_vector_store(ids_of_attribute('buildings','name'),'buildings_name')
# template="""Hauptsächlich Braunerde aus sandigem Lehm (Oberschicht) über Kalkstein, ideal für Erdbeeranbau mit ausreichender Feuchtigkeit und reich an Kalium."""
#
# template='greenary'
# key_vector=get_embedding('')
# print(calculate_similarity_openai('landuse', template))
# df = pd.read_csv('soil_vectors.csv')
# print(df['label'][81])
