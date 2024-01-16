import json

import rdflib
import numpy as np

# Assuming the TTL file is available and named 'data.ttl'
# Parsing the TTL file
def read_ttl():
    g = rdflib.Graph()
    g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\ttl_file\Moore_Bayern.ttl", format="ttl")

    # Fetching all values of the 'fcclass' property
    fcclass_values = []
    for s, p, o in g:
        if p.endswith('kategorie'):
            fcclass_values.append(str(o))
    print(len(fcclass_values))
    # Convert the set to a list for JSON serialization
    with open("kategorie2.json", "w") as json_file:
        json.dump(list(fcclass_values), json_file)
def read_list():
    import json

    def read_fcclass_values(json_file_path):
        """
        读取存储在JSON文件中的fcclass值列表。

        参数:
        json_file_path (str): JSON文件的路径。

        返回:
        list: 从JSON文件中读取的fcclass值列表。
        """
        with open(json_file_path, "r") as file:
            fcclass_values = json.load(file)
        return fcclass_values

    # 使用函数
    no_repeat=set()
    fcclass_list = read_fcclass_values("kategorie2.json")
    for i in fcclass_list:
        no_repeat.add(i)
    print(len(no_repeat))
    print(no_repeat)
def get_emb():

    import openai
    from sklearn.cluster import DBSCAN
    import numpy as np
    # 设置您的 OpenAI API 密钥
    openai.api_key = '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'

    def text_to_vector(text):
        response = openai.Embedding.create(
            input=text,
            engine="text-similarity-babbage-001"  # 您可以根据需要选择不同的模型
        )
        return response['data'][0]['embedding']

    # 示例文本标签列表
    # text_labels = ["cat", "dog", "animal", "computer", "laptop", "pet"]

    # 向量化所有标签
    # vectors = [text_to_vector(label) for label in text_labels]
    # 示例文本标签列表
    text_labels = ['gpt3.5', 'openai', 'microsoft', 'England', 'woman', 'sex', 'traffic accident', 'murder',
                   'Apple company', 'man', 'life', 'discrimination', 'sexual abuse']
    # text_labels = ["cat", "dog", "animal", "computer", "laptop", "pet","gpt","gpt-4","gpt3.5","openai","microsoft","usa","USA","china","England","india","woman","sex","traffic accident","murder","Apple company","man","life","discrimination","sexual abuse"]
    vectors = [text_to_vector(label) for label in cleaned_words]
    np.save('vectors.npy', vectors)
def get_similarword():
    loaded_array_txt = np.load('embedding_array.txt')
    loaded_array_csv = np.loadtxt('embedding_array.csv', delimiter=',')


read_ttl()
read_list()