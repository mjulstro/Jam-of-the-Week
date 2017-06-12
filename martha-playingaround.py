from facepy import GraphAPI
import urllib2
import json
import datetime
import csv
import time

# app_id = "<FILL IN>"
# app_secret = "<FILL IN>" # DO NOT SHARE WITH ANYONE!
group_id = "558429457587216"

# access_token = app_id + "|" + app_secret
access_token = "318577115222655|623cad8bc46ebcb08ca7bc225ab15860"
def request_until_succeed(url):
    time.sleep(100)
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

    return response.read()


# Needed to write tricky unicode correctly to csv
def unicode_normalize(text):
    return text.translate({0x2018: 0x27, 0x2019: 0x27, 0x201C: 0x22, 0x201D: 0x22,
                           0xa0: 0x20}).encode('utf-8')

def getFacebookPageFeedData(group_id, access_token, num_statuses):
    # Construct the URL string; see
    # http://stackoverflow.com/a/37239851 for Reactions parameters
    base = "https://graph.facebook.com/v2.6"
    node = "/%s/feed" % group_id
    fields = "/?fields=permalink_url,id"
    parameters = "&limit=%s&access_token=%s" % (num_statuses, access_token)
    url = base + node + fields + parameters

    # retrieve data
    data = json.loads(request_until_succeed(url))

    return data

def processFacebookPageFeedStatus(status, access_token):
    status_id = status['id']
    # status_message = '' if 'message' not in status.keys() else \
    #         unicode_normalize(status['message'])
    # link_name = '' if 'name' not in status.keys() else \
    #     unicode_normalize(status['name'])
    # status_type = status['type']
    # status_link = '' if 'link' not in status.keys() else \
    #     unicode_normalize(status['link'])
    status_permalink_url = '' if 'permalink_url' not in status.keys() else \
        unicode_normalize(status['permalink_url'])
    # status_author = unicode_normalize(status['from']['name'])

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

    #status_published = datetime.datetime.strptime(\
             #status['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
    #status_published = status_published + datetime.timedelta(hours=-5) # EST
    # # best time format for spreadsheet programs:
    #status_published = status_published.strftime('%Y-%m-%d %H:%M:%S')

    # return a tuple of all processed data

    return (status_id, status_permalink_url)

def scrapeFacebookPageFeedStatus(group_id, access_token):
    with open('%s_facebook_statuses.csv' % group_id, 'wb') as file:
        w = csv.writer(file)
        w.writerow(["permalink_url"]) #change this to ["status_id", "permalink_url"]

        has_next_page = True
        num_processed = 0  # keep a count on how many we've processed
        scrape_starttime = datetime.datetime.now()

        print "Scraping %s Facebook Page: %s\n" % \
              (group_id, scrape_starttime)

        statuses = getFacebookPageFeedData(group_id, access_token, 500)

        while has_next_page:
            for status in statuses['data']:
                w.writerow(processFacebookPageFeedStatus(status, access_token))
                # # Ensure it is a status with the expected metadata
                # if 'reactions' in status:
                #     w.writerow(processFacebookPageFeedStatus(status, \
                #                                             access_token))

                # output progress occasionally to make sure code is not
                # stalling
                num_processed += 1
                if num_processed % 100 == 0:
                    print "%s Statuses Processed: %s" % (num_processed,
                                                         datetime.datetime.now())

            # if there is no next page, we're done.
            if 'paging' in statuses.keys():
                statuses = json.loads(request_until_succeed(
                    statuses['paging']['next']))
            else:
                has_next_page = False

        print "\nDone!\n{} Statuses Processed in {}" \
            .format(num_processed, datetime.datetime.now() - scrape_starttime)


if __name__ == '__main__':
    scrapeFacebookPageFeedStatus(group_id, access_token)