import spacy

# 加载spaCy的英语模型
nlp = spacy.load('en_core_web_sm')


def find_negation(text):
    # 使用spaCy处理文本
    doc = nlp(text)

    # 检查是否有依存关系为'neg'的词
    for token in doc:
        if token.dep_ == 'neg':
            return True, token.text
    return False, None


# 示例句子
text1 = "buildings not in forest"
text2 = "I like apples."

negation1, word1 = find_negation(text1)
negation2, word2 = find_negation(text2)

print(f"Text: {text1}, Contains negation: {negation1}, Negation word: {word1}")
print(f"Text: {text2}, Contains negation: {negation2}, Negation word: {word2}")
