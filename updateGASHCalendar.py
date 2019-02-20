# Possible tagging
#   Title has "Book Group":  "Book Group"
#   Title has "Gathering":  "Gathering"
#   Title or body has "Volunteer":  Volunteering
#   Title has "Discussion Group": "Discussion Group"

import pdb
import json
import time
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost, GetPost, DeletePost
from wordpress_xmlrpc.methods.users import GetUserInfo
import meetup.api
from datetime import datetime


def wpGetLastUpdatedDate(eventType, eventID):
    configuration = json.loads(open('config.json').read())
    wp = Client('https://greateraustinsecularhub.org/xmlrpc2.php', configuration['wpUser'], configuration['wpKey'])
    if eventType == 'meetup':
        pass
    return 0

def deleteWPEvent(eventType, eventID):
    configuration = json.loads(open('config.json').read())
    wp = Client('https://greateraustinsecularhub.org/xmlrpc2.php', configuration['wpUser'], configuration['wpKey'])
    result = wp.call(DeletePost(734))
    return result

def createWPEvent(eventType, event):
    configuration = json.loads(open('config.json').read())
    wp = Client('https://greateraustinsecularhub.org/xmlrpc2.php', configuration['wpUser'], configuration['wpKey'])
    post = WordPressPost()
    post.post_type = 'events'
    if eventType == 'meetup':
        post.title = event['name']
        post.content = ""

        #If the event is public, note the details.
        eventLocation = "See event details"
        if event['visibility'] == 'public':
            eventLocation = event['venue']['name']
        
        post.terms_names = {
            'post_tag': [],
            'venue': [eventLocation],
            'organizer': [event['group']['name']]
        }
        
        eventStartDateTime_Datetime = datetime.fromtimestamp(event['time']/1000)  
        eventEndDateTime_Datetime = datetime.fromtimestamp((event['time']+event['duration'])/1000) 

        eventStartTime = eventStartDateTime_Datetime.strftime("%H:%M")
        eventEndTime = eventEndDateTime_Datetime.strftime("%H:%M")
        eventStartDateTime = eventStartDateTime_Datetime.strftime("%Y-%m-%d")
        eventEndDateTime = eventEndDateTime_Datetime.strftime("%Y-%m-%d")
        eventTags = ''
        post.excerpt = configuration['wpInfoBox'] % (eventStartTime, eventEndTime, eventLocation, event['group']['name'], eventTags, event['event_url'], event['event_url'], event['description'][:200])
        post.custom_fields = [{'key': 'fc_allday','value': 0},
                            {'key': 'fc_start','value':eventStartDateTime},
                            {'key': 'fc_start_time','value': eventStartTime},
                            {'key':'fc_end','value':eventEndDateTime},
                            {'key':'fc_end_time','value': eventEndTime},
                            {'key':'fc_interval', 'value':''},
                            {'key':'fc_end_interval', 'value':''},
                            {'key': 'fc_dow_except', 'value':''},
                            {'key':'fc_color', 'value':'#'},
                            {'key':'fc_text_color', 'value':'#'},
                            {'key':'fc_click_link', 'value':'view'},
                            {'key':'fc_click_target', 'value':'_blank'},
                            {'key':'fc_exdate', 'value':''},
                            {'key':'fc_rdate', 'value':''},
                            {'key':'fc_event_map', 'value':''},
                            {'key':'enable_featuredimage', 'value':1},
                            {'key':'enable_postinfo', 'value':1},
                            {'key':'enable_postinfo_image', 'value':1},
                            {'key':'enable_venuebox', 'value':1},
                            {'key':'enable_venuebox_gmap', 'value':1},
                            {'key':'rhc_top_image', 'value':''},
                            {'key':'rhc_dbox_image', 'value':''},
                            {'key':'rhc_tooltip_image', 'value':''},
                            {'key':'rhc_month_image', 'value':''},
                            {'key': 'meetupID', 'value': event['id']},
                            {'key': 'meetupLastUpdated', 'value': event['updated']/1000}]
        
    #pdb.set_trace()
    post.post_status = 'publish'
    post.id = wp.call(NewPost(post))
    time.sleep(0.5)


    return

#Query configuration file
configuration = json.loads(open('config.json').read())

#Pull events on WordPress
wp = Client('https://greateraustinsecularhub.org/xmlrpc2.php', configuration['wpUser'], configuration['wpKey'])
currentWPEvents = wp.call(GetPosts({'post_type': 'events'}))

#Loop through meetup groups
meetupGroupNames = configuration['meetupGroups']
meetupClient = meetup.api.Client(configuration['meetupKey'])
for meetupGroupName in meetupGroupNames:
    #Query the meet up information
    print('Searching ' + meetupGroupName)
    tempGroupInfo = meetupClient.GetGroup({'urlname': meetupGroupName})
    tempGroupID = tempGroupInfo.id
    tempOrganizer = tempGroupInfo.name
    tempEvents = meetupClient.GetEvents({'group_id': tempGroupID})
    
    #Iterate through the meetings
    for event in tempEvents.results:
        
        #Check to see if the meeting already exists in wp
        lastUpdated = wpGetLastUpdatedDate('meetup', event['id'])

        #If the meeting needs to be updated, delete it.
        if lastUpdated < event['updated'] and lastUpdated != 0:
            deleteWPEvent('meetup', event['id'])
            lastUpdated = 0

        #If the meeting doesn't exist create it.    
        if lastUpdated == 0:
            createWPEvent('meetup', event)

        #pdb.set_trace()        