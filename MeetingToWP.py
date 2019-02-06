#https://python-wordpress-xmlrpc.readthedocs.io/en/latest/index.html

import pdb
import json
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost, EditPost, GetPost
from wordpress_xmlrpc.methods.users import GetUserInfo
from wordpress_xmlrpc import WordPressPost

configuration = json.loads(open('config.json').read())

wp = Client('https://greateraustinsecularhub.org/xmlrpc2.php', configuration['MeetupUser'], configuration['MeetupKey'])

posts = wp.call(GetPosts({'post_type': 'events'}))
post = wp.call(GetPost(73))
print(post.custom_fields)
pdb.set_trace()
post = WordPressPost()
pdb.set_trace()
post.title = 'Create Feb 23 event'
post.post_type = 'events'
post.terms_names = {
    'post_tag': ['Volunteering'],
    'calendar': ['Austin Humanist Community'],
    'venue': ['Freethought Library'],
    'organizer': ['CFI Austin']
}
pdb.set_trace()
post.custom_fields = {'event_start': '2019-02-21 13:00:00', 'event_end': '2019-02-21 15:00:00'}
#Date
#Time
#Location
post.content = 'Something is happenning!'
post.id = wp.call(NewPost(post))

post.post_status = 'publish'
wp.call(EditPost(post.id, post))

# wp_rhc_events
# event_start
# event_end

