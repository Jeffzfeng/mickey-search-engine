from bottle import route, run, request, redirect, app
import collections, httplib2
from collections import OrderedDict
from collections import Counter
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from beaker.middleware import SessionMiddleware

#Variable are used to store history of the top 20 most popular keywords searched
#since the server was launched. This will be made global later in the code
historyTable = {}
userAndHistory = {}
currentEmail = ''
printhtable = ''
userLoggedIn = False
client_id='394896223709-7s4up8chvj91t1b46okqn6r5pu79hqvh.apps.googleusercontent.com'
client_secret = 'b06MxTqsWPWO1mXQwr45q8t8'
redirect_uri = 'http://ec2-52-14-224-74.us-east-2.compute.amazonaws.com:80/redirect'
scope = 'https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email'

#The page template sets up the necessary styling and form for the homepage
pageTemplate = '''
	<!DOCTYPE html>
	<html>
	<head>
	<style>
	html {
	    background: #648880;
	    background: linear-gradient(to right, #f6f1d3, #648880, #293f50);
	}

	h1 {
	    color: maroon;
	} 

	.header img {
	  float: left;
	  width: 62px;
	  height: 62px;
	}

	.header h1 {
	  position: relative;
	  top: 18px;
	  left: 10px;
	}
	</style>
	</head>

	<div class="header">
		<img src="https://lumiere-a.akamaihd.net/v1/images/navigation_mickeymouseclubhouse_disneyjunior_7844134d.png" alt="Mickey"/>
		<h1>mIcky Search<h1>
	</div>
	<br><br><br>
'''
searchBar='''

	<form action ="/results" method="get">
				<b>Type in a phrase:<b> <br><input name="keywords" type="text" style="width: 300px;"/>
				<input value = "Search" type="submit" />
			</form>
	<br><br>
'''
signInButton = '''
	<form action="/signin" method="get"
		<b>Sign in here: <b>
		<input value = "Sign In" type="submit"/>
	</form>
	<br><br>
'''

signOutButton = '''
<form method="link" action="http://ec2-52-14-224-74.us-east-2.compute.amazonaws.com:80/logout" >
	<input type="submit" value="Sign Out">
</form>
<br>
'''
returnToSearchButton = '''
<form method="link" action="http://ec2-52-14-224-74.us-east-2.compute.amazonaws.com:80/">
	<input type="submit" value="Back To Search">
</form>
<br>
'''
historyTableMarkup='''
	<h3>History<h3>
	<table name=""history""style=""width:300px""> <col width="300"> <col width="120"> <tr><td><b>Word</b></td><td><b>Count</b></td></tr>
	</body>
	</html>

	'''
#Purpose: return the number of occurences of each word in the input phrase
def count_words(phrase):

	counts = OrderedDict()
	words = phrase.split()
	
	for word in words:
		if word in counts:
			counts[word] += 1
		else:
			counts[word] = 1
	return counts

#Purpose: return the updated history dictionary after adding in the results
#of the most recent search. Then print these results to the history table.
def add_new_dictionary(countedWords):
	#somewhere here you're going to have to add the historyTable to the userAndHistory as well
	global historyTable

	historyTable = Counter(historyTable) 
	countedWords = Counter(countedWords)
	newDict = historyTable + countedWords
	historyTable = newDict
	#fixxxxx
	global currentEmail
	global userAndHistory
	userAndHistory[currentEmail]=historyTable
	print userAndHistory[currentEmail]
	print_table(newDict)

def print_table(newDict):
	global printhtable
	printhtable = ""
	for key, value in newDict.most_common(20):
		printhtable += "<tr><td>" + key + "</td><td>" + str(value) + "</td></tr>"

@route('/signin', method='GET')
def google_api():
	session = request.environ.get('beaker.session')
	session.save()
	#google api set up
	flow = flow_from_clientsecrets("client_secrets.json", scope = scope, redirect_uri = redirect_uri)
	uri = flow.step1_get_authorize_url()
	redirect(uri)

session_opts = {
	'session.type': 'file', 
	'session.cookie_expires': 300,
	'session.data_dir': './data',
	'session.auto': True,
}
wsgi_app = SessionMiddleware(app(), session_opts)

@route('/logout')
def logout():
	global userLoggedIn
	userLoggedIn = False
	redirect("https://www.google.com/accounts/Logout?continue=https://appengine.google.com/_ah/logout?continue=http://ec2-52-14-224-74.us-east-2.compute.amazonaws.com:80/")

@route('/redirect', method='GET')
def redirect_page():
	code = request.query.get('code', '/')
	flow = OAuth2WebServerFlow( client_id = client_id, client_secret = client_secret, scope = scope, redirect_uri = 'http://ec2-52-14-224-74.us-east-2.compute.amazonaws.com:80/redirect')
	credentials = flow.step2_exchange(code)
	token = credentials.id_token['sub']
	print 'The token is: ' + token
	#retrieve user data with the access token
	http = httplib2.Http()
	http = credentials.authorize(http)

	#get user email
	users_service = build('oauth2', 'v2', http=http)
	user_document = users_service.userinfo().get().execute()
	user_email = user_document['email']
	global currentEmail 
	currentEmail = user_email
	global userLoggedIn	
	userLoggedIn = True
	redirect('/loggedIn')

@route('/loggedIn', method = 'GET')
def logged_in_page():
	#if this users email doesn't exist in the users_and_history dictionary
	global historyTable
	historyTable = {}
	printhtable = ''
	global currentEmail
	welcomeMessage = 'Welcome <b>' + currentEmail + '<b>'
	if currentEmail in userAndHistory.keys():
		list_userAndHistory = userAndHistory[currentEmail]
		print "Current email exists, and the list is: " + str(list_userAndHistory)
		add_new_dictionary(list_userAndHistory)
		newDict = userAndHistory[currentEmail]
		global printhtable
		printhtable = ""
		for key, value in newDict.most_common(20):
			printhtable += "<tr><td>" + key + "</td><td>" + str(value) + "</td></tr>"
		print userAndHistory[currentEmail]
	else:
		print "Email doesnt exist, check value of userAndHistory" + str(userAndHistory)
		userAndHistory[currentEmail] = {}
		print "The current email doesnt exist, therefore add: " + str(userAndHistory)
	
	return  welcomeMessage + pageTemplate + searchBar + signOutButton + historyTableMarkup + printhtable 

@route('/', method='GET')
def initial_page():
	if userLoggedIn:
		redirect('/loggedIn')
	return pageTemplate + searchBar + signInButton

#Purpose: Return the count of each occurence of a word in the most recent
#search phrase. Then print these results to the results table.
@route('/results', method='GET')
def results_table():
	phrase = request.query["keywords"]
	#return phrase

	counted_words = count_words(phrase.lower())
	table = "<table id=""results"" name=""results"" style=""width:50%""> <tr><td><b>Word</b></td><td><b>Count</b></td></tr>"
	global userLoggedIn
	if userLoggedIn:
		add_new_dictionary(counted_words)

	for key, value in counted_words.items():
		table += "<tr><td>" + key + "</td><td>" + str(value) + "</td></tr>"
	welcomeMessage = 'Welcome <b>' + currentEmail + '<b>'
	if userLoggedIn:
		return welcomeMessage + pageTemplate +  returnToSearchButton+ signOutButton + "<b>Search for: </b>\"" + phrase + "\"<br><h3>Results<h3>" + table 
	else: 
		return pageTemplate + returnToSearchButton + "<b>Search for: </b>\"" + phrase + "\"<br><h3>Results<h3>" + table



run(host="0.0.0.0", port="80", debug=True, app=wsgi_app)
