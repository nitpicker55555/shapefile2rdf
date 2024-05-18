def extract_code_blocks(code_str):
    code_blocks = []
    parts = code_str.split("```python")
    for part in parts[1:]:  # 跳过第一个部分，因为它在第一个代码块之前
        code_block = part.split("```")[0]
        code_blocks.append(code_block)
    return code_blocks
example_str = """
Here is some text.

```python
def hello_world():
    print("Hello, world!")
```
```python
def hello_world():
    print("Hello, world!")
```
"""
for i in extract_code_blocks(example_str):
    print(i)