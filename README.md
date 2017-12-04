# README #

This README document steps neccessary to run the Mickey Mickey Go Search Engine. 

### How do I get set up?
 - All setup will be done in the deployment.cfg file, follow the example config set for further information 

###To Change credentials
1. `cd csc326-mikeymikeygo`
2. `vim deployment.cfg`

###To Deploy
1. `cd csc326-mikeymikeygo`
2. `python deployment.py`

###To Run
1. once deployed, go to 'ip address'

###To Terminate 
1. `cd csc326-mikeymikeygo`
2. run `python termination.py`

###To Crawl:
1. run `python crawler.py`
2. output of crawled results will be in the pickle file, 'search_database.pickle'
