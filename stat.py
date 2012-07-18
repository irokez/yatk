import math

def t_paired(list1, list2):
	n = len(list1)
	diff = [list1[i] - list2[i] for i in range(0, n)]
	s = sd(diff, True)
	#print(list1, sd(list1, True), avg(list1))
	#print(list2, sd(list2, True), avg(list2))
	t = avg(diff) / s / math.sqrt(n) if s != 0 else 0
	return t
	
def avg(values):
	return sum(values) / len(values)

def var(values, unbiased = False):
	av = avg(values)
	vr = 0
	for i in values:
		vr += (av - i) ** 2

	return vr / (len(values) - unbiased)

def sd(values, unbiased = False):
	return math.sqrt(var(values, unbiased))