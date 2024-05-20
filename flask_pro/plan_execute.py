def format_sql_query(names):
    formatted_names = []
    for name in names:
        # Replace single quote with two single quotes for SQL escape
        formatted_name = name.replace("'", "''")
        # Wrap the name with single quotes
        formatted_name = f"'{formatted_name}'"
        formatted_names.append(formatted_name)

    # Join all formatted names with a comma
    formatted_names_str = ", ".join(formatted_names)
    return f"({formatted_names_str})"
names = ['Schlichtner Lake', "Lake O' Mio"]
sql_query = format_sql_query(names)
print(sql_query)