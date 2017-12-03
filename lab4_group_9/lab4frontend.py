from bottle import route, run, request, redirect, app, error, get, static_file
import collections, httplib2, redis
import enchant

pageTemplate = '''
<!DOCTYPE html>
<html>
<head>
	<style>
		html {
			background: #ffffff;
		}
		body {
			text-align: center;
		}

		h1 {
			color: 000000;
			text-align: center;
		} 

		.outer-div
		{
			padding: 30px;
			text-align: center;
		}
		.header h1 {
			position: relative;
			top: 10%;
		}

		div.container3{
			margin: 0;
			position: left;
			left:85%
		}

		input.go{
			border-radius: 10px; 
			background-color: white; 
			display: inline-block;
			width:50px;
			height: 45px;
			font-size:100%;
			color: black;
		}

		div.resultsouter{
			border-radius: 10px;
			background-color: #f2f2f4; 
			display: inline-block;
			width:77%;

		}

		p.resultsstyle{
			border-radius: 10px;
			padding: 1px;	  
			background-color: white; 
			display: inline-block;
			width:95%;
			font-size:100%;
			font-family: 'Libre Baskerville', serif;
			font-size: 14px;
			color: #616163;
			text-align: left;
			overflow-wrap: break-word;
			word-wrap: break-word;
		}

		div.alertwarning{
			background-color: #f9f9a7;
			width: 77%;
			display: inline-block;
			text-align: middle;
			padding: 2px;
			border-width: 1px;
			border-color: #595005;
		}

		div.alertnoresults{
			background-color: #f9ccce;
			width: 77%;
			display: inline-block;
			text-align: middle;
			padding: 2px;
			border-width: 1px;
			border-color: #595005;
		}

		div.searchstyle{
			display:inline-block;
			text-align: center;
			padding: 10px ;
			width: 85%;
			color: yellow;
		}

		input.searchstyle{
			border-radius: 10px; 
			background-color: white; 
			padding:  0 0 0 10px;
			width: 80%;
			height: 45px;
			font-size:100%;
		}
		a.pagetitlestyle{
			color: #23328c;
			text-align: left;
			text-decoration: none;
			font-family: 'Libre Baskerville', sans-serif;
			font-size: 19px;
			overflow-wrap: break-word;
			word-wrap: break-word;
		}

		a.linkstyle{
			color: green;
			text-align: left;
		}

		div.welcome{
			margin: 0;
			position: left;
			right: 35%;
			top: 5%;
		}

		div.backButton{
			margin: 0;
			position: absolute;
			top: 20%;
			left: 20%;
			margin-right: -80%;
			transform: translate(-50%, -50%)
		}

		p.searchresultstitlestyle{
			color: #757791;
			font-family: 'Libre Baskerville', sans-serif;
			font-size: 20px;
		}

		.topnav {
			overflow: hidden;
			background-color: #0444a3;
			border-radius: 10px;
		}

		.topnav a {
			float: left;
			display: block;
			color: black;
			text-align: center;
			padding: 17px 16px;
			text-decoration: none;
			font-size: 17px;
		}

		.topnav a:hover {
			background-color: blue;
			color: black;
		}

		.active {
			background-color: #f7e30e;
			color: white;
		}

		@media screen and (max-width: 600px) {
			.topnav a:not(:first-child) {display: none;}
			.topnav a.icon {
				float: right;
				display: block;
			}
		}

		@media screen and (max-width: 600px) {
			.topnav.responsive {position: relative;}
			.topnav.responsive .icon {
				position: absolute;
				right: 0;
				top: 0;
			}
			.topnav.responsive a {
				float: none;
				display: block;
				text-align: left;
			}

		}

	</style>
</head>
<body>
	<div class="topnav" id="myTopnav">
		<a style="font:25px" href="/" class="active">Mickey Mickey Go</a>
	</div>
	<br>
	<form action ="/results" method="get">
		<div class="searchstyle">
			<input class=searchstyle name="keywords" type="text" placeholder="Type search phrase here"/>
			<input class=go value = "GO!" type="submit" />
		</div>
	</form>
	<div class="outer-div">
'''
mickeyPicture='''
<div class="header">
	<img width="20%"
	height="30%" src="https://lumiere-a.akamaihd.net/v1/images/navigation_mickeymouseclubhouse_disneyjunior_7844134d.png" />
</div>
'''
searchBar='''
<form action ="/results" method="get">
	<br><input class=searchstyle name="keywords" type="text" placeholder="Type search phrase here"/>
	<input class=go value = "GO!" type="submit" />
</form>
'''

@route('/', method='GET')
def initial_page():
	return  pageTemplate + mickeyPicture + "</body> </html>"

@error(404)

def error404(error):
	return pageTemplate + '''This page or file does not exist. <br><br> 
				Please visit the <a href="http://localhost:8080/">
				Search page</a> for a new search.'''

@route('/&keywords=<keywords>&page_no=<pageNum>', method='GET')

#This function displays the results based on the page number. We only use this 
#function if the number of urls require more than one page to display. 

def results_per_page(keywords, pageNum):

	searchResultsTitle = '''<p class=searchresultstitlestyle> Search Results For: %s</p> '''%(keywords)
	listofwords=keywords.split(' ')
	redisServer = redis.Redis('52.14.224.74')
	
	#Make sure there are no repeated words - if there are only include the first instance of the word
	list(set(listofwords))
	
	a = []
	for x in listofwords:
	    if x not in a:
		a.append(x)

	listofwords = list()
	listofwords = a
	
	#Set up the spell checking and spell correction feature 
	spellchecker = ' '
	englishD = enchant.Dict()
	incorrectWords = list()
	
	#Loop through the users input and determine any misspelt words
	for word in listofwords:
		if not word:
			pass
		else:
			if englishD.check(word) == False:
				#words that are misspelt but still bring up search results are not considered as misspelt words
				urlspellcheck = redisServer.lrange(word, 0, -1)
				if len(urlspellcheck) == 0:
					incorrectWords.append(word);
	
	#If there are misspelt words, create html to be able to display it later
	if len(incorrectWords)>0: 
		spellchecker+='''<div class="alertwarning"><p style="color: #595005">
    				<strong>Spell Check!</strong> You may have misspelt words:<br><br>'''

	for word in incorrectWords:
		if len(englishD.suggest(word)) > 0:
			spellchecker+='''%s -> suggestion: %s<br>'''%(word, englishD.suggest(word)[0])
		else:
			spellchecker+=''''%s -> suggestion: no suggestion<br>''' %(word)
	
	#Closing html tags if any incorrect words are detected
  	if len(incorrectWords)>0: 	
		spellchecker += '''</p></div><br><br>'''

	#Obtain the list of Urls for every word and add it to the urlsSet
	urlsSet=list()
	no_results_found = ' '
	for m in range(len(listofwords)):
		if not listofwords[m]:
			pass
		else:
			currword = listofwords[m]
			urlsSet += redisServer.lrange(currword, 0, -1)
	
	numLinks = len(urlsSet)	
	print numLinks
	if numLinks == 0:
		no_results_found += '<div class=alertnoresults><p><strong>Sorry!</strong> No Results Found</p></div><br><br>'
	
	#Calculate the number of pages it would require to display all the urls 
	#in urlsSet if the number of urls per page limit was set to 5 pages

	objectsInTotalSet = range(len(urlsSet))
	maxLinksPerPage=5

	if len(urlsSet) < maxLinksPerPage:
		numPages = 1
		remainderLinks = len(urlsSet)
	else:
		numPages, remainderLinks = divmod(objectsInTotalSet[-1]+1, maxLinksPerPage)

		if remainderLinks > 0:
			numPages += 1

	if int(pageNum) > numPages:
		redirect('/err')

	#Create the html tags to display the page numbers list at the bottom of the page
	pageList = "Page: "

	for page in range(numPages):
		pageList += '<a href= "http://localhost:8080/&keywords=' + keywords + '&page_no=' + str(page+1) + '"<a>' + str(page+1) + ' '

	pageList += "</tr>"


	#Based on the current page number get the correct set of urls to display
	#i.e. page 1 will have links 1-5, page 2 will have links 6-10 and so on

	global maxLinksPerPage
	higherRangeofData = int(pageNum)*maxLinksPerPage
	lowerRangeofData = higherRangeofData-maxLinksPerPage
	
	displayLinks = ''
	urltitle = ''
	urldescrip = ''
	urlsSet = urlsSet[lowerRangeofData:higherRangeofData]

	#Loop through the urlsSet and obtain the title, description for every url
	for i in range(len(urlsSet)):
		url = urlsSet[i]
		urlinfo = redisServer.lrange(url, 0, -1);
		lengthurllist=len(urlinfo)
		
		#perform error checking to make sure the title of the url exists before obtaining it
		if lengthurllist == 1:
			if urlinfo[0]==None:
				pass;
			else:
				urltitle = urlinfo[0]
	
		#perform error checking to make sure the description of the url exists before obtaining it
		elif lengthurllist <= 2 :
			if urlinfo[0]==None or urlinfo[1]==None:
				pass;
			else:
				urltitle = urlinfo[0]
				urldescrip = urlinfo[1]

		#Create the html tags to display the url, title, description
		urlString = str(url)
		displayLinks += '''<div class=resultsouter><p class=resultsstyle>
				<a class=pagetitlestyle href="%s">%s</a><br>
				<a class="linkstyle">%s</a><br><br>%s<br></p></div>
				<br><br>''' % (urlString, urltitle, urlString, urldescrip)

	return pageTemplate + searchResultsTitle + no_results_found + spellchecker + displayLinks + '<br>' + pageList 


@route('/results', method='GET')
def results_table():

	phrase = request.query["keywords"]
	redirect('/&keywords=%s&page_no=%d'% (phrase, 1))

	

run(host="localhost", port="8080", debug=True)
