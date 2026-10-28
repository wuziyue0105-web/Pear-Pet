'''
Check-in questions and how they are scored.
Stress uses the PSS-4, mood uses the WHO-5 and belonging uses the 3-item UCLA Loneliness Scale.
Social energy and confidence are self-rated.
'''

import datetime

# PSS-4 (Perceived Stress Scale, 4 items), asked about the last month.
PSS4_QUESTIONS = [
    'In the last month, how often have you felt that you were unable to control the important things in your life?',
    'In the last month, how often have you felt confident about your ability to handle your personal problems?',
    'In the last month, how often have you felt that things were going your way?',
    'In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?',
]
PSS4_OPTIONS = '0 = Never, 1 = Almost never, 2 = Sometimes, 3 = Fairly often, 4 = Very often'
# Questions 2 and 3 (indexes 1 and 2) are positively worded, so they are reverse scored.
PSS4_REVERSED = [1, 2]

# WHO-5 Well-Being Index, asked about the last two weeks.
WHO5_QUESTIONS = [
    'Over the last two weeks, I have felt cheerful and in good spirits.',
    'Over the last two weeks, I have felt calm and relaxed.',
    'Over the last two weeks, I have felt active and vigorous.',
    'Over the last two weeks, I woke up feeling fresh and rested.',
    'Over the last two weeks, my daily life has been filled with things that interest me.',
]
WHO5_OPTIONS = ('5 = All of the time, 4 = Most of the time, 3 = More than half of the time,\n'
                '   2 = Less than half of the time, 1 = Some of the time, 0 = At no time')

# 3-item UCLA Loneliness Scale.
UCLA3_QUESTIONS = [
    'How often do you feel that you lack companionship?',
    'How often do you feel left out?',
    'How often do you feel isolated from others?',
]
UCLA3_OPTIONS = '1 = Hardly ever, 2 = Some of the time, 3 = Often'

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# Group size that suits today, by personality and today's social energy band.
SIZE_TABLE = {
    'introvert': ['small', 'small', 'medium'],
    'ambivert': ['small', 'medium', 'medium'],
    'extrovert': ['small', 'medium', 'large'],
}

# Cut-offs that decide when support resources are shown first.
HIGH_STRESS = 12
LOW_MOOD = 28
# A need value (0-1) must reach this level to be shown as today's focus.
FOCUS_LEVEL = 0.4


def ask_int(prompt, low, high):
    '''
    Keep asking until the user types a whole number from low to high, then return it.
    '''

    while True:
        answer = input(prompt).strip()
        # isdigit() rejects empty input, letters and minus signs.
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print('   Please enter a whole number from ' + str(low) + ' to ' + str(high) + '.')


def ask_choice(prompt, options):
    '''
    Keep asking until the user types one of the options, then return it in lower case.
    '''

    while True:
        answer = input(prompt).strip().lower()
        if answer in options:
            return answer
        print('   Please type one of: ' + ', '.join(options))


def ask_many(prompt, options):
    '''
    Ask for several options separated by spaces and return the valid ones without repeats.
    Typing "none" returns an empty list.
    '''

    while True:
        words = input(prompt).strip().lower().split()
        if words == ['none']:
            return []

        chosen = []
        unknown = []
        for word in words:
            if word in options:
                if word not in chosen:
                    chosen.append(word)
            else:
                unknown.append(word)

        if len(unknown) > 0:
            print('   Not recognised: ' + ', '.join(unknown) + '. Please try again.')
        elif len(chosen) == 0:
            print('   Please choose at least one, or type none.')
        else:
            return chosen


def ask_days():
    '''
    Ask which days the user is free and return them as a list such as ['Tue', 'Sat'].
    '''

    lower_days = []
    for day in DAYS:
        lower_days.append(day.lower())

    print('\nWhich days are you free this week? e.g. tue sat')
    chosen = ask_many('> ', lower_days + ['all'])
    if 'all' in chosen:
        return DAYS[:]

    days = []
    for day in chosen:
        days.append(day.title())
    return days


def ask_scale(title, questions, options, low, high):
    '''
    Ask every question of one scale and return the list of answers.
    '''

    print('\n--- ' + title + ' ---')
    print('   ' + options)
    answers = []
    number = 1
    for question in questions:
        print('\n' + str(number) + '. ' + question)
        answers.append(ask_int('> ', low, high))
        number += 1
    return answers


def score_pss4(answers):
    '''
    Return the PSS-4 total from 0 to 16; a higher score means more stress.
    '''

    total = 0
    for i in range(len(answers)):
        if i in PSS4_REVERSED:
            total += 4 - answers[i]
        else:
            total += answers[i]
    return total


def score_who5(answers):
    '''
    Return the WHO-5 score as a percentage from 0 to 100; a higher score means better wellbeing.
    '''

    return sum(answers) * 4


def score_ucla3(answers):
    '''
    Return the UCLA-3 total from 3 to 9; 6 or more means feeling lonely.
    '''

    return sum(answers)


def today_size(personality, energy):
    '''
    Combine personality (trait) with today's social energy (state) and return the best group size.
    '''

    if energy <= 4:
        band = 0
    elif energy <= 7:
        band = 1
    else:
        band = 2
    return SIZE_TABLE[personality][band]


def run_checkin():
    '''
    Ask all check-in questions and return the results as a dictionary.
    '''

    pss = ask_scale('Stress (PSS-4)', PSS4_QUESTIONS, PSS4_OPTIONS, 0, 4)
    who = ask_scale('Mood (WHO-5)', WHO5_QUESTIONS, WHO5_OPTIONS, 0, 5)
    ucla = ask_scale('Belonging (UCLA-3)', UCLA3_QUESTIONS, UCLA3_OPTIONS, 1, 3)

    print('\n--- Today ---')
    print('\nHow much energy do you have for being around people today? (1-10)')
    energy = ask_int('> ', 1, 10)
    print('\nHow confident do you feel in yourself right now? (1-10)')
    confidence = ask_int('> ', 1, 10)
    days = ask_days()

    return {
        'date': datetime.date.today().strftime('%a %d %b %Y'),
        'stress': score_pss4(pss),
        'mood': score_who5(who),
        'belonging': score_ucla3(ucla),
        'energy': energy,
        'confidence': confidence,
        'days': days,
    }


def overall_state(mood):
    '''
    Turn the WHO-5 percentage into an overall state name.
    '''

    if mood <= 28:
        return 'RUNNING ON EMPTY'
    elif mood <= 50:
        return 'STRETCHED THIN'
    elif mood <= 75:
        return 'STEADY'
    else:
        return 'THRIVING'


def focus_area(checkin):
    '''
    Return the area that needs the most attention today, or 'none' if every area looks fine.
    Each score is turned into a 0-1 "need" value so different scales can be compared.
    '''

    needs = {
        'stress': checkin['stress'] / 16,
        'mood': (100 - checkin['mood']) / 100,
        'belonging': (checkin['belonging'] - 3) / 6,
        'confidence': (10 - checkin['confidence']) / 9,
    }

    best = 'stress'
    for area in needs:
        if needs[area] > needs[best]:
            best = area

    # Below this level nothing really stands out.
    if needs[best] < FOCUS_LEVEL:
        return 'none'
    return best


def needs_support(checkin):
    '''
    Return True when stress is very high or mood is very low.
    '''

    return checkin['stress'] >= HIGH_STRESS or checkin['mood'] <= LOW_MOOD
