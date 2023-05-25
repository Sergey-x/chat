def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        val = getattr(row, column.name)
        d[column.name] = None if val is None else str(val)
    return d
