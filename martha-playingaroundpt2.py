import urllib2
import json
import datetime
import csv
import time
from collections import defaultdict
group_id = "558429457587216"

# access_token = app_id + "|" + app_secret
access_token = "318577115222655|623cad8bc46ebcb08ca7bc225ab15860"

def request_until_succeed(url):
    req = urllib2.Request(url)
    success = False
    while success is False:
        try:
            response = urllib2.urlopen(req)
            if response.getcode() == 200:
                success = True
                return response.read()
        except Exception, e:
            print e
            time.sleep(5)

            print "Error for URL %s: %s" % (url, datetime.datetime.now())
            print "Retrying."

            if '400' in str(e):
                return None



# Needed to write tricky unicode correctly to csv
def unicode_normalize(text):
    return text.translate({ 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22,
                            0xa0:0x20 }).encode('utf-8')


def getReactionsForStatus(status_id, access_token):

    # See http://stackoverflow.com/a/37239851 for Reactions parameters
        # Reactions are only accessable at a single-post endpoint

    base = "https://graph.facebook.com/v2.6"
    node = "/%s" % status_id
    reactions = "/?fields=" \
            "reactions.type(LIKE).limit(0).summary(total_count).as(like)" \
            ",reactions.type(LOVE).limit(0).summary(total_count).as(love)" \
            ",reactions.type(WOW).limit(0).summary(total_count).as(wow)" \
            ",reactions.type(HAHA).limit(0).summary(total_count).as(haha)" \
            ",reactions.type(SAD).limit(0).summary(total_count).as(sad)" \
            ",reactions.type(ANGRY).limit(0).summary(total_count).as(angry)"
    parameters = "&access_token=%s" % access_token
    url = base + node + reactions + parameters
    print url

    # retrieve data
    data = json.loads(request_until_succeed(url))

    return data

def processFacebookPageFeedStatus(page_id, access_token):
    #goal is take a url and create the python dictionary
    # Construct the URL string; see
    # http://stackoverflow.com/a/37239851 for Reactions parameters
    base = "https://graph.facebook.com/v2.6"
    node = "/%s" % page_id
    fields = "/?fields=message,link,permalink_url,created_time,type,name,id," + \
             "comments.limit(0).summary(true),shares,reactions." + \
             "limit(0).summary(true),from"
    parameters = "&access_token=%s" % access_token
    url = base + node + fields + parameters

    urlResponse = request_until_succeed(url)

    # retrieve data
    if urlResponse is None:
        status_id = page_id
        status_message = "N/A"
        status_author = "N/A"
        link_name = "N/A"
        status_type = "N/A"
        status_link = "N/A"
        status_permalink_url = "N/A"
        status_published = "N/A"
        num_reactions = "N/A"
        num_comments = "N/A"
        num_shares = "N/A"
        num_likes = "N/A"
        num_loves = "N/A"
        num_wows = "N/A"
        num_hahas = "N/A"
        num_sads = "N/A"
        num_angrys = "N/A"
    else:
        status = json.loads(urlResponse)
        status_id = status['id']
        status_message = '' if 'message' not in status.keys() else \
            unicode_normalize(status['message'])
        link_name = '' if 'name' not in status.keys() else \
            unicode_normalize(status['name'])
        status_type = status['type']
        status_link = '' if 'link' not in status.keys() else \
            unicode_normalize(status['link'])
        status_permalink_url = '' if 'permalink_url' not in status.keys() else \
            unicode_normalize(status['permalink_url'])
        status_author = unicode_normalize(status['from']['name'])

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

        status_published = datetime.datetime.strptime( \
            status['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
        status_published = status_published + datetime.timedelta(hours=-5)  # EST
    # best time format for spreadsheet programs:
        status_published = status_published.strftime('%Y-%m-%d %H:%M:%S')

    # Nested items require chaining dictionary keys.

        num_reactions = 0 if 'reactions' not in status else \
            status['reactions']['summary']['total_count']
        num_comments = 0 if 'comments' not in status else \
            status['comments']['summary']['total_count']
        num_shares = 0 if 'shares' not in status else \
            status['shares']['count']

    # Counts of each reaction separately; good for sentiment
    # Only check for reactions if past date of implementation:
    # http://newsroom.fb.com/news/2016/02/reactions-now-available-globally/

        reactions = getReactionsForStatus(status_id, access_token) \
            if status_published > '2016-02-24 00:00:00' else {}

        num_likes = 0 if 'like' not in reactions else \
            reactions['like']['summary']['total_count']

    # Special case: Set number of Likes to Number of reactions for pre-reaction
    # statuses

        num_likes = num_reactions if status_published < '2016-02-24 00:00:00' else \
            num_likes

        def get_num_total_reactions(reaction_type, reactions):
            if reaction_type not in reactions:
                return 0
            else:
                return reactions[reaction_type]['summary']['total_count']

        num_loves = get_num_total_reactions('love', reactions)
        num_wows = get_num_total_reactions('wow', reactions)
        num_hahas = get_num_total_reactions('haha', reactions)
        num_sads = get_num_total_reactions('sad', reactions)
        num_angrys = get_num_total_reactions('angry', reactions)


    return (status_id, status_message, status_author, link_name, status_type,
            status_link, status_permalink_url, status_published, num_reactions, num_comments,
            num_shares,  num_likes, num_loves, num_wows, num_hahas, num_sads,
            num_angrys)

def scrapeFacebookStatus():
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
            w.writerow(processFacebookPageFeedStatus(str(listofstatusids[i]), access_token))
            num_processed += 1
            if num_processed % 100 == 0:
                print "%s Statuses Processed: %s" % (num_processed,
                                                     datetime.datetime.now())
        print "\nDone!\n%s Statuses Processed in %s" % \
          (num_processed, datetime.datetime.now() - scrape_starttime)

if __name__ == '__main__':
    scrapeFacebookStatus()
