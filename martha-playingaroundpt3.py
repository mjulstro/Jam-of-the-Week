
#https://nocodewebscraping.com/facebook-scraper/

import urllib2
import json
import datetime
import csv
import time
from collections import defaultdict

#app_id = "<FILL IN>"
#app_secret = "<FILL IN>" # DO NOT SHARE WITH ANYONE!
file_id = raw_input("Please Paste the Page name or Group ID:")

#access_token = app_id + "|" + app_secret
access_token = "318577115222655|623cad8bc46ebcb08ca7bc225ab15860"

def request_until_succeed(url):
    req = urllib2.Request(url)
    success = False
    while success is False:
        try:
            response = urllib2.urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception, e:
            print e
            time.sleep(5)

            print "Error for URL %s: %s" % (url, datetime.datetime.now())
            print "Retrying."

            if '400' in str(e):
                return None

    return response.read()

# Needed to write tricky unicode correctly to csv
def unicode_normalize(text):
    return text.translate({ 0x2018:0x27, 0x2019:0x27, 0x201C:0x22,
                            0x201D:0x22, 0xa0:0x20 }).encode('utf-8')

def getFacebookCommentFeedData(status_id, access_token, num_comments):

    # Construct the URL string
        base = "https://graph.facebook.com/v2.6"
        node = "/%s/comments" % status_id
        fields = "?fields=id,message,like_count,created_time,comments,from,attachment"
        parameters = "&order=chronological&limit=%s&access_token=%s" % \
                (num_comments, access_token)
        url = base + node + fields + parameters

        # retrieve data
        data = request_until_succeed(url)
        if data is None:
            return None
        else:
            return json.loads(data)

def processFacebookComment(comment, status_id, parent_id = ''):

    # The status is now a Python dictionary, so for top-level items,
    # we can simply call the key.

    # Additionally, some items may not always exist,
    # so must check for existence first

    comment_id = comment['id']
    comment_message = '' if 'message' not in comment else \
            unicode_normalize(comment['message'])
    comment_author = unicode_normalize(comment['from']['name'])
    comment_likes = 0 if 'like_count' not in comment else \
            comment['like_count']

    if 'attachment' in comment:
        attach_tag = "[[%s]]" % comment['attachment']['type'].upper()
        comment_message = attach_tag if comment_message is '' else \
                (comment_message.decode("utf-8") + " " + \
                        attach_tag).encode("utf-8")

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

    comment_published = datetime.datetime.strptime(
            comment['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
    comment_published = comment_published + datetime.timedelta(hours=-5) # EST
    comment_published = comment_published.strftime(
            '%Y-%m-%d %H:%M:%S') # best time format for spreadsheet programs

    # Return a tuple of all processed data

    return (comment_id, status_id, parent_id, comment_message, comment_author,
            comment_published, comment_likes)

def scrapeFacebookPageFeedComments():
    with open('%s_facebook_statuses.csv' % group_id, 'wb') as file: #i want to name this something else?
        w = csv.writer(file)
        w.writerow(["status_id", "status_message", "status_author",
            "link_name", "status_type", "status_link","permalink_url",
            "status_published", "num_reactions", "num_comments",
            "num_shares", "num_likes", "num_loves", "num_wows",
            "num_hahas", "num_sads", "num_angrys"])

        num_processed = 0   # keep a count on how many we've processed
        scrape_starttime = datetime.datetime.now()


        columns = defaultdict(list) # each value in each column is appended to a list

        with open('SAVE ME.csv') as f:
            reader = csv.DictReader(f) # read rows into a dictionary format
            for row in reader: # read a row as {column1: value1, column2: value2,...}
                for (k,v) in row.items(): # go over each column name and value
                    columns[k].append(v) # append the value into the appropriate list


        listofstatusids = list(columns['status_id'])

        for i in range(len(listofstatusids)):
            w.writerow(processFacebookComment(str(listofstatusids[i]), access_token)) #print str(listofstatusids[i]) #What this does right now: prints each status id as a string. #right... so here we will call something that writes the row
            num_processed += 1
            if num_processed % 100 == 0:
                print "%s Statuses Processed: %s" % (num_processed,
                                                     datetime.datetime.now())
        print "\nDone!\n%s Statuses Processed in %s" % \
          (num_processed, datetime.datetime.now() - scrape_starttime)


if __name__ == '__main__':
    scrapeFacebookPageFeedComments()


# The CSV can be opened in all major statistical programs. Have fun! :)