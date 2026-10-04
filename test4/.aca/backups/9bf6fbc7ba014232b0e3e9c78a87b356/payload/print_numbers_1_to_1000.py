import datetime

# Create or open the text file to log the numbers and timestamps
with open('numbers_log.txt', 'a') as log_file:
    for i in range(1, 1001):
        log_file.write('شماره: {} - زمان: {}
'.format(i, datetime.datetime.now()))
        print(i)