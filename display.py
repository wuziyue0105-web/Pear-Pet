'''
Everything the user sees: the state card, the support box and the recommendations.
'''

from questions import overall_state, focus_area, today_size

LINE = '=' * 50
SUPPORT_LINK = 'https://sydney.edu.au/students/counselling-and-mental-health-support.html'

FOCUS_TEXT = {
    'stress': 'stress is your biggest load right now.',
    'mood': 'your mood is the area to look after first.',
    'belonging': 'feeling isolated is your main concern today.',
    'confidence': 'your confidence could use a boost.',
    'none': 'nothing stands out today, keep doing what works for you.',
}


def bar(value, low, high):
    '''
    Return a 10-character bar such as [######----] showing where value sits between low and high.
    Plain # and - are used so the bar looks right in every terminal font.
    '''

    filled = round((value - low) / (high - low) * 10)
    return '[' + '#' * filled + '-' * (10 - filled) + ']'


def level(value, cut_low, cut_high, words):
    '''
    Return words[0] if value <= cut_low, words[1] if value <= cut_high, otherwise words[2].
    '''

    if value <= cut_low:
        return words[0]
    elif value <= cut_high:
        return words[1]
    else:
        return words[2]


def card_row(label, value, low, high, verdict, meaning):
    '''
    Print one row of the state card: label, bar, score, verdict and what a high score means.
    '''

    score = str(value) + '/' + str(high)
    print('  ' + label.ljust(11) + bar(value, low, high) + '  ' + score.ljust(7) + verdict.ljust(18) + meaning)


def show_card(user, checkin):
    '''
    Print today's state card.
    Every row says in words what the score means, so no score is left to guess.
    '''

    size = today_size(user['personality'], checkin['energy'])
    stress = level(checkin['stress'], 5, 9, ['Low stress', 'Moderate stress', 'High stress'])
    mood = level(checkin['mood'], 28, 50, ['Very low mood', 'Low mood', 'Good mood'])
    # WHO-5 has one more band at the top.
    if checkin['mood'] > 75:
        mood = 'Very good mood'
    belonging = level(checkin['belonging'], 5, 7, ['Connected', 'Somewhat isolated', 'Isolated'])
    energy = level(checkin['energy'], 4, 7, ['Low energy', 'Medium energy', 'High energy'])
    confidence = level(checkin['confidence'], 4, 7, ['Low', 'Medium', 'High'])

    print('\n' + LINE)
    print('  Your check-in - ' + checkin['date'])
    print(LINE)
    print('  Overall: ' + overall_state(checkin['mood']))
    print()
    card_row('Stress', checkin['stress'], 0, 16, stress, '(higher = more stressed)')
    card_row('Mood', checkin['mood'], 0, 100, mood, '(higher = happier)')
    card_row('Loneliness', checkin['belonging'], 3, 9, belonging, '(higher = more isolated)')
    card_row('Energy', checkin['energy'], 0, 10, energy, '-> ' + size + ' groups today')
    card_row('Confidence', checkin['confidence'], 0, 10, confidence, '(higher = more confident)')
    print('\n  Focus today: ' + FOCUS_TEXT[focus_area(checkin)])


def show_support():
    '''
    Print support resources, shown before recommendations when scores are concerning.
    '''

    print('\n' + LINE)
    print('  Your answers suggest things feel heavy right now.')
    print('  Talking to someone can really help:')
    print('  - USyd Counselling and Mental Health Support')
    print('    ' + SUPPORT_LINK)
    print('  - Lifeline (24/7): 13 11 14')
    print(LINE)


def show_recommendations(results):
    '''
    Print each recommended event with its score and reasons.
    '''

    print('\n' + LINE)
    print('  YOUR RECOMMENDED USU EVENTS')
    print(LINE)

    if len(results) == 0:
        print('No event matches your answers this time.')
        print('Try choosing more free days or interests.')
        return

    rank = 1
    for result in results:
        event = result['event']
        print('\n' + str(rank) + '. ' + event['name'])
        print('   Club:  ' + event['club'])
        when = event['sessions'][0]
        # Weekly events have several sessions; show the next one and how many follow.
        if len(event['sessions']) > 1:
            when += '  (+' + str(len(event['sessions']) - 1) + ' more)'
        print('   When:  ' + when)
        print('   Where: ' + event['location'])
        print('   Match score: ' + str(result['score']))
        print('   Why:')
        for reason in result['reasons']:
            print('     - ' + reason)
        print('   More info: ' + event['link'])
        rank += 1
