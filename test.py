import time
import os
import sys
import requests
import random
#import web

import feedparser
from pandas.io.json import json_normalize
import pandas as pd
import requests
from nltk import word_tokenize, pos_tag

# a list of all the sites to source from
sites = ["http://www.irinnews.org/irin.xml",\
         "http://rss.cnn.com/rss/edition.rss",\
         "http://syndication.apn.co.nz/rss/nzhrsscid_000000001.xml",\
         "http://chinaview.wordpress.com/feed/",\
         "http://www.zeenews.com/rss/india-national-news.xml",\
         "http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml",\
         "http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/front_page/rss.xml",\
         "http://www.guardian.co.uk/world/rss",\
         "http://pewforum.org/rssfeeds/news/rss.xml",\
         "http://www.thepress.co.uk/news/rss/"]

# "http://myagonyaunt.com/feed/" has been removed. The sequence 'population' below has been shortened accordingly.


# the population sequence is used to help select sites at random without replacement
population = (0,1,2,3,4,5,6,7,8,9)

# number of sites to source from
numberSites1 = 5
numberSites2 = 4

# time interval between sourcings in seconds
timeInterval = 300

# set the maximum word length of each headline and feeling
maxLen = 8
maxLenFeeling = 12

# for gathering up selected news and feelings sentences
selectedNews = []
selectedFeelings = []

feelingsList = []

#repoPath = '/home/pi/prayer_companion_moma_git/prayercompanion-text'
#repoPath = '/Users/ynpv8/Documents/prayercompanion/prayer_update/prayer_companion_moma_git/prayercompanion-text'

from nltk import word_tokenize, pos_tag

def txt2List(text):
    global feelingsList
    my_file = open(text, "r")

    # reading the file
    data = my_file.read()
    # replacing end splitting the text
    # when newline ('\n') is seen.
    feelingsList = data.split("\n")
    #print(feelingsList)
    my_file.close()


def is_valid_sentence(sentence):
    allowable_nouns = ['NP', 'NN', 'NNP', 'NNS', 'PRP', 'WP']
    allowable_verbs = ['VP', 'VB', 'VBD', 'VBN', 'VBP', 'VBZ']
    tags = pos_tag(word_tokenize(sentence))
    #print(tags)
    nouns = 0
    verbs = 0
    first_noun = None
    first_verb = None
    for i, t in enumerate(tags):
        #print(t)
		# Is the noun before the verb?
        if t[1] in allowable_nouns:
            nouns = nouns + 1
            if first_noun == None:
                first_noun = i
        elif t[1] in allowable_verbs:
            verbs = verbs + 1
            if first_verb == None:
                first_verb = i

    #print("Nouns: ", nouns)
    #print("Verbs: ", verbs)
    #print("First noun: ", first_noun)
    #print("First verb: ", first_verb)
	# is there at least one noun and one verb, and is the noun first?
    if first_noun != None and first_verb != None:
        if first_noun < first_verb:
            #print("Noun before verb, valid sentence")
            return True
        else:
            #print("Verb before noun!")
            return False
    else:
        #print("Does not contain 1 noun and 1 verb")
        return False

def testForRogues(s):
    # this function tests for characters which can cause trouble somewhere down the line
    result = 0
    if (s.count("'") > 0) or (s.count("-") > 0) or (s.count(";") > 0) or (s.count(",") > 0) \
       or (s.count("\"") > 0) or (s.count(",") > 0) or (s.count("“") > 0) or (s.count("”") > 0) \
       or (s.count("‘") > 0) or (s.count("”") > 0) or (s.count("http") > 0) or (s.count("’") > 0) \
       or (s.count("*") > 0) or (s.count("&") > 0) or (s.count("src") > 0) or (s.count("(") > 0) \
       or (s.count(")") > 0) or (s.count("`") > 0) or (s.count("href") > 0):
        result = 1
    return result

def testForDisplayables(s):
    for i in range(0,len(s)):
        if (ord(s[i]) > 122):
##            print 'ITEM REJECTED', s
            time.sleep(5)
            return 0
    return 1



def getNews(site):
    global selectedNews
    #newsfeed = web.newsfeed.parse(site, cached=False)
    newsfeed = feedparser.parse(site)

    for newitem in newsfeed['items']:
        s = newitem['title']
        if s[0].isdigit():
            if s[1].isdigit() or s[1] == '.':
                print("starts with a number")
                if s[2] == ".":
                    s = s[3:]
                else:
                    s = s[2:]
                if s[0] == ' ':
                    s = s[1:]
        # the next conditionals eliminate headlines:
        # which are less than four words long (implied by presence of spaces)
        # which are greater than maxLen words
        # which contain rogue characters
        spaceCount = 0;
        spaceCount = s.count(" ")
        if (spaceCount < 3) | (spaceCount >= maxLen):
            continue
        if (testForRogues(s) > 0):
            continue
        # replace pound signs which are non-ascii with stars (conversion-back takes place at the device)
        # replace dollar signs which are ascii but confuse pd with ampersands (conversion-back takes place at the device)
        s = s.replace('£','*')
        s = s.replace('$','&')
        # now test if the headline contains characters the device cannot display
        if (testForDisplayables(s) < 1):
            continue

        if is_valid_sentence(s) == True :
            selectedNews.append(s)


def getFeelings(call):
    global selectedFeelings
    # retrieve feelings as instructed in the call to wefeelfine.org (see the API documentation)
    f = requests.get(call)
    out = f.text
    #print(out)
    feelingElements = out.split("<br>")
    for x in feelingElements:
        s = x.__str__()
        #s = s.strip();
        # the next conditionals eliminate headlines:
        # which are greater than maxLenFeeling words long
        # which contain rogue characters
        spaceCount = 0
        spaceCount = s.count(" ")
        #print(s)
        #print(spaceCount)
        if (spaceCount >= maxLenFeeling):
            print("too long")
            continue
        if (testForRogues(s) > 0):
            print("rogues")
            continue
        # replace pound signs which are non-ascii with stars (conversion-back takes place at the device)
        # replace dollar signs which are ascii but confuse pd with ampersands (conversion-back takes place at the device)
        s = s.replace('£','*')
        s = s.replace('$','&')
        s = s.replace('i ','I ')
        s = s.replace('don t ','don\'t ')
        s = s.replace('doesn t','doesn\'t')
        s = s.replace('can t ','can\'t ')
        s = s.replace('didn t','didn\'t')
        s = s.replace('it s ','it\'s ')
        s = s.replace('wouldn t','wouldn\'t')
        s = s.replace('shouldn t','shouldn\'t')
        s = s.replace('couldn t','couldn\'t')
        s = s.replace('I m ','I\'m ')
        # now test if the headline contains characters the device cannot display
        if (testForDisplayables(s) < 1):
            print("displayables")
            continue

        if is_valid_sentence(s) == True :
            print(s)
            print("appending")
            selectedFeelings.append(s)

def getFeelingsLocal():
    global selectedFeelings
    randomFeelings = []
    # retrieve feelings as instructed in the call to wefeelfine.org (see the API documentation)
    randomFeelings = random.choices(feelingsList, k=60)
    print(randomFeelings)
    for x in randomFeelings:
        s = x.__str__()
        #s = s.strip();
        # the next conditionals eliminate headlines:
        # which are greater than maxLenFeeling words long
        # which contain rogue characters
        spaceCount = 0
        spaceCount = s.count(" ")
        #print(s)
        #print(spaceCount)
        if (spaceCount >= maxLenFeeling):
            print("too long")
            continue
        if (testForRogues(s) > 0):
            print("rogues")
            continue
        # replace pound signs which are non-ascii with stars (conversion-back takes place at the device)
        # replace dollar signs which are ascii but confuse pd with ampersands (conversion-back takes place at the device)
        s = s.replace('£','*')
        s = s.replace('$','&')
        s = s.replace('i ','I ')
        s = s.replace('don t ','don\'t ')
        s = s.replace('doesn t','doesn\'t')
        s = s.replace('can t ','can\'t ')
        s = s.replace('didn t','didn\'t')
        s = s.replace('it s ','it\'s ')
        s = s.replace('wouldn t','wouldn\'t')
        s = s.replace('shouldn t','shouldn\'t')
        s = s.replace('couldn t','couldn\'t')
        s = s.replace('I m ','I\'m ')
        # now test if the headline contains characters the device cannot display
        if (testForDisplayables(s) < 1):
            print("displayables")
            continue

        if is_valid_sentence(s) == True :
            print(s)
            s = s + '\n'
            print("appending")
            selectedFeelings.append(s)

def pullFromGithub():
    repo = Repo(repoPath)
    repo.remotes.origin.pull()

def postGithub():
    repo = Repo(repoPath)
    diff = repo.git.diff(repo.head.commit.tree)
    print(diff)
    repo.index.add(['feelingsfile.txt','newsfile.txt','sourcinglogfile.txt'])
    repo.index.commit('news and feelings commit')
    repo.remotes.origin.push(force=True)


txt2List(os.path.join(sys.path[0], "archivefeelings.txt"))

print("** Getting news and feelings **")
#pullFromGithub()
#try:

    #web.clear_cache()

log =  time.strftime("New Sourcing at: " "%A, %B %d, %Y" " at " "%H:%M:%S", time.localtime())
print(log)


selectedSites1 = []
selectedSites2 = []

selectedSites = random.sample(population, numberSites1+numberSites2)
for p in range(0,numberSites1):
    selectedSites1.append(selectedSites[p])
for q in range(numberSites1,numberSites1+numberSites2):
    selectedSites2.append(selectedSites[q])

selectedSites1.sort()
selectedSites2.sort()

for p in range(0, numberSites1):
    print(sites[selectedSites1[p]])
##           log = string.join(log, sites1[selectedSites1[p]])

for q in range(0, numberSites1):
    getNews(sites[selectedSites1[q]])


selectedNews = '\n'.join(selectedNews)
selectedNews = selectedNews + '\n'
print("test")
print(sys.path[0])
newsfile = open(os.path.join(sys.path[0], 'newsfile.txt'), 'w')
newsfile.write(selectedNews)
newsfile.close()

print("News File")
print(selectedNews)

selectedNews = []

for p in range(0, numberSites2):
    print(sites[selectedSites2[p]])
##           log = string.join(log, sites2[selectedSites2[p]])

for q in range(0, numberSites2):
    getNews(sites[selectedSites2[q]])

#getFeelings("http://api.wefeelfine.org:8080/ShowFeelings?display=text&returnfields=sentence&limit=60")
getFeelingsLocal()
selectedNews = '\n'.join(selectedNews)
selectedNews = selectedNews + '\n'

newsfile = open(os.path.join(sys.path[0], "newsfile.txt"), 'w')
newsfile.write(selectedNews)
newsfile.close()

for line in selectedFeelings:
    if line in ['\n', '\r\n']:
        selectedFeelings.remove(line)
selectedFeelings.append(selectedNews)
selectedFeelings.reverse()

selectedFeelings = ' '.join(selectedFeelings)
feelingsfile = open(os.path.join(sys.path[0], "feelingsfile.txt"), 'w')
feelingsfile.write(selectedFeelings)
feelingsfile.close()

print("Feelings File")
print(selectedFeelings)

selectedNews = []
selectedFeelings = []



sourcinglogfile = open(os.path.join(sys.path[0], "sourcinglogfile.txt"), 'w')
sourcinglogfile.write(log)
sourcinglogfile.close()
print("** Uploading news and feelings **")
#postGithub()

print("** Uploading done **")
print(log)
print("** Next sourcing in 60 minutes **")
