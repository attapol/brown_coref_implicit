"""Utility functions for using sqlite3

%s can be get awkward pretty fast. 
Using dictionary can be more convenient.

"""
def insert_row(cursor, table_name, row_dict):
	# XXX table_name not sanitized
	# XXX test for allowed keys is case-sensitive
	# filter out keys that are not column names
	cursor.execute('pragma table_info(%s)' % table_name)
	allowed_keys = set(column[1] for column in cursor.fetchall())
	keys = allowed_keys.intersection(row_dict)
	if len(row_dict) > len(keys):
		unknown_keys = set(row_dict) - allowed_keys
		print >> sys.stderr, "skipping keys:", ", ".join(unknown_keys)
	columns = ", ".join(keys)
	values_template = ", ".join(["?"] * len(keys))

	sql = "INSERT OR REPLACE INTO %s (%s) VALUES (%s)" % \
		(table_name, columns, values_template)
	values = tuple(row_dict[key] for key in keys)
	cursor.execute(sql, values)


def insert_rows(cursor, table_name, row_dict_list):
	"""INSERT INTO table_name (_) VALUES (_)

	Convenience function for inserting a bunch of rows
	Rows must be dictionaries

	Note that table_name not sanitized
	and we assume that row_dict is well-formed
	"""
	keys = row_dict_list[0].keys()
	columns = ", ".join(keys)
	values_template = ", ".join(["?"] * len(keys))

	sql = "INSERT INTO %s (%s) VALUES (%s)" % \
		(table_name, columns, values_template)
	tuples = [tuple(row_dict[key] for key in keys) for row_dict in row_dict_list]
	cursor.executemany(sql, tuples)

def convert_sqlite_row_to_dict(sqlite_row):
	row_dict = {}
	for key in sqlite_row.keys():
		row_dict[key] = sqlite_row[key]
	return row_dict
