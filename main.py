'''
Campus Wellbeing Recommender.
Check in -> state card -> recommendations -> feedback.
The feedback is saved, so the next session starts from better recommendations.
'''

from questions import run_checkin, needs_support, ask_int
from user_profile import sign_in, save_user, add_checkin, update_learned
from recommender import load_events, recommend
from display import show_card, show_support, show_recommendations


def collect_feedback(user, results):
    '''
    Ask the user to rate every recommendation and update the learned weights.
    '''

    print('\nHow well does each suggestion suit you?')
    print('   1 = not for me, 2 = okay, 3 = loved it')
    for result in results:
        event = result['event']
        rating = ask_int(event['name'] + ': ', 1, 3)
        update_learned(user, event, rating)


def main():
    '''
    Run one session for one user.
    '''

    print('Welcome to the Campus Wellbeing Recommender!')
    print('This is a self-reflection tool, not a diagnosis.')

    events = load_events('events.json')
    user = sign_in()

    checkin = run_checkin()
    add_checkin(user, checkin)
    save_user(user)

    show_card(user, checkin)
    if needs_support(checkin):
        show_support()

    # Ratings from earlier sessions are already part of the scores.
    if len(user['ratings']) > 0:
        print('\nThese suggestions use your ' + str(len(user['ratings'])) + ' earlier ratings.')

    results = recommend(user, checkin, events)
    show_recommendations(results)
    if len(results) > 0:
        collect_feedback(user, results)
        save_user(user)
        print('\nThanks! Your next recommendations will use these ratings.')

    print('\nYour answers are saved. Take care, ' + user['name'].title() + '!')


if __name__ == '__main__':
    main()
