import random
import socket as so
import ssl
import threading as th
import time
from db import user_exists, add_user, check_password, build_db, add_score_to_user
import hashlib


class Server:
    clients = []

    def __init__(self, clients_list):
        self.clients = clients_list


NUMBER_OF_PLAYERS = 2
certfile = r"localhost.pem"
cafile = r"cacert.pem"
purpose = ssl.Purpose.CLIENT_AUTH
context = ssl.create_default_context(purpose, cafile=cafile)
context.load_cert_chain(certfile)
all_set = []
categories_milon = {
    0: "country",
    1: "capital",
    2: "boy",
    3: "movie",
    4: "animal",
    5: "fruit/vegetable",
    6: "household item",
}
client_num = 0
round_num = 1
client_done = False
finished_game_counter = 0
broadcast_end = False
username = ""
player_lists = []
current_start_letter = 'A'
start_game = False
build_db()
round_letters = ['', '', '']
game_data_updated = False
clientsReady = []
clients = []
buf = 1024
file = open("countries.txt")
countriesList = file.read().split("\n")
file2 = open("cities.txt")
citiesList = file2.read().split("\n")
file3 = open("boy.txt")
boyList = file3.read().split("\n")
movieList = []
file4 = open("movies.txt")
long_movie_List = file4.read().split("\n")
for z in long_movie_List:
    position = z.find("(")
    z = z[:(position - 1)]
    movieList.append(z)
file5 = open("animals.txt", encoding="utf8")
animalsList = file5.read().split("\n")
file6 = open("fruitsAndVeggies.txt")
fruitsAndVeggiesList = file6.read().split("\n")
file7 = open("householdItems.txt")
householdItemsList = file7.read().split("\n")


def md5_encrypt(message):
    md5_hash = hashlib.md5()
    md5_hash.update(message.encode('utf-8'))
    encrypted = md5_hash.hexdigest()
    return encrypted


def create_msg(data):
    data_len = len(data)
    data_len_len = len(str(data_len))
    data_len = str(data_len)
    for i in range(4 - data_len_len):
        data_len = "0" + data_len
    return data_len + data


def handle_msg(client_socket):
    data_len_received = client_socket.recv(4).decode()
    data_received = client_socket.recv(int(data_len_received)).decode()
    return data_received


def log_in(data, client_socket):
    global clientsReady
    global username
    global clients
    if "username:" in data:
        while user_exists(data.split(":")[1]) is True:
            client_socket.send("Username is already taken".encode())
            data = client_socket.recv(1024).decode()
        username = data.split(":")[1]
        client_socket.send("Accepted1".encode())
        data = client_socket.recv(1024).decode()
        add_user(data.split()[0], data.split()[1], data.split()[2], md5_encrypt(data.split()[3]))
        if len(clients) == 3:
            client_socket.send("User added but game is currently full".encode())
        while len(clients) == 3:
            pass
        clients.append([client_socket, data.split()[0]])
        clientsReady.append([clients[-1][1], False])
        print(clients)
        client_socket.send("Accepted2".encode())
    if "usernameold:" in data:
        while user_exists(data.split(":")[1]) is not True:
            client_socket.send("user not found.".encode())
            data = client_socket.recv(1024).decode()
        username = data.split(":")[1]
        if len(clients) == 3:
            client_socket.send("Game is currently full".encode())
        while len(clients) == 3:
            pass
        client_socket.send("Accepted3".encode())
        data = client_socket.recv(1024).decode()
        while check_password(username, md5_encrypt(data.split(":")[1])) is not True:
            client_socket.send("password is wrong: ".encode())
            data = client_socket.recv(1024).decode()
        client_socket.send("Accepted4".encode())
        clients.append((client_socket, username))
        clientsReady.append([clients[-1][1], False])
    return username


def broadcast(string_to_broadcast, clientList):
    for i in clientList:
        i[0].send(string_to_broadcast.encode())


def check_if_ready(clientList):
    if len(clientList) < NUMBER_OF_PLAYERS:
        return False
    for i in clientList:
        if i[1] is False:
            return False
    return True


def check_if_category(word_list, category_list, category_array, word_array, num):
    global categories_milon
    for i in category_list:
        if i in word_list:
            category_array[num] = 1
            word_array[num] = i
            return "you said a ?" + categories_milon[num] + "? :" + i + ": "
    return ""


def analyze_word(word_list, category_array, word_array):
    msgToSend = check_if_category(word_list, countriesList, category_array, word_array, 0)
    msgToSend += check_if_category(word_list, citiesList, category_array, word_array, 1)
    msgToSend += check_if_category(word_list, boyList, category_array, word_array, 2)
    msgToSend += check_if_category(word_list, movieList, category_array, word_array, 3)
    msgToSend += check_if_category(word_list, animalsList, category_array, word_array, 4)
    msgToSend += check_if_category(word_list, fruitsAndVeggiesList, category_array, word_array, 5)
    house = check_if_category(word_list, householdItemsList, category_array, word_array, 6)
    if house == "":
        msgToSend += check_if_category(word_list, fruitsAndVeggiesList, category_array, word_array, 6)
    else:
        msgToSend += house
    return msgToSend


def add_lists(list1, list2):
    result = []
    for i in range(len(list1)):
        result.append(list1[i] + list2[i])
    return result


def check_for_special_word(single_category_list):
    special = True
    counter = 0
    for i in range(3):
        if single_category_list[i] != "":
            for x in range(3):
                if x != i:
                    if single_category_list[x] != "":
                        special = False
            if special is True:
                return counter
        counter += 1
        special = True
    return -1


def calculate_points_for_a_single_category(single_category_list):
    points = [0] * len(single_category_list)  # initialize points list to 0
    special_word_index = check_for_special_word(single_category_list)
    counter = 0
    five_pts = False
    if single_category_list[0] == "" and single_category_list[1] == "" and single_category_list[2] == "":
        return points
    if special_word_index != -1:
        points[special_word_index] = 15
        return points
    else:
        for i in single_category_list:
            if i != "":
                for x in single_category_list:
                    if x == i:
                        points[counter] = 5
                        five_pts = True
                if five_pts is False:
                    points[counter] = 10
            counter += 1
        return points


def calculate_and_add_points(player_list):
    all_clients_words_list = [player_list[0][0], player_list[1][0], player_list[2][0]]
    points = [0] * len(player_list)  # initialize points list to 0
    for i in range(7):
        results = calculate_points_for_a_single_category(
            [all_clients_words_list[0][i], all_clients_words_list[1][i], all_clients_words_list[2][i]])
        points = add_lists(results, points)
    for j in range(3):
        add_score_to_user(player_list[j][1], points[j])


def calculate_points_for_debug(player_list):
    for x in range(len(player_list)):
        add_score_to_user(player_list[x][1], 15)


def handle_client(client_socket):
    global current_start_letter, client_num
    global clients
    global start_game
    global clientsReady
    global game_data_updated
    global finished_game_counter
    global broadcast_end
    global client_done
    categories_arr = [0, 0, 0, 0, 0, 0, 0]
    word_arr = ["", "", "", "", "", "", ""]
    print("222", th.get_native_id())
    """Handles a single client connection."""
    data = client_socket.recv(1024).decode()
    print(data)
    client_name = log_in(data, client_socket)
    while "q:" not in data:
        # ready message
        data = client_socket.recv(1024).decode()
        print("before before" + data)
        if "ready:" in data:
            for c in clientsReady:
                if c[0] == client_name:
                    c[1] = True
        for i in range(3):
            client_done = False
            finished_game_counter = 0
            broadcast_end = False
            while start_game is False:
                pass
            game_data_updated = False
            for c in clientsReady:
                if c[0] == client_name:
                    c[1] = False
            data = client_socket.recv(1024).decode()
            print("receive23d" + data)
            start_time = time.time()
            while client_done is False:
                try:
                    if data == " ":
                        client_socket.send("you said a phrase with no category".encode())
                    else:
                        myText = data.lower()
                        myText = myText.title()
                        myTextListAllWords = myText.split(" ")
                        myTextListAllWords.append(myText)
                        myTextList = [word for word in myTextListAllWords if word.startswith(current_start_letter)]
                        plural_list = []
                        for q in myTextList:
                            plural_list.append(q + "s")
                        myTextList = myTextList + plural_list
                        msgToSend = analyze_word(myTextList, categories_arr, word_arr)
                        print("Did you say ", data)
                        print("time: " + str(time.time() - start_time))
                        if 0 not in categories_arr and broadcast_end is False:
                            broadcast("A player finished@ ending game" + msgToSend, clients)
                            broadcast_end = True
                            client_done = True
                        elif (time.time() - start_time) > 5 and broadcast_end is False:
                            print(client_name + ". end")
                            broadcast("Time is up, turn finished@ ending turn" + msgToSend, clients)
                            broadcast_end = True
                            client_done = True
                        else:
                            if msgToSend == "":
                                client_socket.send(" ".encode())
                            client_socket.send(msgToSend.encode())
                    data = client_socket.recv(1024).decode()
                    print(client_name + "received1 " + data)

                except:
                    pass

            player_lists.append([word_arr, client_name])
            print(client_name + "added list")
            finished_game_counter += 1
            print(client_name + "finisghed game counter updated")
            while game_data_updated is False:
                pass
            print(client_name + "points updated")
            categories_arr = [0, 0, 0, 0, 0, 0, 0]
            word_arr = ["", "", "", "", "", "", ""]
            print(client_name + "lists restarted")
            broadcast_end = False
            print(client_name + "data before done" + data)
            if "done:" in data:
                print(client_name + "done in data")
            while "done:" not in data:
                print(client_name + "before" + data)
                data = client_socket.recv(1024).decode()
                print(client_name + "after" + data)
            for c in clientsReady:
                if c[0] == client_name:
                    c[1] = True


def main():
    global current_start_letter, finished_game_counter
    global start_game
    global game_data_updated
    global round_num
    global client_num
    global round_letters

    client_num = 0
    print("Start Server")
    server_socket = so.socket()
    server_socket.bind(('0.0.0.0', 8820))
    server_socket.listen(1)
    while client_num < NUMBER_OF_PLAYERS:
        (client_socket, client_address) = server_socket.accept()
        client_socket = context.wrap_socket(client_socket, server_side=True)
        client_num += 1
        try:
            e = th.Thread(target=handle_client, args=(client_socket,))
            e.start()
        except:
            pass
    while client_num == NUMBER_OF_PLAYERS:
        while check_if_ready(clientsReady) is False:
            pass
        for i in range(3):

            start_game = False
            print("got ready" + str(i))
            while check_if_ready(clientsReady) is False:
                pass
            current_start_letter = random.choice("ABCDGHIJKLMNOPRST")
            while current_start_letter in round_letters:
                current_start_letter = random.choice("ABCDGHIJKLMNOPRST")
            round_letters[i] = current_start_letter
            print(current_start_letter + " letter")
            broadcast("The letter is:" + current_start_letter, clients)
            start_game = True
            while finished_game_counter < NUMBER_OF_PLAYERS:
                pass
            print("got out of loop")
            finished_game_counter = 0
            calculate_points_for_debug(player_lists)
            print("pts updated from main")
            game_data_updated = True
            start_game = False


main()
