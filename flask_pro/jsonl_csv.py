import json
import csv

def jsonl_to_csv(jsonl_file, csv_file):
    with open(jsonl_file, 'r', encoding='utf-8') as infile, open(csv_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        first_line = True
        for line in infile:
            data = json.loads(line)['answers']
            if first_line:
                header = data.keys()
                writer.writerow(header)
                first_line = False
            writer.writerow(data.values())

# 使用示例
jsonl_to_csv(r"C:\Users\Morning\Desktop\responses.jsonl", 'result.csv')
