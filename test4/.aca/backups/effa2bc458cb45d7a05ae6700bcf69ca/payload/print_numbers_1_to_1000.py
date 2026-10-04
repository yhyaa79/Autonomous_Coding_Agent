def print_numbers_1_to_1000():
    import datetime
    # Create or open the text file to log the numbers and timestamps
    with open('numbers_log.txt', 'a') as log_file:
        for i in range(1, 1001):
            print(i)
            log_file.write('Number: {}, Time: {}
'.format(i, datetime.datetime.now()))

print_numbers_1_to_1000()