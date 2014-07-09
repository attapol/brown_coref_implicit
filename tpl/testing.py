
def assert_lt(x, y):
	assert x < y, 'Expected less than %s. Got %s' % (y, x)

def assert_le(x, y):
	assert x <= y, 'Expected less than or equal to %s. Got %s' % (y, x)

def assert_gt(x, y):
	assert x > y, 'Expected greater than %s. Got %s' % (y, x)

def assert_ge(x, y):
	assert x >= y, 'Expected greater than or equal to %s. Got %s' % (y, x)

def assert_eq(x, y):
	assert x == y, 'Expected %s. Got %s' % (x, y)
