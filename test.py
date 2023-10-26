
import shapefile
from shapely.geometry import shape as Shape
from rdflib import Graph, Literal, Namespace, RDF, URIRef

# Setting base namespaces
GEO = Namespace("http://www.opengis.net/ont/geosparql#")
EX = Namespace("http://example.org/data/")

# Read Shapefile
shp_path = r"C:\Users\Morning\Downloads\tn_09162\Nutzung.dbf"
sf = shapefile.Reader(shp_path)

# Create a new RDF graph
g = Graph()
g.bind("geo", GEO)
g.bind("ex", EX)

# Loop through each record in the Shapefile and convert it to RDF triples
for idx, (shp, record) in enumerate(zip(sf.shapes(), sf.records())):
    feature_uri = URIRef(f"http://example.org/data/{idx}")  # Use idx as unique identifier

    geom = Shape(shp)
    wkt_literal = Literal(geom.wkt)

    # You can add type-specific handling if needed, but for now, we'll generalize
    g.add((feature_uri, RDF.type, GEO[geom.geometryType()]))
    g.add((feature_uri, GEO["asWKT"], wkt_literal))

    # Add other attributes
    for i, field in enumerate(sf.fields[1:]):
        prop_uri = URIRef(f"http://example.org/data/{field[0]}")
        g.add((feature_uri, prop_uri, Literal(record[i])))

# Serialize the graph as a Turtle file
g.serialize(destination="output2.ttl", format="turtle")

