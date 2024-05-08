def auto_add_conditions(sql_query):
    # 将 SQL 查询分割成多行
    lines = sql_query.splitlines()
    # 标记是否已经添加了 WHERE 子句
    where_added = False
    # 标记是否已经处理过 FROM 关键字的行
    from_processed = False
    # 准备存储处理后的 SQL 查询
    modified_query = []

    for line in lines:
        # 删除行首和行尾的空白字符
        stripped_line = line.strip()
        # 如果行是注释或空行，直接添加到结果中
        if stripped_line.startswith('--') or not stripped_line:
            modified_query.append(line)
            continue

        # 检查是否是 FROM 行或之后的行
        if 'FROM' in stripped_line.upper():
            modified_query.append(line)
            from_processed = True
        elif from_processed:
            # 检查行是否已经以 WHERE 或 AND 开始
            if not (stripped_line.upper().startswith('WHERE') or stripped_line.upper().startswith('AND')):
                # 如果还未添加 WHERE，则首个条件添加 WHERE，之后添加 AND
                if not where_added:
                    line = line.replace(stripped_line, 'WHERE ' + stripped_line)
                    where_added = True
                else:
                    line = line.replace(stripped_line, 'AND ' + stripped_line)
            modified_query.append(line)
        else:
            modified_query.append(line)
    if not modified_query[-1].strip().endswith(';'):
        modified_query[-1] += ';'
    # 将处理后的行合并回一个单一的字符串
    return '\n'.join(modified_query)

# 示例 SQL 查询
sql_example = """SELECT 'landuse' AS source_table, fclass, name, osm_id, geom
FROM landuse
ST_Intersects(geom, ST_MakeEnvelope(11.60877, 11.51839, 48.13934, 48.1579, 4326))
fclass = 'park'
name = 'TUM'"""

# 应用函数
modified_sql = auto_add_conditions(sql_example)
print(modified_sql)
