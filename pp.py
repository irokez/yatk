import sys
 
def print_table(data, outfile = sys.stdout, maxlen = {}):
	vsep = '|'
	endl = '\n'
	s = ''
	
	keys = []
	maxkey = 0
	for rowkey, row in data.items():
		l = len(str(rowkey))
		if l > maxkey:
			maxkey = l
		for key in row:
			if key not in keys:
				keys.append(key)
			l = len(str(row[key]))
			if key not in maxlen or l > maxlen[key]:
				maxlen[key] = l
		
	for key in keys:
		l = len(str(key))
		if l > maxlen[key]:
			maxlen[key] = l
		if maxlen[key] < 3:
			maxlen[key] = 3
			
	hline = '+' + '-' * maxkey + '+' + '+'.join(['-' * maxlen[key] for key in keys]) + '+'

	s += endl + hline + endl
	s += vsep
	s += ' ' * maxkey
	s += vsep
	s += vsep.join([str(key).ljust(maxlen[key]) for key in keys])
	s += vsep
	s += endl + hline + endl
	
	for rowkey, row in data.items():
		s += vsep
		s += str(rowkey).ljust(maxkey)
		s += vsep
		s += vsep.join([str(row[key] if key in row else '').rjust(maxlen[key]) for key in keys])
		s += vsep
		s += endl + hline + endl
			
	print(s, file=outfile)
	return maxlen

class XmlWriter:
	PADDING = '\t'
	ENDL = '\n'
	
	def __init__(self, file=sys.stdout, encoding='utf-8'):
		self._str = ''
		self._pad = 0
		self._encoding = encoding
		self._no_cdata = False
		self._file = file
		
	def add(self, s, *args):
		line = ''
		for i in range(0, self._pad):
			line += self.PADDING
		
		line += s#.format(*args)
		line += self.ENDL
		print(line, file=self._file, end='')
		
	def open(self, tag, *args, **kwargs):
		s = '<' + tag
		for name in kwargs:
			s += ' ' + name.replace('__', ':') + '="' + str(kwargs[name]) + '"'
		s += '>'
		self.add(s)
		self._pad += 1
		
	def content(self, tag, content, *args, **kwargs):
		s = '<' + tag
		for name in kwargs:
			s += ' ' + name.replace('__', ':') + '="' + str(kwargs[name]) + '"'
			
		if not self._no_cdata:
			s += '><![CDATA[' + str(content) + ']]></' + tag + '>'
		else:
			s += '>' + str(content) + '</' + tag + '>'
		self.add(s)
		
	def empty(self, tag, *args, **kwargs):
		s = '<' + tag
		for name in kwargs:
			s += ' ' + name.replace('__', ':') + '="' + kwargs[name] + '"'
		s += ' />'
		self.add(s)
		
	def close(self, tag):
		self._pad -= 1
		self.add('</{0}>'.format(tag))
		
#	def last(self, tag):
#		self._str += '</{0}>'.format(tag)

	def header(self):
		print('<?xml version="1.0" encoding="{0}"?>'.format(self._encoding), file=self._file, end=self.ENDL)
	
	def write(self):
		return '<?xml version="1.0" encoding="{0}"?>'.format(self._encoding) + self.ENDL + self._str
	
	def __repr__(self):
		return self.write()
	
	def __str__(self):
		return self.write()
	