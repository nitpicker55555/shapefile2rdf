import subprocess,os

env = os.environ.copy()
print(os.environ['PATH'])
env['PATH'] += os.pathsep + r"C:\Users\Morning\Downloads\apache-jena-4.9.0\bat"
env['PATH'] += os.pathsep + r"C:\Users\Morning\Downloads\apache-jena-4.9.0\bin"
env['JENA_HOME']=r"C:\Users\Morning\Downloads\apache-jena-4.9.0"
print(os.pathsep )
def get_multiline_input():
    print("input:")
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def save_to_file(content, filename):
    with open(filename, 'w') as file:
        file.write(content)


def query_tdb(database_path, sparql_query_file):
    cmd = [
        r"C:\Users\Morning\Downloads\apache-jena-4.9.0\bat\tdb2_tdbquery.bat",
        "--loc=" + database_path,
        "--query=" + database_path+"\\"+sparql_query_file
    ]
    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True,env=env)
    print(result.stdout)
def random_search():
    from SPARQLWrapper import SPARQLWrapper, JSON

    sparql = SPARQLWrapper("http://localhost:3030/ds/query")

    # 示例SPARQL查询，可以根据您的需要修改
    while True:
        query=get_multiline_input()
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:

            print(result)


def main():
    while True:
        sparql_query = get_multiline_input()
        save_to_file(sparql_query, "temp_query.sparql")

        database_path = r'C:\Users\Morning\Desktop\hiwi\ontop\ttt'
        query_tdb(database_path, "temp_query.sparql")


if __name__ == "__main__":
    random_search()
