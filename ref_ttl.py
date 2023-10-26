from rdflib import Graph, URIRef
from rdflib.plugins.sparql.results.csvresults import CSVResultSerializer
from rdflib.plugins.sparql import prepareQuery
def sparql_query():
    g = Graph()
    g.parse("output2.ttl", format="turtle")
    #
    #
    # query = """
    # SELECT ?predicate (COUNT(?predicate) AS ?count) WHERE {
    #          ?subject ?predicate ?object.
    # } GROUP BY ?predicate
    # """
    #
    # results = g.query(query)
    #
    # for row in results:
    #     predicate = row[0]
    #     count = row[1]
    #     print(f"{predicate} {count}")
    """
    predicate: 8
    http://example.org/property/oid, 42241
    http://www.opengis.net/ont/geosparql#asWKT, 42241
    http://example.org/property/gml_id, 42241
    http://example.org/property/aktualit, 42241
    http://example.org/property/nutzart, 42241
    http://example.org/property/bez, 42241
    http://example.org/property/name, 42241
    http://www.w3.org/2000/01/rdf-schema#comment, 1
    """
    q = """
    SELECT ?shapeName WHERE {
        ?subject <http://example.org/data/name> ?shapeName.
    }
    """
    #
    # results = g.query(q)
    #
    # unique_shapes = set()
    #
    # for row in results:
    #     unique_shapes.add(row[0])
    # unique_shapes_list = list(unique_shapes)
    # print(unique_shapes_list[:5])
    # print(f"Number of unique shapes: {len(unique_shapes)}")
    """
    [rdflib.term.Literal(''), rdflib.term.Literal('Krottenkopfstraße'), rdflib.term.Literal('Walter-Schnackenberg-Weg'), rdflib.term.Literal('Marklandstraße'), rdflib.term.Literal('Undinestraße')]
    Number of unique shapes: 6338 
    """

    query = prepareQuery("""
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
        }
        LIMIT 30
    """)

    # 执行查询并打印结果

    for row in g.query(query):
        print(row)

    """
    #{idx}是在Shapefile中的索引或ID。
    #对应的几何类型asWKT
    #几何形状
    
    (rdflib.term.URIRef('http://example.org/data/32194'), rdflib.term.URIRef('http://example.org/data/name'), rdflib.term.Literal(''))
    (rdflib.term.URIRef('http://example.org/data/19485'), rdflib.term.URIRef('http://www.opengis.net/ont/geosparql#asWKT'), rdflib.term.Literal('POLYGON ((688882.9 5341178.93, 688883.41 5341183.14, 688888.01 5341186.85, 688889.16 5341192.16, 688889.05 5341191.35, 688889.08 5341190.52, 688889.24 5341189.7, 688889.54 5341188.93, 688889.96 5341188.23, 688890.5 5341187.59, 688891.12 5341187.05, 688891.83 5341186.63, 688892.6 5341186.32, 688893.41 5341186.15, 688918.13 5341182.93, 688942.3100000001 5341179.76, 688954.39 5341178.18, 688966.47 5341176.6, 688985.65 5341174.09, 688986.52 5341174.05, 688987.38 5341174.17, 688988.21 5341174.43, 688988.97 5341174.83, 688989.66 5341175.37, 688990.25 5341176.01, 688990.72 5341176.74, 688991.05 5341177.54, 688991.23 5341178.39, 688989.58 5341164.97, 688987.2 5341165.29, 688984.64 5341165.62, 688890.76 5341177.9, 688882.9 5341178.93))'))
    (rdflib.term.URIRef('http://example.org/data/32111'), rdflib.term.URIRef('http://www.opengis.net/ont/geosparql#asWKT'), rdflib.term.Literal('POLYGON ((693771.27 5335411.51, 693772.38 5335441.44, 693773.24 5335464.15, 693774.28 5335492.62, 693796.53 5335491.45, 693811.77 5335490.64, 693836 5335489.32, 693845.0699999999 5335488.9, 693859.1800000001 5335488.67, 693888.78 5335488.19, 693889.89 5335457.78, 693890.26 5335446.87, 693890.5699999999 5335433.48, 693891.4300000001 5335405.16, 693864.97 5335406.34, 693835.5 5335407.65, 693807.5 5335408.9, 693772.52 5335410.46, 693771.98 5335410.62, 693771.6 5335410.94, 693771.4300000001 5335411.09, 693771.27 5335411.51))'))
    (rdflib.term.URIRef('http://example.org/data/9538'), rdflib.term.URIRef('http://example.org/data/bez'), rdflib.term.Literal('Grünland'))
    (rdflib.term.URIRef('http://example.org/data/34621'), rdflib.term.URIRef('http://www.opengis.net/ont/geosparql#asWKT'), rdflib.term.Literal('POLYGON ((693868.39 5335180.63, 693897.38 5335181.4, 693897.8100000001 5335165.42, 693898.26 5335149.42, 693893.39 5335149.29, 693868.76 5335148.65, 693868.58 5335164.64, 693868.39 5335180.63))'))
    
    """
    # query = """
    # SELECT (COUNT(?subject) AS ?count)
    # WHERE {
    #   ?subject ?predicate ?object .
    # }
    # """
    #
    # # 执行查询
    # result = g.query(query)
    #
    # # 输出查询结果
    # for row in result:
    #     print(f"Number of distinct subjects: {row['count']}")
    """
    Number of distinct subjects:  337928  /  295688
    """
def intersect():
    g = Graph()
    g.parse("output2.ttl", format="turtle")


    query = """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>

SELECT ?feature WHERE {
  ?feature geo:hasGeometry ?geometry .
  ?geometry a geo:Polygon .
}

    """

    # 执行查询
    result = g.query(query)

    # 输出查询结果
    for row in result:
        print(row)
    """
    Number of distinct subjects:  337928
    """
def shape_analyse():
    import shapefile


    sf = shapefile.Reader(r"C:\Users\Morning\Downloads\tn_09162\Nutzung.shp")

    shape_count = len(sf.shapes())

    print(f"Total number of shapes: {shape_count}")
def repeat_query():
    g = Graph()
    g.parse(r"C:\Users\Morning\Desktop\hiwi\ttl_query\path_to_output.ttl", format="turtle")
    while True:
        try:
            print("Enter your SPARQL query (type 'END' on a new line to submit):")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)

            # 合并多行为单个查询字符串
            query = "\n".join(lines)

            # 如果用户只输入“exit”，则退出循环
            if query.strip().lower() == 'exit':
                break
            print(query)
            result = g.query(query)

            # 输出查询结果

            for row in result:
                print(', '.join(map(str, row)))
            print(len(result),": number of rows")
        except Exception as e:
            print(e)


            """
                    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        
        SELECT ?subject ?polygon
        WHERE {
            ?subject geo:asWKT ?polygon .
            FILTER(STRSTARTS(STR(?polygon), "POLYGON"))
        }
        LIMIT 30

            
            """
def osm_query():
    from SPARQLWrapper import SPARQLWrapper, JSON

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    sparql.setQuery("""
        SELECT ?subject ?predicate ?object WHERE {
            ?subject ?predicate ?object
        } LIMIT 5
    """)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        # 打印查询结果
        s = result["subject"]["value"]
        p = result["predicate"]["value"]
        o = result["object"]["value"]
        print(s, p, o)
repeat_query()

# osm_query()
# intersect()
# shape_analyse()

"""
PREFIX ns1: <http://example.org/property/>

SELECT DISTINCT ?oidType WHERE {
    ?subject ns1:oid ?oidType .
}
"""