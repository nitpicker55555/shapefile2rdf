from SPARQLWrapper import SPARQLWrapper, JSON
import json


def run_query(endpoint_url, query):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    response = sparql.query().convert()

    # 检查响应是否为字节对象，并在必要时解码为字符串
    if isinstance(response, bytes):
        response = response.decode('utf-8')
        response = json.loads(response)

    for result in response["results"]["bindings"]:
        print(result)


if __name__ == "__main__":
    # Fuseki服务器的SPARQL端点URL
    endpoint_url = "http://localhost:8082/sparql"

    # SPARQL查询示例
    query = """
PREFIX : <http://cui.unige.ch/citygml/2.0/>
PREFIX bldg: <http://www.opengis.net/citygml/building/2.0/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX lgdo: <http://linkedgeodata.org/ontology/>

# Q1: Get all hotels over 30m high
SELECT *
{
?linkage a :Association_CityGML_OSM .
?linkage :matchesOSM ?osmentity .
?linkage :matchesCityGML/:mapSurface/bldg:bounds ?citygmlentity .
?osmlinkage a :Association_OSM_Class .
?osmlinkage :hasosmid ?osmentity .
?osmlinkage :hasosmclassid ?osmclassname .
?osmclassname a lgdo:Hotel .
    OPTIONAL { ?osmentity rdfs:label ?hotelname .}
?citygmlentity bldg:measuredHeight ?buildingHeight .
FILTER(?buildingHeight > 30) .
?citygmlentity bldg:lod2Solid ?solid .
?solid geo:asWKT ?address_geom .
}

    """

    run_query(endpoint_url, query)
