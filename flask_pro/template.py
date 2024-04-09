
"""
"PREFIX ns1: <http://example.org/property/>
PREFIX
geo: < http: // www.opengis.net / ont / geosparql  # >
PREFIX
geof: < http: // www.opengis.net / >


def /function / geosparql / >
SELECT ?building ?neighbor
WHERE
{
# 找到所有fclass为building的建筑物
?building
ns1: fclass
""
building
"".
?building
geo: asWKT ?buildingWKT.

# 找到所有uebk25_k为77, 78, 78a的实体
?neighbor
ns1: uebk25_k ?uebk25_k.
    FILTER(?uebk25_k
IN(""
77
"", ""
78
"", ""
78
a
""))
?neighbor
geo: asWKT ?neighborWKT.

    # 检查建筑物和相应实体是否相邻
    FILTER(geof: sfTouches(?buildingWKT, ?neighborWKT))
}"
"PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/>
PREFIX
ns1: < http: // example.org / property / >
PREFIX
geo: < http: // www.opengis.net / ont / geosparql  # >
PREFIX
geof: < http: // www.opengis.net /


def /function / geosparql / >


SELECT ?buildingWKT
WHERE
{
    # 定义我们感兴趣的区域（bounding box）
    BIND(""
POLYGON(
    (11.5971976 48.2168632, 11.6851890 48.2168632, 11.6851890 48.2732260, 11.5971976 48.2732260, 11.5971976 48.2168632))
"" ^ ^ geo: wktLiteral
AS ?bbox).

# 找到所有fclass为forest的森林区域，并且位于bounding box内
?forest
ns1: fclass
""
forest
"".
?forest
geo: asWKT ?forestWKT.
    FILTER(geof: sfWithin(?forestWKT, ?bbox))

# 找到所有fclass为building的建筑物
?building
ns1: fclass
""
building
"".
?building
geo: asWKT ?buildingWKT.

    # 确保建筑物至少位于一个fclass为forest的森林区域之内
    FILTER(geof: sfWithin(?buildingWKT, ?forestWKT))
}"
"PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/>
PREFIX
ns1: < http: // example.org / property / >
PREFIX
geo: < http: // www.opengis.net / ont / geosparql  # >
PREFIX
geof: < http: // www.opengis.net /


def /function / geosparql / >


SELECT ?buildingWKT
WHERE
{
    # 定义我们感兴趣的区域（bounding box）
    BIND(""
POLYGON(
    (11.5971976 48.2168632, 11.6851890 48.2168632, 11.6851890 48.2732260, 11.5971976 48.2732260, 11.5971976 48.2168632))
"" ^ ^ geo: wktLiteral
AS ?bbox).

# 找到所有fclass为forest的森林区域，并且位于bounding box内
?forest
ns1: fclass
""
forest
"".
?forest
geo: asWKT ?forestWKT.
    FILTER(geof: sfWithin(?forestWKT, ?bbox))

# 为这些森林区域创建100米的缓冲区
BIND(geof: buffer(?forestWKT, 1, uom: metre) AS ?forestBufferWKT)

# 找到所有fclass为building的建筑物
?building
ns1: fclass
""
building
"".
?building
geo: asWKT ?buildingWKT.

    # 检查这些建筑物是否位于森林的100米缓冲区内
    FILTER(geof: sfIntersects(?buildingWKT, ?forestBufferWKT))
}"

"PREFIX uom: <http://www.opengis.net/def/uom/OGC/1.0/>
PREFIX
ns1: < http: // example.org / property / >
PREFIX
geo: < http: // www.opengis.net / ont / geosparql  # >
PREFIX
geof: < http: // www.opengis.net /


def /function / geosparql / >


SELECT ?forest(geof: sfArea(?forestWKT) AS ?area)
WHERE
{
?forest
ns1: fclass
""
forest
"".
?forest
geo: asWKT ?forestWKT.
}
ORDER
BY
DESC(?area)
LIMIT
10
"
"PREFIX ns1: <http://example.org/property/>

SELECT ?element
WHERE
{
?element
ns1: uebk25_k ?uebk25_k.
    FILTER(?uebk25_k
IN(""
75
"", ""
75
c"", ""
79
"", ""
61
a
""))
}"
"PREFIX ns1: <http://example.org/property/>
PREFIX
geo: < http: // www.opengis.net / ont / geosparql  # >
PREFIX
geof: < http: // www.opengis.net /


def /function / geosparql / >


SELECT
DISTINCT ?name
WHERE
{
    # 定义我们感兴趣的区域（bounding box）
    BIND(""
POLYGON(
    (11.5971976 48.2168632, 11.6851890 48.2168632, 11.6851890 48.2732260, 11.5971976 48.2732260, 11.5971976 48.2168632))
"" ^ ^ geo: wktLiteral
AS ?bbox).

?element
ns1: fclass
""
building
"".
?element
geo: asWKT ?wkt.

    # 检查元素是否在边界框内
    FILTER(geof: sfWithin(?wkt, ?bbox))

# 获取元素的名称
?element
ns1: type ?name.
}
ORDER
BY ?name
"


"""