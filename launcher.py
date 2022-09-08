import subprocess


process = []

while True:
    action = input('Select action: q - exit , s - launch server and clients, x - close all windows:')
    if action == 'q':
        break
    elif action == 's':
        clients_count = int(input('Enter the ammount of clients: '))
        # Launcing server!
        process.append(subprocess.Popen('python server_class.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
        # Launching clients:
        for i in range(clients_count):
            process.append(subprocess.Popen(f'python client_class.py -n test{i + 1}', creationflags=subprocess.CREATE_NEW_CONSOLE))
    elif action == 'x':
        while process:
            process.pop().kill()
