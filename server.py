#
# Серверное приложение для соединений
#


import asyncio
from asyncio import transports

logs =[""]*10                                       #cписок для последних 10-ти сообщений
class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if self.login in self.server.logins:                        #проверяем, занят ли логин
                    self.transport.write(f"логин {self.login} занят, придумайте новый\n".encode())   # логин уже занят
                    print(f"Пытались ввести занятый логин: {self.login}")
                    self.transport.close()

                else:
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.server.logins.append(self.login)                   #добавляем новый логин в список занятых
                    self.send_history()                                     #отправляем лог сообщений

            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}"
        logs.insert(0, message)
        if len(logs) > 10:                                       # очистка старых сообщений. избавление от переполнения
            logs.pop(10)                                         # списка последних сообщений


        for client in self.server.clients:
            if client.login != self.login:                       # отправка сообщений всем, кроме себя
                client.transport.write(message.encode())

    def send_history(self):                                      # метод для отправки последних 10-ти сообщений
#        history = '\n'.join((logs))
        self.transport.write("Последние 10 сообщений чата: \n\n".encode())
        print(logs)                                              # Для проверки, очищается ли лог сообщений от старых
        if logs [0] == "":                                       # не показывать пустой лог сообщений первому юзеру
            self.transport.write("Пусто, вы первый пользователь чата: \n\n".encode())
        else:

            for i in reversed(range(10)):                               # отправляем последние 10 сообщений в
                self.transport.write((logs[i]).encode())                # в хронологическом порядке
                self.transport.write("\n".encode())

class Server:
    clients: list

    def __init__(self):
        self.clients = []
        self.logins =[]                                                 # список используемых логинов

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
