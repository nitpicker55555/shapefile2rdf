import shapefile
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

GEO = Namespace("http://www.opengis.net/ont/geosparql#")

def shapefile_to_ttl(shapefile_path, output_ttl_path):


    sf = shapefile.Reader(shapefile_path)


    g = Graph()
    g.bind("geo", GEO)

    # Process Shapefile
    for record, shape in zip(sf.records(), sf.shapes()):
        feature_uri = URIRef(f"http://example.org/data/{record.oid}")


        geometry_as_wkt = shape.__geo_interface__['type'].upper() + " " + str(shape.__geo_interface__['coordinates']).replace(",", "")
        g.add((feature_uri, GEO.asWKT, Literal(geometry_as_wkt)))


        for field_name, value in zip(sf.fields[1:], record):
            predicate_uri = URIRef(f"http://example.org/property/{field_name[0].lower()}")
            g.add((feature_uri, predicate_uri, Literal(value)))

    prj_path = shapefile_path + ".prj"
    try:
        with open(prj_path, 'r') as prj_file:
            prj_content = prj_file.read()
            g.add((feature_uri, RDFS.comment, Literal(prj_content)))
    except FileNotFoundError:
        pass

    # Serialize graph to TTL
    g.serialize(destination=output_ttl_path, format="turtle")

shapefile_path = r"C:\Users\Morning\Downloads\oberbayern-latest-free.shp\gis_osm_landuse_a_free_1"  # e.g., 'C:/path_to_file/filename' without .shp
output_ttl_path = 'osm_land_use2.ttl'
shapefile_to_ttl(shapefile_path, output_ttl_path)



"""
PREFIX ns1: <http://example.org/property/>

SELECT DISTINCT ?nutzartType WHERE {
    ?subject ns1:nutzart ?nutzartType .
}
"""
