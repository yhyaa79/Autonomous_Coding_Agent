def log_time():
    with open('time.txt', 'a') as f:
        f.write(f'{__import__("datetime").datetime.now()}\n')

if __name__ == '__main__':
    log_time()