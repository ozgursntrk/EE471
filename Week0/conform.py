# Programming for the Puzzled -- Srini Devadas
# You Will All Conform -- solutions to Exercises 1, 2 and 3
# Input:  a list of 'F' (forward cap), 'B' (backward cap) and 'H' (bareheaded)
# Output: the fewest commands (printed) so that every cap faces the same way

cap1 = ['F', 'F', 'B', 'B', 'B', 'F', 'B',
        'B', 'B', 'F', 'F', 'B', 'F']

cap2 = ['F', 'F', 'B', 'B', 'B', 'F', 'B',
        'B', 'B', 'F', 'F', 'F', 'F']

cap3 = ['F', 'F', 'B', 'H', 'B', 'F', 'B',
        'B', 'B', 'F', 'H', 'F', 'F']


def say(start, end):
    """Exercise 1: one person -> 'Person ... cap!', a group -> 'People ... caps!'"""
    if start == end:
        print('Person in position', start, 'flip your cap!')
    else:
        print('People in positions', start, 'through', end, 'flip your caps!')


def pleaseConform(caps):
    """Exercises 1 and 3: natural commands, and bareheaded people ('H') are skipped."""
    start = None          # beginning of the current interval (None = no open interval)
    forward = backward = 0
    intervals = []        # (start, end, direction)

    for i in range(len(caps)):
        if caps[i] == 'H':
            # Exercise 3: a bareheaded person closes the current interval
            if start is not None:
                intervals.append((start, i - 1, caps[start]))
                start = None
        elif start is None:
            start = i     # first cap after the beginning of the line or after an 'H'
        elif caps[i] != caps[start]:
            intervals.append((start, i - 1, caps[start]))
            start = i

    # Add the last interval (if the line does not end with an 'H')
    if start is not None:
        intervals.append((start, len(caps) - 1, caps[start]))

    for interval in intervals:
        if interval[2] == 'F':
            forward += 1
        else:
            backward += 1

    # Flip the direction that has fewer intervals
    if forward < backward:
        flip = 'F'
    else:
        flip = 'B'

    for start, end, direction in intervals:
        if direction == flip:
            say(start, end)


def pleaseConformOnepass(caps):
    """Exercise 2: one pass, natural commands, and no crash on an empty list."""
    if len(caps) == 0:
        return            # nobody in line -> nothing to say

    caps = caps + [caps[0]]   # sentinel: closes the last interval
    for i in range(1, len(caps)):
        if caps[i] != caps[i - 1]:
            if caps[i] != caps[0]:
                start = i              # remember the beginning (do not print yet)
            else:
                say(start, i - 1)      # the interval ended at i - 1


if __name__ == '__main__':
    for name, line in [('cap1', cap1), ('cap2', cap2)]:
        print(f'--- pleaseConform({name}) ---')
        pleaseConform(line)
        print(f'--- pleaseConformOnepass({name}) ---')
        pleaseConformOnepass(line)

    print('--- pleaseConform(cap3)  (Exercise 3, with bareheaded people) ---')
    pleaseConform(cap3)

    print('--- pleaseConformOnepass([])  (Exercise 2, empty list) ---')
    pleaseConformOnepass([])
    print('(no crash)')