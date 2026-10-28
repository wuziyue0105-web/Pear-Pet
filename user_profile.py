'''
Users and their profiles.
Each user has one file, users/<name>.json, holding the profile, the learned tag weights and the check-in history.
The program only ever opens the file of the user who is signed in.
'''

import json
import os

from questions import ask_choice, ask_many

USERS_FOLDER = 'users'

# The tags used in events.json, so every interest can actually be matched.
INTERESTS = ['art', 'music', 'dance', 'film', 'food', 'games', 'sport', 'outdoor',
             'language', 'study', 'career', 'volunteering', 'party', 'wellness']
COMMUNITIES = ['faith', 'cultural', 'women']

# Learned weights stay in this range so one rating cannot take over.
LEARNED_MIN = -3
LEARNED_MAX = 3


def ask_name():
    '''
    Ask for a user name made of letters and digits only, and return it in lower case.
    '''

    while True:
        name = input('\nWhat is your name? ').strip().lower()
        # Only letters and digits, so the name is always a safe file name.
        if name.isalnum():
            return name
        print('   Please use letters and digits only, with no spaces.')


def user_path(name):
    '''
    Return the path of the file that belongs to this user.
    '''

    return os.path.join(USERS_FOLDER, name + '.json')


def load_user(name):
    '''
    Return the saved user dictionary, or None if this is a new user.
    '''

    path = user_path(name)
    if not os.path.exists(path):
        return None
    with open(path) as file:
        user = json.load(file)
    # Files saved by an older version may not have ratings yet.
    if 'ratings' not in user:
        user['ratings'] = {}
    return user


def save_user(user):
    '''
    Write the user dictionary to the user's own file.
    '''

    if not os.path.exists(USERS_FOLDER):
        os.mkdir(USERS_FOLDER)
    with open(user_path(user['name']), 'w') as file:
        json.dump(user, file, indent=2)


def create_profile(name):
    '''
    Ask the profile questions and return a new user dictionary.
    '''

    print('\n--- About you (asked once, you can update it later) ---')

    print('\nAfter a long, busy week, what recharges you more?')
    print('   1 = time alone or with one close friend')
    print('   2 = it depends')
    print('   3 = going out with a group')
    answer = ask_choice('> ', ['1', '2', '3'])
    if answer == '1':
        personality = 'introvert'
    elif answer == '2':
        personality = 'ambivert'
    else:
        personality = 'extrovert'

    print('\nWhat do you enjoy? Choose any of:')
    print('   ' + ', '.join(INTERESTS))
    print('   Separate several choices with spaces, e.g. music outdoor food')
    interests = ask_many('> ', INTERESTS)

    print('\nDo you prefer indoor or outdoor activities? (indoor / outdoor / either)')
    setting = ask_choice('> ', ['indoor', 'outdoor', 'either'])

    print('\nDo you prefer quiet or active activities? (quiet / active / either)')
    atmosphere = ask_choice('> ', ['quiet', 'active', 'either'])

    print('\nWould you like events from any of these communities? ' + ', '.join(COMMUNITIES))
    print('   Separate several with spaces, or type none')
    communities = ask_many('> ', COMMUNITIES)

    return {
        'name': name,
        'personality': personality,
        'interests': interests,
        'setting': setting,
        'atmosphere': atmosphere,
        'communities': communities,
        'learned': {},
        'ratings': {},
        'checkins': [],
    }


def sign_in():
    '''
    Ask for a name, then load that user or create a new profile, and return the user.
    '''

    name = ask_name()
    user = load_user(name)

    if user is None:
        print('Nice to meet you, ' + name.title() + '! Let us set up your profile first.')
        user = create_profile(name)
        save_user(user)
        return user

    print('Welcome back, ' + name.title() + '!')
    print('Would you like to update your profile? (y/n)')
    if ask_choice('> ', ['y', 'n']) == 'y':
        new_user = create_profile(name)
        # Keep what the program has learned and the history.
        new_user['learned'] = user['learned']
        new_user['ratings'] = user['ratings']
        new_user['checkins'] = user['checkins']
        user = new_user
        save_user(user)
    return user


def add_checkin(user, checkin):
    '''
    Add today's scores to the user's history (free days are not kept).
    '''

    record = {}
    for key in ['date', 'stress', 'mood', 'belonging', 'energy', 'confidence']:
        record[key] = checkin[key]
    user['checkins'].append(record)


def update_learned(user, event, rating):
    '''
    Update the learned weight of every tag of the event from a 1-3 rating.
    3 adds one point, 1 takes one point away, 2 changes nothing.
    The rating is also saved, so the event is not recommended or asked about again.
    '''

    user['ratings'][event['name']] = rating

    if rating == 3:
        change = 1
    elif rating == 1:
        change = -1
    else:
        return

    for tag in event['tags']:
        value = user['learned'].get(tag, 0) + change
        # Keep every weight between LEARNED_MIN and LEARNED_MAX.
        value = max(LEARNED_MIN, min(LEARNED_MAX, value))
        user['learned'][tag] = value
