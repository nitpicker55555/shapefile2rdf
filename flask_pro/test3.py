import spacy

# 加载英语模型
nlp = spacy.load("en_core_web_sm")

# 示例文本
text = "buildings for commercial in landuse which is forest"

# 解析文本
doc = nlp(text)


def find_noun_modifier(token):
    # 递归寻找介词修饰的名词
    head = token.head
    while head.pos_ not in ['NOUN', 'PROPN'] and head.head != head:
        if head.pos_ in ['VERB', 'ADJ']:  # 如果是动词或形容词，可能需要向上追溯更多
            head = head.head
        else:
            break
    return head.text if head.pos_ in ['NOUN', 'PROPN'] else 'No clear noun'


# 遍历文档中的每个令牌
for token in doc:
    if token.pos_ == 'ADP' and token.dep_ == 'prep':
        # 收集整个介词短语的完整文本
        phrase = ' '.join([t.text for t in token.subtree])
        # 找到与介词直接关联的名词（介词宾语）
        pobj = [child for child in token.children if child.dep_ == 'pobj']
        if pobj:
            pobj = pobj[0].text  # 取第一个pobj作为主要宾语
        else:
            pobj = "No direct object"

        # 寻找介词修饰的名词
        head_noun = find_noun_modifier(token)

        print(f"Geographical relation: {phrase}, Modifying noun: {head_noun}")
