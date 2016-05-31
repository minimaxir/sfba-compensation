import urllib2
import json
import datetime
import csv
import time

#https://api.angel.co/1/tags/151282/jobs?access_token=xxx

access_token = "<FILL IN>" # DO NOT SHARE WITH ANYONE!
location_tag = 151282   # San Francisco Bay Area
# location_tag = 1664   # New York City

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

    return response.read()


# Needed to write tricky unicode correctly to csv; not present in tutorial
def unicode_normalize(text):
	return text.translate({ 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22, 0xa0:0x20 }).encode('utf-8')

def getAngelListPageFeedData(location_tag, access_token, page_num):
    
    # construct the URL string
    url = "https://api.angel.co/1/tags/%s/jobs?access_token=%s&page=%s" % (location_tag, access_token, page_num)
    
    # retrieve data
    data = json.loads(request_until_succeed(url))
    
    return data
    

def processAngelListPageFeedStatus(job):
    
    # The status is now a Python dictionary, so for top-level items,
    # we can simply call the key.
    
    # Additionally, some items may not always exist,
    # so must check for existence first
    
    job_id = job['id']
    job_title = '' if 'title' not in job.keys() else unicode_normalize(job['title'])
    job_type = '' if 'job_type' not in job.keys() else unicode_normalize(job['job_type'])
    job_city = [unicode_normalize(tag['display_name']) for tag in job['tags'] if tag['tag_type'] == 'LocationTag'][0].decode('utf-8')
    
    salary_min = '' if 'salary_min' not in job.keys() else job['salary_min']
    salary_max = '' if 'salary_max' not in job.keys() else job['salary_max']
    
    equity_cliff = '' if 'equity_cliff' not in job.keys() else job['equity_cliff']
    equity_vest = '' if 'equity_vest' not in job.keys() else job['equity_vest']
    equity_min = '' if 'equity_min' not in job.keys() else job['equity_min']
    equity_max = '' if 'equity_max' not in job.keys() else job['equity_max']
    
    roles = ', '.join([unicode_normalize(tag['display_name']) for tag in job['tags'] if tag['tag_type'] == 'RoleTag']).decode('utf-8')
    skills = ', '.join([unicode_normalize(tag['display_name']) for tag in job['tags'] if tag['tag_type'] == 'SkillTag']).decode('utf-8')

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.
    
    updated_at = datetime.datetime.strptime(job['updated_at'],'%Y-%m-%dT%H:%M:%SZ')
    updated_at = updated_at + datetime.timedelta(hours=-8) # PST
    updated_at = updated_at.strftime('%Y-%m-%d %H:%M:%S') # best time format for spreadsheet programs
    

    # return a tuple of all processed data
    return (job_id, job_title, job_type, job_city, salary_min, salary_max, equity_cliff,
    			equity_vest, equity_min, equity_max, roles, skills, updated_at)

def scrapeAngelListPageFeedStatus(location_tag, access_token):
    with open('%s_angelist_jobs.csv' % location_tag, 'wb') as file:
		w = csv.writer(file)
		w.writerow(['job_id', 'job_title', 'job_type', 'job_city', 'salary_min', 'salary_max', 'equity_cliff', 'equity_vest', 'equity_min', 'equity_max', 'roles', 'skills', 'updated_at'])

		has_next_page = True
		page = 1
		num_processed = 0   # keep a count on how many we've processed
		scrape_starttime = datetime.datetime.now()

		print "Scraping %s AngelList Page: %s\n" % (location_tag, scrape_starttime)
        
		while has_next_page:
	
			data = getAngelListPageFeedData(location_tag, access_token, page)
		
			for job in data['jobs']:
				w.writerow(processAngelListPageFeedStatus(job))
			
				# output progress occasionally to make sure code is not stalling
				num_processed += 1
				if num_processed % 100 == 0:
					print "%s Jobs Processed: %s" % (num_processed, datetime.datetime.now())
				
			# if there is no next page, we're done.
			if data['last_page'] == page:
				has_next_page = False
			else:
				page += 1
				               
	#print "\nDone!\n%s Jobs Processed in %s" % (num_processed, datetime.datetime.now() - scrape_starttime)


if __name__ == '__main__':
	scrapeAngelListPageFeedStatus(location_tag, access_token)


# The CSV can be opened in all major statistical programs. Have fun! :)
