def reorder_relations(relations):
    for relation in relations:
        if 0 not in (relation['head'], relation['tail']):
            break
    else:
        # 0 simultaneously exists in all dictionaries
        return relations

    reordered_relations = []
    zero_relation = None
    for relation in relations:
        if 0 in (relation['head'], relation['tail']):
            zero_relation = relation
        else:
            reordered_relations.append(relation)

    if zero_relation:
        reordered_relations.append(zero_relation)

    return reordered_relations

spatial_relations = [
    {"type": "on", "head":3, "tail": 1},

]

print(reorder_relations(spatial_relations))
