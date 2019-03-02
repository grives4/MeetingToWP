# Possible tagging
#   Title has "Book Group":  "Book Group"
#   Title has "Gathering":  "Gathering"
#   Title or body has "Volunteer":  "Volunteering"
#   Title has "Discussion Group": "Discussion Group"
#   Title has "Role": "Games"
#   Title or body has "Dinner" or "Brunch" or "Potluck":  "Community"
#   Title or body has "Tramps" or "Trivia": Trivia night
#   Title or body has "Broadcast" or "Taping": Broadcast


import pdb
import json
import time
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost, GetPost, DeletePost
from wordpress_xmlrpc.methods.users import GetUserInfo
import meetup.api
from datetime import datetime
from pprint import pprint

def getTags(title, body):
    textToSearch = (title + ' ' + body).lower()
    criteria = {'Book/Dicussion Group': ['book'],
                'Community': ['gathering', 'tramps', 'trivia', 'potluck', 'brunch', 'dinner', 'lunch', 'game', 'role-play'],
                'Volunteering': ['volunteer'],
                'Broadcast/Podcast': ['broadcast','podcast', 'taping'],
                'Trivia Night': ['tramps','trivia'],
                'Potluck': ['potluck'],
                'Brunch/Lunch/Dinner': ['brunch','dinner','lunch'],
                'Lecture': ['lecture', 'philosophy', 'gathering'],
                'Games': ['game','role-play']}
    
    tags = []
    for key, values in criteria.items():
        for value in values:
            if value in textToSearch:
                tags.append(key)
                continue

    if not tags:
        tags = ['Community']  

    return tags


def wpGetLastUpdatedDate(eventType, eventID,currentWPEvents):
    for event in currentWPEvents:
        if eventType == 'meetup':
            meetupIDDictionary = next((item for item in event.custom_fields if item["key"] == "meetupID"),None)
            if meetupIDDictionary is not None:
                if meetupIDDictionary['value'] == eventID:
                    meetupLastUpdatedDictionary = next((item for item in event.custom_fields if item["key"] == "meetupLastUpdated"),None)
                    return [meetupLastUpdatedDictionary['value'], event.id]
    
    return [0,0]

def deleteWPEvent(wpID):
    configuration = json.loads(open('config.json').read())
    wp = Client('https://greateraustinsecularhub.org/xmlrpc2.php', configuration['wpUser'], configuration['wpKey'])
    result = wp.call(DeletePost(wpID))
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
        
        eventTags = getTags(event['name'], event['description'])
        post.terms_names = {
            'post_tag': eventTags,
            #'venue': [eventLocation],
            'organizer': [event['group']['name']]
        }
        
        eventStartDateTime_Datetime = datetime.fromtimestamp((event['time']+event['utc_offset'])/1000)  
        eventEndDateTime_Datetime = datetime.fromtimestamp((event['time']+event['utc_offset']+event['duration'])/1000) 

        eventStartTime = eventStartDateTime_Datetime.strftime("%H:%M")
        eventEndTime = eventEndDateTime_Datetime.strftime("%H:%M")
        eventStartTime_Pretty = eventStartDateTime_Datetime.strftime("%-I:%M %P")
        eventEndTime_Pretty = eventEndDateTime_Datetime.strftime("%-I:%M %P")
        eventStartDateTime = eventStartDateTime_Datetime.strftime("%Y-%m-%d")
        eventEndDateTime = eventEndDateTime_Datetime.strftime("%Y-%m-%d")
        post.excerpt = configuration['wpInfoBox'] % (event['group']['name'], eventStartTime_Pretty, eventEndTime_Pretty, eventLocation, ', '.join(eventTags), event['event_url'], event['event_url'], event['description'][:200])
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
                            {'key': 'meetupLastUpdated', 'value': int(event['updated']/1000)}]
    #pdb.set_trace()
    post.post_status = 'publish'
    #pprint(post)
    post.id = wp.call(NewPost(post))
    time.sleep(0.5)
    return

#Query configuration file
configuration = json.loads(open('config.json').read())

#Pull events on WordPress
wp = Client('https://greateraustinsecularhub.org/xmlrpc2.php', configuration['wpUser'], configuration['wpKey'])
currentWPEvents = wp.call(GetPosts({'post_type': 'events', 'number': 10000}))

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
        [lastUpdated, wpID] = wpGetLastUpdatedDate('meetup', event['id'],currentWPEvents)
 
        #If the meeting needs to be updated, delete it.
        if int(lastUpdated) < int(event['updated']/1000) and lastUpdated != 0:
            print("delete event" + str(wpID))
            #pdb.set_trace()
            deleteWPEvent(str(wpID))
            lastUpdated = 0
            print('Meetup deleted due to last update too old.')

        #If the meeting doesn't exist create it.    
        if lastUpdated == 0:
            print("Creating Event")
            #pprint(event)
            #print("WP")
            createWPEvent('meetup', event)
      
