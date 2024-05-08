import spacy


def remove_prep_and_extract_location(text):
    # 加载 spaCy 的英语模型
    nlp = spacy.load("en_core_web_sm")

    # 处理文本
    doc = nlp(text)

    # 存储地名的起始和结束索引
    start_index = None
    end_index = None

    # 找到地名的起始和结束索引
    for i, token in enumerate(doc):
        if token.ent_type_ == "GPE":
            if start_index is None:
                start_index = i
            end_index = i

    # 如果找到了地名，则删除地名及其前面的介词
    if start_index is not None and end_index is not None:
        # 提取地名
        location = doc[start_index:end_index + 1].text
        # 删除地名及其前面的介词
        while start_index > 0 and doc[start_index - 1].pos_ == "ADP":
            start_index -= 1
        updated_text = doc[:start_index].text + doc[end_index + 1:].text
        return location, updated_text.strip()
    else:
        return None, text.strip()


# 测试函数
text = "I want to know park around residential area in Augsburg"
location, updated_text = remove_prep_and_extract_location(text)
print("Location:", location)
print("Updated Text:", updated_text)
