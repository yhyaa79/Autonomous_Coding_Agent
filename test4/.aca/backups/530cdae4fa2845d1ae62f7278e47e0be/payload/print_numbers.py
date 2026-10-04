import datetime

# Create or open the text file to log the numbers and timestamps
with open('numbers_log.txt', 'a') as log_file:
    log_file.write('سلاممم\n')
    for i in range(1, 11):
        print(i)
        # Get the current time
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Write the number and current time to the log file
        log_file.write(f'Number: {i}, Time: {current_time}\n')
