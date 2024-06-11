import spacy

# 加载英文模型
nlp = spacy.load('en_core_web_sm')

# 输入句子
sentence = "I want to know which land is university and named technisch"

# 处理句子
doc = nlp(sentence)

# 输出每个词和它的词性
for token in doc:
    print(f"{token.text}: {token.pos_}")
