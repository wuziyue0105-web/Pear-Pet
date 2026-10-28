'''
Web version of the Campus Wellbeing Recommender.
Runs a small server on this computer and opens the app in the browser.
All scoring, saving and recommending is done by the same modules main.py uses;
this file only passes answers between the page (web/) and those modules.
Run with: python3 web_app.py
'''

import datetime
import json
import os
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

from questions import (PSS4_QUESTIONS, WHO5_QUESTIONS, UCLA3_QUESTIONS, DAYS,
                       score_pss4, score_who5, score_ucla3, today_size,
                       overall_state, focus_area, needs_support)
from user_profile import (INTERESTS, COMMUNITIES, load_user, save_user,
                          add_checkin, update_learned)
from recommender import load_events, recommend
from display import level, FOCUS_TEXT, SUPPORT_LINK

PORT = 8001
HERE = os.path.dirname(os.path.abspath(__file__))
WEB_FOLDER = os.path.join(HERE, 'web')

# Answer options as [value, words], in the order the scales list them.
PSS4_CHOICES = [[0, 'Never'], [1, 'Almost never'], [2, 'Sometimes'],
                [3, 'Fairly often'], [4, 'Very often']]
WHO5_CHOICES = [[5, 'All of the time'], [4, 'Most of the time'],
                [3, 'More than half of the time'], [2, 'Less than half of the time'],
                [1, 'Some of the time'], [0, 'At no time']]
UCLA3_CHOICES = [[1, 'Hardly ever'], [2, 'Some of the time'], [3, 'Often']]

PERSONALITIES = ['introvert', 'ambivert', 'extrovert']
SETTINGS = ['indoor', 'outdoor', 'either']
ATMOSPHERES = ['quiet', 'active', 'either']

# For each score: is a lower number the better direction?
LOWER_IS_BETTER = {'stress': True, 'mood': False, 'belonging': True,
                   'energy': False, 'confidence': False}


class InputError(Exception):
    '''
    Raised when the page sends an answer the program cannot accept.
    '''


def check_name(name):
    '''
    Return the name in lower case if it is letters and digits only, otherwise raise InputError.
    '''

    name = str(name).strip().lower()
    if not name.isalnum():
        raise InputError('Please use letters and digits only, with no spaces.')
    return name


def check_int(value, low, high, what):
    '''
    Return value if it is a whole number from low to high, otherwise raise InputError.
    '''

    if type(value) != int or not low <= value <= high:
        raise InputError(what + ' must be a whole number from ' + str(low) + ' to ' + str(high) + '.')
    return value


def check_answers(values, count, low, high, what):
    '''
    Check a list of scale answers and return it.
    '''

    if type(values) != list or len(values) != count:
        raise InputError('Please answer every ' + what + ' question.')
    for value in values:
        check_int(value, low, high, what + ' answers')
    return values


def check_list(values, options, what):
    '''
    Return the values that are in options, without repeats.
    '''

    if type(values) != list:
        raise InputError(what + ' must be a list.')
    chosen = []
    for value in values:
        if value not in options:
            raise InputError('Not recognised: ' + str(value) + '.')
        if value not in chosen:
            chosen.append(value)
    return chosen


def public_user(user):
    '''
    Return the parts of the user dictionary the page shows.
    '''

    return {
        'name': user['name'],
        'personality': user['personality'],
        'interests': user['interests'],
        'setting': user['setting'],
        'atmosphere': user['atmosphere'],
        'communities': user['communities'],
        'learned': user['learned'],
        'ratings': user['ratings'],
        'checkins': user['checkins'],
    }


def card_row(key, label, value, low, high, cuts, verdict, meaning):
    '''
    Return one row of the state card as a dictionary.
    cuts are the scores where one band ends and the next begins.
    '''

    return {'key': key, 'label': label, 'value': value, 'low': low, 'high': high,
            'cuts': cuts, 'verdict': verdict, 'meaning': meaning}


def state_card(user, checkin):
    '''
    Return today's state card: the same bands and words as show_card in display.py.
    '''

    size = today_size(user['personality'], checkin['energy'])
    mood = level(checkin['mood'], 28, 50, ['Very low mood', 'Low mood', 'Good mood'])
    if checkin['mood'] > 75:
        mood = 'Very good mood'

    rows = [
        card_row('stress', 'Stress', checkin['stress'], 0, 16, [5, 9],
                 level(checkin['stress'], 5, 9, ['Low stress', 'Moderate stress', 'High stress']),
                 'Higher means more stressed'),
        card_row('mood', 'Mood', checkin['mood'], 0, 100, [28, 50, 75], mood,
                 'Higher means happier'),
        card_row('belonging', 'Loneliness', checkin['belonging'], 3, 9, [5, 7],
                 level(checkin['belonging'], 5, 7, ['Connected', 'Somewhat isolated', 'Isolated']),
                 'Higher means more isolated'),
        card_row('confidence', 'Confidence', checkin['confidence'], 1, 10, [4, 7],
                 level(checkin['confidence'], 4, 7, ['Low', 'Medium', 'High']),
                 'Higher means more confident'),
        card_row('energy', 'Social energy', checkin['energy'], 1, 10, [4, 7],
                 level(checkin['energy'], 4, 7, ['Low energy', 'Medium energy', 'High energy']),
                 size.title() + ' groups suit you today'),
    ]

    # Compare with the check-in before this one, if there is one.
    changes = []
    if len(user['checkins']) >= 2:
        before = user['checkins'][-2]
        for row in rows:
            diff = checkin[row['key']] - before[row['key']]
            better = (diff < 0) == LOWER_IS_BETTER[row['key']]
            changes.append({'label': row['label'], 'diff': diff, 'better': diff != 0 and better})

    focus = focus_area(checkin)
    return {
        'date': checkin['date'],
        'overall': overall_state(checkin['mood']),
        'rows': rows,
        'focus': focus,
        'focus_text': FOCUS_TEXT[focus],
        'size': size,
        'support': needs_support(checkin),
        'support_link': SUPPORT_LINK,
        'days': checkin['days'],
        'changes': changes,
        'before_date': user['checkins'][-2]['date'] if len(user['checkins']) >= 2 else None,
    }


def public_results(results):
    '''
    Return the recommendations as plain dictionaries for the page.
    '''

    output = []
    for result in results:
        event = result['event']
        output.append({
            'name': event['name'],
            'club': event['club'],
            'when': event['sessions'][0],
            'more_sessions': len(event['sessions']) - 1,
            'location': event['location'],
            'price': event['price'],
            'link': event['link'],
            'tags': event['tags'],
            'size': event['size'],
            'score': result['score'],
            'reasons': result['reasons'],
        })
    return output


def handle_signin(body, events):
    '''
    Return the saved user, or say that this name is new.
    '''

    name = check_name(body.get('name', ''))
    user = load_user(name)
    if user is None:
        return {'is_new': True, 'name': name, 'user': None}
    return {'is_new': False, 'name': name, 'user': public_user(user)}


def handle_profile(body, events):
    '''
    Save the profile answers, keeping what was learned and the history.
    '''

    name = check_name(body.get('name', ''))
    personality = body.get('personality')
    setting = body.get('setting')
    atmosphere = body.get('atmosphere')
    if personality not in PERSONALITIES:
        raise InputError('Please choose what recharges you.')
    if setting not in SETTINGS or atmosphere not in ATMOSPHERES:
        raise InputError('Please choose a setting and an atmosphere.')
    interests = check_list(body.get('interests', []), INTERESTS, 'Interests')
    if len(interests) == 0:
        raise InputError('Please choose at least one interest.')
    communities = check_list(body.get('communities', []), COMMUNITIES, 'Communities')

    user = {
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
    old = load_user(name)
    if old is not None:
        user['learned'] = old['learned']
        user['ratings'] = old['ratings']
        user['checkins'] = old['checkins']
    save_user(user)
    return {'user': public_user(user)}


def handle_checkin(body, events):
    '''
    Score the answers, save the check-in and return the state card and recommendations.
    '''

    name = check_name(body.get('name', ''))
    user = load_user(name)
    if user is None:
        raise InputError('Please set up your profile first.')

    pss = check_answers(body.get('pss'), len(PSS4_QUESTIONS), 0, 4, 'stress')
    who = check_answers(body.get('who'), len(WHO5_QUESTIONS), 0, 5, 'mood')
    ucla = check_answers(body.get('ucla'), len(UCLA3_QUESTIONS), 1, 3, 'belonging')
    energy = check_int(body.get('energy'), 1, 10, 'Energy')
    confidence = check_int(body.get('confidence'), 1, 10, 'Confidence')
    days = check_list(body.get('days', []), DAYS, 'Free days')
    if len(days) == 0:
        raise InputError('Please choose at least one free day.')

    checkin = {
        'date': datetime.date.today().strftime('%a %d %b %Y'),
        'stress': score_pss4(pss),
        'mood': score_who5(who),
        'belonging': score_ucla3(ucla),
        'energy': energy,
        'confidence': confidence,
        'days': days,
    }
    add_checkin(user, checkin)
    save_user(user)

    # Ratings from earlier sessions are already part of the scores.
    earlier = len(user['ratings'])
    results = recommend(user, checkin, events)
    return {
        'user': public_user(user),
        'card': state_card(user, checkin),
        'earlier_ratings': earlier,
        'recommendations': public_results(results),
    }


def handle_feedback(body, events):
    '''
    Update the learned weights from the 1-3 ratings and save them.
    '''

    name = check_name(body.get('name', ''))
    user = load_user(name)
    if user is None:
        raise InputError('Please sign in again.')

    ratings = body.get('ratings', {})
    if type(ratings) != dict or len(ratings) == 0:
        raise InputError('Please rate every suggestion.')

    by_name = {}
    for event in events:
        by_name[event['name']] = event

    for event_name in ratings:
        if event_name not in by_name:
            raise InputError('Unknown event: ' + str(event_name))
        rating = check_int(ratings[event_name], 1, 3, 'Ratings')
        update_learned(user, by_name[event_name], rating)
    save_user(user)
    return {'user': public_user(user)}


def handle_meta(events):
    '''
    Return the questions and options the page needs to draw its forms.
    '''

    return {
        'pss': {'questions': PSS4_QUESTIONS, 'choices': PSS4_CHOICES},
        'who': {'questions': WHO5_QUESTIONS, 'choices': WHO5_CHOICES},
        'ucla': {'questions': UCLA3_QUESTIONS, 'choices': UCLA3_CHOICES},
        'interests': INTERESTS,
        'communities': COMMUNITIES,
        'days': DAYS,
        'event_count': len(events),
    }


ROUTES = {
    '/api/signin': handle_signin,
    '/api/profile': handle_profile,
    '/api/checkin': handle_checkin,
    '/api/feedback': handle_feedback,
}


class Handler(SimpleHTTPRequestHandler):
    '''
    Serves the files in web/ and answers the /api/ requests.
    '''

    events = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_FOLDER, **kwargs)

    def send_json(self, status, data):
        '''
        Send data back to the page as JSON.
        '''

        text = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(text)))
        self.end_headers()
        self.wfile.write(text)

    def do_GET(self):
        if self.path == '/api/meta':
            self.send_json(200, handle_meta(self.events))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path not in ROUTES:
            self.send_json(404, {'error': 'Not found.'})
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length) or b'{}')
            if type(body) != dict:
                raise InputError('Expected a JSON object.')
            self.send_json(200, ROUTES[self.path](body, self.events))
        except InputError as error:
            self.send_json(400, {'error': str(error)})
        except json.JSONDecodeError:
            self.send_json(400, {'error': 'Expected a JSON object.'})

    def log_message(self, format, *args):
        # Keep the terminal quiet; only startup messages are printed.
        pass


def main():
    '''
    Start the server and open the app in the browser.
    '''

    # users/ and events.json are found relative to this folder.
    os.chdir(HERE)
    Handler.events = load_events('events.json')

    # Only this computer can reach the server.
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    url = 'http://127.0.0.1:' + str(PORT) + '/'
    print('Campus Wellbeing is running at ' + url)
    print('Press Ctrl+C to stop.')
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped. Take care!')


if __name__ == '__main__':
    main()
