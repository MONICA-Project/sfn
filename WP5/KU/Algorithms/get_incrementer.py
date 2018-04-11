# get_incrementer.py


def get_incrementer(num, num_digits):
    if num >= 10**num_digits:
        print('NUMBER IS LARGER THAN THE MAX POSSIBLE BASED ON num_digits')
        return -1
    else:
        if num > 99999:
            number_length = 6
        elif num > 9999:
            number_length = 5
        elif num > 999:
            number_length = 4
        elif num > 99:
            number_length = 3
        elif num > 9:
            number_length = 2
        else:
            number_length = 1

    char = ''
    for i in range(num_digits - number_length):
        char = char + '0'
    return char + str(num)