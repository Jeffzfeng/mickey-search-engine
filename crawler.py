# Copyright (C) 2011 by Peter Goodman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import urllib2
import urlparse
#from bs4 import BeautifulSoup
#from bs4 import Tag
import unicodedata
from BeautifulSoup import *
from collections import defaultdict
import re
from collections import defaultdict
import numpy as np
import redis
import pickle

server = redis.Redis('52.14.224.74')

def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')

class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        #cache of urls
        self._url_queue = [ ]
        #dictionary which uses url as key and doc id as return value
        self._doc_id_cache = { }
        #dictionary which uses word as key and word id as  return value
        self._word_id_cache = { }

    	""" -- Objects added for Lab 1 start -- """
    	#dictionary which uses doc id as key and returns url as value
    	self._doc_str_cache = { }
    	#dictionary which uses word id as key and returns word as value
    	self._word_str_cache = { }
    	#need 2-D dictionary, which uses wordID as key and set of docID as value
        self._mapping_word_id_to_doc_id = { }
        #need 2-D dictionary, which uses word as key and set of url as value
        self._mapping_word_str_to_doc_str = { } 
      	""" -- Objects added for Lab 1 end -- """
        
        """ -- Objects added for lab 3 start -- """
        # new list to hold list of links (from, to)
        self.links = []
        
        #new list to hold list of word to url with page rank
        self.word_to_url_list = { }
        
        """ -- Objects added for lab 3 end -- """
        
        """ -- Objects added for lab 4 start -- """

        self.title_dict = { }
        
        self.description_dict = { }

        self.p_dict = { }

        """ -- Objects added for lab 4 end -- """

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)
            
        def visit_description(*args, **kargs):
            self._visit_description(*args, **kargs)
            self._increase_font_factor(5)(*args, **kargs)
            
        def visit_paragraph(*args, **kargs):
            self._visit_paragraph(*args, **kargs)
            self._increase_font_factor(1)(*args, **kargs)
        

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title
        self._enter['meta'] = visit_description
        self._enter['p'] = visit_paragraph

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)
        self._exit['meta'] = self._increase_font_factor(-5)
        self._exit['p'] = self._increase_font_factor(-1)
        

        # never go in and parse these tags
        self._ignored_tags = set([
            'script', 'link', 'embed', 'iframe', 'frame', 
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset', 
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        #used as keys for doc/word id
        self._next_doc_id = 1
        self._next_word_id = 1

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass
        
    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]
        doc_id = self._insert_document(url)
        self._doc_id_cache[url] = doc_id
        return doc_id
    
    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""
            
        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        new_link = (from_doc_id, to_doc_id)
        self.links.append(new_link)
    
    # need to add comments
    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        title_string = unicodedata.normalize('NFKD', title_text).encode('ascii', 'ignore')
        url = self._doc_str_cache[self._curr_doc_id]              
        if url not in self.title_dict:
            #server.rpush(url, title_string)
            self.title_dict[url] = title_string            
        print "document title="+ repr(title_text)

    # need to add comments 
    def _visit_description(self, elem):
        elem_string = str(elem)
        url = self._doc_str_cache[self._curr_doc_id]              
        if "content" in elem_string and "description" in elem_string and url not in self.description_dict:
            elem_string = re.search('(?<=content=").*', elem_string)
            elem_string = re.sub('".*', "", elem_string.group(0))
            #redis_desc_key = "desc: " + url
            if len(elem_string) > 150:
                cat_elem_string = elem_string[:150]
                cat_elem_string = cat_elem_string + '...'
                self.description_dict[url] = cat_elem_string
                #server.rpush(url, cat_elem_string)
            else:
                self.description_dict[url] = elem_string
                #server.rpush(url, elem_string)
                pass
              
    # need to add comments  
    def _visit_paragraph(self, elem):
        url = self._doc_str_cache[self._curr_doc_id]              
        p_text = self._text_of(elem).strip()
        if url not in self.description_dict:
            p_string = unicodedata.normalize('NFKD', p_text).encode('ascii', 'ignore')
            #redis_desc_key = "desc: " + url
            if len(p_string) > 150:
                cat_p_string = p_string[:150]
                cat_p_string = cat_p_string + '...'
                self.description_dict[url] = cat_p_string 
                #server.rpush(url, cat_p_string)
            else:
                self.description_dict[url] = p_string
                #server.rpush(url, p_string)
                pass
            
    def _visit_a(self, elem):
        """Called when visiting <a> tags."""
        dest_url = self._fix_url(self._curr_url, attr(elem,"href"))

        #print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))
        
        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        # TODO add title/alt/text to index for destination url
    
    def _add_words_to_document(self):
        # TODO: knowing self._curr_doc_id and the list of all words and their
        #       font sizes (in self._curr_words), add all the words into the
        #       database for this document
        print "    num words="+ str(len(self._curr_words))

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""
        def increase_it(elem):
            self._font_size += factor
        return increase_it
    
    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.word_id(word), self._font_size))
            self.add_doc_id(word)
           
    """ -- methods added for lab 1 start -- """

    def word_id(self, word):
        """Get the word id of some specific word."""
        if word in self._word_id_cache:
            return self._word_id_cache[word]
        word_id = self._insert_word(word)
        self._word_id_cache[word] = word_id
        self._mapping_word_id_to_doc_id[word_id] = set()
        return word_id

    def _insert_document(self, url):
        """A function that inserts a url into a document db table
        increments the doc id
        and then returns that newly inserted document's id."""
	self._doc_str_cache[self._next_doc_id] = url
	ret_id = self._next_doc_id
        self._next_doc_id += 1
        return ret_id
    
    def _insert_word(self, word):
        """A function that inserts a word into the lexicon db table,
        increments the word id
        and then returns that newly inserted word's id."""
	self._word_str_cache[self._next_word_id] = word 
        ret_id = self._next_word_id
        self._next_word_id += 1
        return ret_id  
    
    def get_inverted_index(self):
        """A function that returns the set of doc ids when given the word id as a key"""
        mapping = self._mapping_word_id_to_doc_id
        return mapping
            
    """iterates through the word id and set of doc ids,
    resolves them all into their cooresponding strings and puts them back"""
    
    def resolve_index(self):
        #iterate through keys (word_id) of 2d dictionary
	for word_id in self._mapping_word_id_to_doc_id.iterkeys():
	    mapping = self.get_inverted_index()
	    word = self._word_str_cache[word_id]
	    #create list to use as a stack
            tmp_list = []
            #initialize an empty set to store the urls
            self._mapping_word_str_to_doc_str[word] = set()     
            #convert doc id to urls, and throw them onto the stack
            for doc_id in mapping[word_id]:
		        url = self._doc_str_cache[doc_id]
		        tmp_list.append(url)
            #iterate through stack to add back onto new set    
            length = len(tmp_list)
            i = 0
            while i < length:
            #for list_url in test_list:
                reversed_url = tmp_list.pop();
                self._mapping_word_str_to_doc_str[word].add(reversed_url)
                i += 1
    	
    def get_resolved_inverted_index(self):
        """A function that returns a set of doc str when given the word str as a key"""
        mapping = self._mapping_word_str_to_doc_str 
        return mapping
    
    def add_doc_id(self, word):
        """adds to set of doc ids when called"""
	id_set = self._mapping_word_id_to_doc_id[self.word_id(word)]
        id_set.add(self._curr_doc_id)
    
    """ -- methods added for lab 1 end -- """

    """ -- methods added for lab 3 start -- """

    # function to assign a rank to pages based on their outgoing links
    def page_rank(self, num_iterations=20, initial_page_rank = 1.0):
        page_rank = defaultdict(lambda: float(initial_page_rank))
        num_outgoing_links = defaultdict(float)
        incoming_links_sets = defaultdict(set)
        incoming_links = defaultdict(lambda: np.array([]))
        damping_factor = 0.85
        
        # for each link pair: 
        # incr outgoing links dictionary for from_id
        # add to incoming link set for to_id
        for from_id, to_id in self.links:
            num_outgoing_links[from_id] += 1.0
            incoming_links_sets[to_id].add(from_id)
        
        # turn into array for easier processing later
        # use every to_id as key to hold entire array of incoming ids
        for to_id in incoming_links_sets:
            incoming_links[to_id] = np.array([from_id for from_id in incoming_links_sets[to_id]])
                    
        # find how many documents are leaving the page (from_id)
        # then create equation in from_id
        num_documents = float(len(num_outgoing_links))
        lead = (1.0 - damping_factor) / num_documents
        partial_page_rank = np.vectorize(lambda from_id: page_rank[from_id] / num_outgoing_links[from_id])

        for num in xrange(num_iterations):
            for from_id in num_outgoing_links:
                end = 0.0
                if len(incoming_links[from_id]):
                    # change this function later
                    end = damping_factor * partial_page_rank(incoming_links[from_id]).sum()
                    page_rank[from_id] = lead + end
        return page_rank

    def ranked_inverted_index(self):
        #preload the data for future use
        doc_id_sets = self.get_inverted_index()
        tmp_list = []
        page_rank_dicts = self.page_rank()
        # for every word in the cache, a list of doc ids are assigned
        for word, word_id in self._word_id_cache.items():
            for doc_id in doc_id_sets[word_id]:
                pr = page_rank_dicts[doc_id]
                new_rank_pair = doc_id, pr
                # append to a set and sort
                tmp_list.append(new_rank_pair)
            tmp_list.sort(reverse = True, key = lambda rank_pair: rank_pair[1])
            self.word_to_url_list[word] = list()               
            while(len(tmp_list)>0):
                doc_id, pr =  tmp_list.pop(0)
                url = self._doc_str_cache[doc_id]
                self.word_to_url_list[word].append(url)
                #server.rpush(word, url)
                # cache it as a dictionary for quick access

    """ -- methods added for lab 3 end -- """
 
    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = [ ]
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))
            
            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup, _curr_doc_id):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""
        class DummyTag(object):
            next = False
            name = ''
        
        class NextTag(object):
            def __init__(self, obj):
                self.next = obj
        
        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)
                    
                    continue
                
                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)

            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id) # mark this document as haven't been visited
            
            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = [ ]
                self._index_document(soup, self._curr_doc_id)
                self._add_words_to_document()
                print "    url="+repr(self._curr_url)

            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()

if __name__ == "__main__":
    bot = crawler(None, "urls.txt")
    bot.crawl(depth=1)
    bot.resolve_index()
    bot.ranked_inverted_index()
    print bot.title_dict
    print bot.description_dict
    #for title in bot.title_dict.keys():
        #print title
        #urls = bot._doc_str_cache[title]
        #info = server.lrange(urls, 0, -1)
        #print info[0]
        #print info[1]
        #print info
    #print "actual url queue: "
    #firstWord = 'toronto'
    #urlsSet = server.lrange(firstWord, 0, -1)
    with open('search_database.pickle', 'wb') as handle:
        url_list = bot.word_to_url_list
        pickle.dump(url_list, handle)
        
        url_titles = bot.title_dict
        pickle.dump(url_titles, handle)
        
        url_desc = bot.description_dict
        pickle.dump(url_desc, handle)
        
    # for url in urlsSet:
    #     print bot._doc_id_cache[url]
    #bot.print_links()
    #links = [(1,2), (1,3), (3,4), (1,4), (2,3), (4,3)]
    #ranks = bot.page_rank()
    #for doc_id in ranks:
    #    print "doc_id : " + str(doc_id)
    #    print "rank is :" + str(ranks[doc_id])
    #word = raw_input("search for an existing word or : ")  
    #while word != "exit":          
    #    print "word is " + word
    #    word_id = bot.word_id(word)
    #    print "word_id is " + str(word_id)  
    #    inverted = bot.get_inverted_index()
	#bot.resolve_index()        
    #    inverted_resolved = bot.get_resolved_inverted_index()
    #    print inverted[word_id]
    #    print inverted_resolved[word]
	#word = raw_input("search for an existing word or : ") 

