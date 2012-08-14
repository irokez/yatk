import re
import math
import pickle
from collections import Counter

re_not_word = re.compile('^-+$')

def tokenize(text):
	return [word for word in re.split('[^\w\-]+', text) if len(word) > 0 and not re_not_word.match(word)]

def ngrams(words, order, sep=' '):
	return [sep.join(words[n - order : n]) for n in range(order, len(words))]

def ngrams_neg(words, n, negatives = set()):
	ngrams = []

	if len(negatives):
		for i in range(0, len(words) - n + 1):
			ngram_words = []
			j = 0
			while len(ngram_words) < n and len(words) > i + j:
				word = words[i + j]
				if word in negatives:
					j += 1
					if len(words) > i + j:
						word += '+' + words[i + j]
				ngram_words.append(word)
				j += 1
	
			if len(words) > i + j and words[i + j] in negatives:
				ngram_words[-1] += '+' + words[i + j]
			
			ngrams.append(' '.join(ngram_words))
				
	else:
		for l in range(n, len(words)):
			ngram = ' '.join(words[l - n : l])
			ngrams.append(ngram)
		
	return ngrams

def avg(values):
	return sum(values) / len(values)

def var(values, unbiased = False):
	av = avg(values)
	vr = 0
	for i in values:
		vr += (av - i) ** 2

	return vr / (len(values) - unbiased)

def sd(values):
	return math.sqrt(var(values))

accents = {
	'à': 'a', 'â': 'a', 
	'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e', 
	'ï': 'i', 
	'ô': 'o', 
	'ù': 'u', 'û': 'u', 'ü': 'u',
	'ÿ': 'y',
	'ç': 'c',
	'À': 'A', 'Â': 'A', 
	'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E', 
	'Ï': 'I', 
	'Ô': 'O', 
	'Ù': 'U', 'Û': 'U', 'Ü': 'U',
	'Ÿ': 'Y',
	'Ç': 'C'
}
def remove_accents(str):
	for accent in accents:
		str = str.replace(accent, accents[accent])
	return str

class BaseIndex:
	_weight_functions = {}
	_features_functions = {}
	_features_functions_prep = {}
	
	_index = {}
	
	def __init__(self, weight = None, features = None):
		self.set_weight_function(weight)
		self.set_features_function(features)

	def save(self, path):
		f = open(path, 'wb')
		pickle.dump(self, f)
		f.close()
	
	@staticmethod
	def load(path):
		f = open(path, 'rb')
		obj = pickle.load(f)
		f.close()
		return obj		
	
	def build(self, items):
		pass
		
	def set_weight_function(self, weight):
		if weight in self._weight_functions:
			self._weight_function = self._weight_functions[weight]
		else:
			print('Wrong weight function')
			exit()
			
	def weight(self, features):
		return dict([(feature, self._weight_function(feature, count)) for feature, count in features.items()])
	
	def set_features_function(self, features):
		if features in self._features_functions:
			self._features_function = self._features_functions[features]
			if features in self._features_functions_prep:
				self._features_function_prep = self._features_functions_prep[features]
			else:
				self._features_function_prep = self._features_function
		else:
			print('Wrong features function')
			exit()		
	
	def features(self, item):
		return self._features_function(item)
	
	def features_prep(self, item):
		return self._features_function_prep(item)

class NgramIndex(BaseIndex):
	def __init__(self, weight = None, features = None):	
		
		self._weight_functions['bin'] = self.weight_bin
		self._weight_functions['bin_norm'] = self.weight_bin_norm
		
		self._features_functions['unigram'] = self.features_unigrams
		self._features_functions['bigram'] = self.features_bigrams
		self._features_functions['bogram'] = self.features_bograms
		
		BaseIndex.__init__(self, weight, features)
	
	def build(self, items):
		#if self._weight_function == self.weight_bin:
		#	return
		
		data = {}
		
		for item in items:
			ngrams = self.features_prep(item)
			for ngram, count in ngrams.items():
				if ngram not in data:
					data[ngram] = {
						'df': 0,
						'tf': [],
					}
					
				data[ngram]['df'] += 1
				data[ngram]['tf'].append(count)
				
		for ngram in data:
			data[ngram]['tf_avg'] = avg(data[ngram]['tf'])
			
		self._index = data
		
	def weight_bin(self, ngram, count):
		return 1
	
	def weight_bin_norm(self, ngram, count):
		return 1 / self._index[ngram]['tf_avg'] if ngram in self._index else 0
	
	def features_unigrams(self, item):
		return self.features_ngrams(item, 1)
	
	def features_bigrams(self, item):
		return self.features_ngrams(item, 2)

	def features_bograms(self, item):
		return self.features_unigrams(item) + self.features_bigrams(item)
	
	def features_ngrams(self, item, ngram_order):
		words = tokenize(self.get_text(item).lower())
		return Counter(ngrams(words, ngram_order))

	def get_text(self, item):
		pass

class SentimentIndex(NgramIndex):
	CLASS_POS = 'pos'
	
	def __init__(self, weight = None, features = None):
		self._n_pos = 0
		self._n_neg = 0
		
		self._weight_functions['delta'] = self.weight_delta_tfidf
		self._weight_functions['delta_norm'] = self.weight_delta_tfidf_norm
		
		NgramIndex.__init__(self, weight, features)
	
	def build(self, items):
		if self._weight_function == self.weight_bin:
			return
		
		data = {}
		n_pos = 0
		n_neg = 0
		
		for item in items:
			item_class = self.get_class(item)
			if item_class == self.CLASS_POS:
				n_pos += 1
				df_class = 'df_pos'
			else:
				n_neg += 1
				df_class = 'df_neg'
	
			ngrams = self.features_prep(item)
			for ngram, count in ngrams.items():
				if ngram not in data:
					data[ngram] = {
						'df': 0,
						'tf': [],
						'df_pos': 0,
						'df_neg': 0,
					}
					
				data[ngram]['df'] += 1
				data[ngram]['tf'].append(count)
				data[ngram][df_class] += 1
				
		for ngram in data:
			data[ngram]['tf_avg'] = avg(data[ngram]['tf'])
			
		self._index = data
		self._n_pos = n_pos
		self._n_neg = n_neg
		# print(len(self._index))
		
	def weight_delta_idf(self, ngram, count):
		return math.log((self._index[ngram]['df_pos'] + 0.5) / (self._index[ngram]['df_neg'] + 0.5)) if ngram in self._index else 0
	
	def weight_delta_tfidf(self, ngram, count):
		return count * self.weight_delta_idf(ngram, count)
	
	def weight_delta_tfidf_norm(self, ngram, count):
		return self.weight_delta_tfidf(ngram, count) / self._index[ngram]['tf_avg'] if ngram in self._index else 0
	
	def get_class(self, item):
		pass

	@staticmethod
	def load(path, weight, features):
		f = open(path, 'rb')
		obj = pickle.load(f)
		f.close()
		me = SentimentIndex(weight, features)
		me._index = obj['index']
		me._n_pos = obj['n_pos']
		me._n_neg = obj['n_neg']
		return me

	def save(self, path):
		f = open(path, 'wb')
		pickle.dump({'index': self._index, 'n_pos': self._n_pos, 'n_neg': self._n_neg}, f)
		f.close()
