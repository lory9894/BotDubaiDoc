import os
import re
import threading
import queue
import traceback

from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import telebot
from telebot.apihelper import ApiTelegramException
from threading import Thread
from time import sleep
import schedule
from telegram.constants import ParseMode
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import time
import json

# ------------------------------------------------------------------------------

TOKEN = ''
MAIL = ''
PSW = ''
URL_DOC = 'https://www.facebook.com/selfservicedoctorino'
URL_DUBAI = 'https://www.facebook.com/people/Dubai-coffee-lounge/100087591040668/'
LOGURL = 'https://www.facebook.com/login/'

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
daily_dubai = True
daily_doc = True
new_menu_dubai = None
new_menu_doc = None
global driver
driver = None


# sslify = SSLify(server)

# ------------------------------------------------------------------------------

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# ------------------------------------------------------------------------------

def write_id(id,dubai,doc):

    dati = {"id": id,"dubai": dubai,"doc": doc}
    try:
        with open("database.json", "r") as file:
            dati_esistenti = json.load(file)
    except FileNotFoundError:
        dati_esistenti = []

    dati_esistenti.append(dati)

    with open("database.json", "w") as file:
        json.dump(dati_esistenti, file)

def write_name(nick, name, surname):
    with open("nomi.json", "r+") as f:
        # Leggi il contenuto del file
        content = f.read()
        # Se il file è vuoto, scrivi direttamente il nuovo record
        if not content:
            user_data = {"nickname": nick, "first_name": name, "last_name": surname}
            json.dump(user_data, f)
            f.write('\n')
        else:
            # Altrimenti, cerca se esiste già un record con lo stesso nickname
            f.seek(0)  # torna all'inizio del file
            found = False
            for line in f:
                record = json.loads(line)
                if record["nickname"] == nick:
                    found = True
                    break
            # Se non esiste già un record con lo stesso nickname, aggiungi il nuovo record
            if not found:
                f.seek(0, 2)  # vai alla fine del file
                user_data = {"nickname": nick, "first_name": name, "last_name": surname}
                json.dump(user_data, f)
                f.write('\n')

def add_name(nickname, first_name, last_name):
    # Leggi il contenuto del file JSON
    with open("nomi.json", 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            # Se il file è vuoto o non ha un formato JSON valido, inizializza data come una lista vuota
            data = []

    # Verifica se l'elemento esiste già nel file
    elementi_esistenti = [elemento for elemento in data if elemento.get('nickname') == nickname]
    if elementi_esistenti:
        return

    # Crea il nuovo elemento da aggiungere
    nuovo_elemento = {
        'nickname': nickname,
        'first_name': first_name,
        'last_name': last_name
    }

    # Aggiungi il nuovo elemento alla lista dei dati
    data.append(nuovo_elemento)

    # Scrivi i dati aggiornati nel file JSON
    with open("nomi.json", 'w') as file:
        json.dump(data, file, indent=4)

def write_txt(file, text):
    f = open(file, 'w', encoding='utf8')
    f.write(text)
    f.close()

def read_ids(m):
    ids = []
    try:
        with open('database.json', 'r', encoding='utf8') as file:
            contenuto = file.read()
        file.close()
        dati = json.loads(contenuto)

        if m == "all":
            ids = [str(d['id']) for d in dati]


        elif m == "dubai" or m == "doc":
            for item in dati:
                if str(item[m]) == str(True):
                    ids.append(str(item['id']))
    except:
        print("No dati")

    return ids

def delete_element(id_to_delete):
    with open('database.json', 'r', encoding='utf8') as file:
        dati = json.load(file)

    dati = [dato for dato in dati if str(dato['id']) != id_to_delete]

    with open('database.json', 'w', encoding='utf8') as file:
        json.dump(dati, file)

def send_menu(menu,m):
    sleep(5)
    database = read_ids(m)
    for id in database:
        if id != "":
            try:
                # bot.send_message(int(id), menu)
                message_queue.put((int(id), menu))
            except:
                print("Errore")

def conta_database(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        record_count = len(data)
        return record_count

def leggi_database(file_path):
    with open(file_path) as file:
        data = json.load(file)

    elementi = []
    for elemento in data:
        campo = elemento[list(elemento.keys())[0]]
        elementi.append(campo)

    return elementi

def leggi_nomi(file_path):
    with open(file_path) as file:
        data = json.load(file)

    elementi = []
    for elemento in data:
        campi = [campo for campo in elemento.values() if campo is not None]
        elementi.append(" - ".join(campi))

    risultato = "\n".join(elementi)
    return risultato

def update_json(id, string, val):
    # Apri il file JSON in modalità di lettura e scrittura
    with open("database.json", "r+") as json_file:
        data = json.load(json_file)

        # Cerca l'elemento con l'id corrispondente
        for item in data:
            if item["id"] == id:
                # Modifica l'elemento con il valore specificato
                item[string] = val
        # Torna all'inizio del file e sovrascrivi i dati
        json_file.seek(0)
        json.dump(data, json_file)

        # Riduci la dimensione del file, se necessario, per eliminare eventuali dati residui
        json_file.truncate()

def grid():

    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2)
    button1 = telebot.types.KeyboardButton('Start')
    button2 = telebot.types.KeyboardButton('Stop')
    button3 = telebot.types.KeyboardButton('Start Dubai')
    button4 = telebot.types.KeyboardButton('Stop Dubai')
    button5 = telebot.types.KeyboardButton('Start Doc')
    button6 = telebot.types.KeyboardButton('Stop Doc')
    button7 = telebot.types.KeyboardButton('HELP')
    button8 = telebot.types.KeyboardButton('Autori')
    keyboard.add(button1, button2, button3, button4, button5, button6, button7, button8)

    return keyboard

# ------------------------------------------------------------------------------

def process_message_queue():

    keyboard = grid()

    while True:
        try:
            user_id, text = message_queue.get()
            try:
                bot.send_message(user_id, text, reply_markup=keyboard)
            except ApiTelegramException as e:
                if e.result_json['error_code'] == 403:
                    # Bot blocked by the user
                    delete_element(str(id))
                else:
                    try:
                        bot.send_message(168648726, e.result_json)
                    except:
                        print("Errore")
            except:
                print("Errore")

            sleep(0.5)
            message_queue.task_done()
        except Exception as e:
            error_message = f"Queue errore: {traceback.format_exc()}"
            bot.send_message(168648726, error_message)
            try:
                message_queue.task_done()
            except:
                print("Errore queue done")

    bot.send_message(168648726, "Queue chiusa")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("START")
    user_id = message.chat.id
    user_nickname = message.chat.username
    user_first_name = message.chat.first_name
    user_last_name = message.chat.last_name

    try:
        # write_name(user_nickname,user_first_name,user_last_name)
        add_name(user_nickname, user_first_name, user_last_name)
    except:
        print("Errore scrittura nome")

    if str(user_id) in read_ids("all"):
        message_queue.put((user_id, 'Sei già presente nel database! Appena disponibile ti sarà inviato il menu del giorno.'))
        sleep(1)
    else:
        write_id(user_id,False,False)
        message_queue.put((user_id,'Benvenuto! Sei stato inserito nel database! Scegli quali menù vuoi ricevere giornalmente tramite i comandi.'))
        sleep(1)
        helper(message)

@bot.message_handler(commands=['annuncioall'])
def annuncio_all(message):
    try:
        user_id = message.chat.id
        if (str(user_id) == "220450935" or str(user_id) == "168648726"):
            send_menu(message.text.replace('/annuncioall', '', 1).strip(), "all")
            sleep(1)
    except:
        print("Errore annuncio all")

@bot.message_handler(commands=['annunciodubai'])
def annuncio_dubai(message):
    try:
        user_id = message.chat.id
        if (str(user_id) == "220450935" or str(user_id) == "168648726"):
            send_menu(message.text.replace('/annunciodubai', '', 1).strip(), "dubai")
            sleep(1)
    except:
        print("Errore annuncio dubai")

@bot.message_handler(commands=['annunciodoc'])
def annuncio_doc(message):
    try:
        user_id = message.chat.id
        if (str(user_id) == "220450935" or str(user_id) == "168648726"):
            send_menu(message.text.replace('/annunciodoc', '', 1).strip(), "doc")
            sleep(1)
    except:
        print("Errore annuncio doc")

@bot.message_handler(commands=['startdubai'])
def insert_dubai(message):
    print("START DUBAI")
    user_id = message.chat.id

    if str(user_id) in read_ids("all"):
        if str(user_id) in read_ids("dubai"):
            message_queue.put((user_id, 'Sei già presente nel database! Appena disponibile ti sarà inviato il menu del giorno.'))
            sleep(1)
        else:
            update_json(user_id, "dubai", True)
            message_queue.put((user_id, 'Benvenuto! Da adesso ti arriverà il menù del Dubai giornalmente.'))
            sleep(1)
            global new_menu_dubai, daily_dubai

            if not daily_dubai:
                message_queue.put((user_id, new_menu_dubai))
                sleep(1)
    else:
        message_queue.put((user_id, "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)

@bot.message_handler(commands=['stopdubai'])
def delete_dubai(message):
    print("STOP DUBAI")
    user_id = message.chat.id

    if str(user_id) in read_ids("all"):
        if str(user_id) in read_ids("dubai"):
            update_json(user_id, "dubai", False)
            message_queue.put((user_id, 'Da adesso non ti arriveranno più i menù giornalieri del Dubai. Per riattivarli usa il comando /startdubai.'))
            sleep(1)
        else:
            message_queue.put((user_id, 'Sei già disiscritto dal Dubai. Usa il comando /startdubai per essere aggiunto.'))
            sleep(1)
    else:
        message_queue.put((user_id, "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)

@bot.message_handler(commands=['startdoc'])
def insert_doc(message):
    print("START DOC")
    user_id = message.chat.id

    if str(user_id) in read_ids("all"):
        if str(user_id) in read_ids("doc"):
            message_queue.put((user_id, 'Sei già presente nel database! Appena disponibile ti sarà inviato il menu del giorno.'))
            sleep(1)
        else:
            update_json(user_id, "doc", True)
            message_queue.put((user_id, 'Benvenuto! Da adesso ti arriverà il menù del Doc giornalmente.'))
            sleep(1)
            global new_menu_doc, daily_doc

            if not daily_doc:
                message_queue.put((user_id, new_menu_doc))
                sleep(1)
    else:
        message_queue.put((user_id, "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)

@bot.message_handler(commands=['stopdoc'])
def delete_doc(message):
    print("STOP DOC")
    user_id = message.chat.id

    if str(user_id) in read_ids("all"):
        if str(user_id) in read_ids("doc"):
            update_json(user_id, "doc", False)
            message_queue.put((user_id, 'Da adesso non ti arriveranno più i menù giornalieri del Doc. Per riattivarli usa il comando /startdoc.'))
            sleep(1)
        else:
            message_queue.put((user_id, 'Sei già disiscritto dal Doc. Usa il comando /startdoc per essere aggiunto.'))
            sleep(1)
    else:
        message_queue.put((user_id, "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)

@bot.message_handler(commands=['autori'])
def send_autori(message):
    print("AUTORI")
    user_id = message.chat.id
    if str(user_id) in read_ids("all"):
        bot.send_message(user_id,
                         text='Gli autori di questo bot sono:\n\nTELEGRAM:\n @antonio_adascaliti \n @lodipi \n\nINSTAGRAM:\n <a href="https://www.instagram.com/antonio_adascaliti/">antonio_adascaliti</a>  \n <a href="https://www.instagram.com/lorenzo.dipi/">lorenzo.dipi</a>',
                         parse_mode=ParseMode.HTML)
        # message_queue.put((user_id, ('Gli autori di questo bot sono:\n\nTELEGRAM:\n @antonio_adascaliti \n @lodipi \n\nINSTAGRAM:\n <a href="https://www.instagram.com/antonio_adascaliti/">antonio_adascaliti</a>  \n <a href="https://www.instagram.com/lorenzo.dipi/">lorenzo.dipi</a>', ParseMode.HTML)))
        sleep(1)
    else:
        # bot.send_message(user_id, text = "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi")
        message_queue.put((user_id, "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)

@bot.message_handler(commands=['stop'])
def remove_user(message):
    print("STOP")
    user_id = message.chat.id
    if str(user_id) in read_ids("all"):
        delete_element(str(user_id))
        # bot.send_message(user_id, 'Ci dispiace che tu ci lasci così presto! Usa il comando /start per tornare!')
        message_queue.put((user_id, 'Ci dispiace che tu ci lasci così presto! Usa il comando /start per tornare!'))
        sleep(1)
    else:
        # bot.send_message(user_id, text = "Il bot è già disattivato. \nUtilizza il comando /start per avviarlo!")
        message_queue.put((user_id, "Il bot è già disattivato. \nUtilizza il comando /start per avviarlo!"))
        sleep(1)

@bot.message_handler(commands=['help'])
def helper(message):
    print("HELP")
    user_id = message.chat.id
    if str(user_id) in read_ids("all"):
        # bot.send_message(user_id, 'In questo bot potrai utilizzare i seguenti comandi:\n - /start per inserire il tuo id nel nostro database (ci serve solo per inviarti il menu!)\n - /stop per rimuovere il tuo id dal database quando lo vorrai\n - /help per farti inviare questo messaggio\n - /autori per sapere chi ha fatto questo bot')
        message_queue.put((user_id,'In questo bot potrai utilizzare i seguenti comandi:\n - /start per inserire il tuo id nel nostro database ed iscriverti al bot!\n - /stop per rimuovere il tuo id dal database quando lo vorrai\n - /startdubai per ricevere i menù del dubai giornalmente\n - /startdoc per ricevere i menù del doc giornalmente\n - /stopdubai per non ricevere più i menù del dubai giornalmente\n - /stopdoc per non ricevere più i menù del doc giornalmente\n - /help per farti inviare questo messaggio\n - /autori per sapere chi ha fatto questo bot'))
        sleep(1)
    else:
        # bot.send_message(user_id, text = "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi")
        message_queue.put((user_id, "Sembra che tu sia nuovo! Usa il comando /start per usufruire di tutti i comandi"))
        sleep(1)

@bot.message_handler(commands=['stats'])
def stats(message):
    try:
        user_id = message.chat.id
        print("STATS")
        if (str(user_id) == "220450935" or str(user_id) == "168648726"):
            num_db = conta_database("database.json")
            num_nomi = conta_database("nomi.json")
            # bot.send_message(user_id, str(num_db))
            # sleep(1)
            # bot.send_message(user_id, str(num_nomi))

            stringa = "database: '{}' \nnomi: '{}'".format(num_db, num_nomi)
            # bot.send_message(user_id, stringa)
            message_queue.put((user_id, stringa))
            sleep(1)
    except:
        print("Errore conteggio")

@bot.message_handler(commands=['nomi'])
def names(message):
    try:
        user_id = message.chat.id
        print("NOMI")
        if (str(user_id) == "220450935" or str(user_id) == "168648726"):
            nomi = leggi_nomi("nomi.json")
            # bot.send_message(user_id, str(nomi))
            message_queue.put((user_id, str(nomi)))
            sleep(1)
    except:
        print("Errore lettura nomi")

@bot.message_handler(commands=['database'])
def databaseID(message):
    try:
        user_id = message.chat.id
        print("DATABASE")
        if (str(user_id) == "220450935" or str(user_id) == "168648726"):
            db = leggi_database("database.json")
            # bot.send_message(user_id, str(db))
            message_queue.put((user_id, str(db)))
            sleep(1)
    except:
        print("Errore lettura database")
    # ------------------------------------------------------------------------------

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    if message.text == "Start":
        send_welcome(message)
    elif message.text == "Stop":
        remove_user(message)
    elif message.text == "Start Dubai":
        insert_dubai(message)
    elif message.text == "Stop Dubai":
        delete_dubai(message)
    elif message.text == "Start Doc":
        insert_doc(message)
    elif message.text == "Stop Doc":
        delete_doc(message)
    elif message.text == "HELP":
        helper(message)
    elif message.text == "Autori":
        send_autori(message)
    else:
        bot.send_message(message.chat.id, "Questo comando non esiste. Usa la tastiera personalizzata per aiutarti!")

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

def format_dubai(menu):
    menu = menu.replace("Oggi vi proponiamo:", "Buongiorno, oggi vi proponiamo: 🍽️")
    menu = menu.replace("PRIMI", "\nPRIMI 🍝")
    menu = menu.replace("SECONDI", "\nSECONDI 🍖")
    menu = menu.replace("CONTORNI", "\nCONTORNI 🍟🥦")
    menu = menu.replace("FRUTTA E YOGURT", "\nFRUTTA E YOGURT 🍎🍍🥛")
    menu = menu.replace("DOLCI", "\nDOLCI 🍰")



    menu = menu.replace(" -", "-")
    menu = menu.replace("\n-", "-")
    menu = menu.replace("-", "\n - ")

    menu = menu + "\n\nVI ASPETTIAMO!"

    menu = "\tMENÙ DUBAI\n" + menu
    return menu

def lowercase_menu(menu):
    # Dividi il testo in linee
    lines = menu.split('\n')

    # Elabora ogni linea
    for i, line in enumerate(lines):
        # Tratta titoli, introduzione e insalate
        if line.startswith("PRIMI") or line.startswith("SECONDI") or line.startswith("CONTORNI") or line.startswith(
                "PIATTI FREDDI") or line.startswith("INSALATE") or line.startswith("DOLCI") or line.startswith("FRUTTA") or line.startswith(" - INSALATA") or line.startswith("Buongiorno"):
            # Mantieni maiuscole e minuscole originali
            lines[i] = line
        else:
            # Trasforma il resto in minuscolo
            lines[i] = line.lower()

    # Ricompatta il testo
    formatted_menu = '\n'.join(lines)

    return formatted_menu

def format_doc(menu):
    date_pattern = r'\d{2}/\d{2}/\d{4}'

    # Sostituisci tutte le occorrenze del pattern con un testo specifico (ad esempio, "DATA_RIMOSSA")
    menu = re.sub(date_pattern, "", menu)
    menu = menu.replace("\nPER PRENOTAZIONI CHIAMARE IL NUMERO.3385305973. Lucia \n","\n")
    menu = menu.replace("\n", "\n-")
    menu = menu.replace("\n-\n", "\n")

    menu = menu.replace("MENU DEL GIORNO", "Buongiorno, oggi vi proponiamo: 🍽")
    menu = menu.replace("-PRIMI", "\nPRIMI 🍝")
    menu = menu.replace("-SECONDO", "\nSECONDI 🍖")
    menu = menu.replace("-CONTORNI", "\nCONTORNI 🍟🥦")
    menu = menu.replace("-INSALATE:", "\nINSALATE 🥗")
    menu = menu.replace("-DESSERT:", "\nDOLCI 🍰")
    menu = menu.replace("-FRUTTA:", "\nFRUTTA 🍎🍍🥛")
    menu = menu.replace("-PIATTI FREDDI:", "\nPIATTI FREDDI 🍱 ")


    # Aggiungi uno spazio dopo i trattini
    menu = menu.replace(" -", "-")
    #menu = menu.replace("\n-", "\n-")
    menu = menu.replace("-", " - ")
    
    menu = lowercase_menu(menu)
    menu = menu + "\n\nVI ASPETTIAMO!"
    menu = menu.replace("inasalata", "insalata")
    menu = "\tMENÙ DOC\n"+menu

    return menu

def get_menu(link):
    global div_block
    global driver
    while True:
        try:
            print("prima di chrome options")
            while driver is not None:
                sleep(10)
            chrome_options = webdriver.ChromeOptions()
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.delete_all_cookies()

            print("DENTRO AL BROWSER")

            driver.get(LOGURL)

            try:
                driver.find_element(by=By.XPATH,
                                    value='//button[@data-testid="cookie-policy-manage-dialog-accept-button"]').click()
            except:
                print("niente cookies")

            sleep(2)
            driver.find_element(by=By.XPATH, value='//input[@name="email"]').send_keys(MAIL)
            driver.find_element(by=By.XPATH, value='//input[@name="pass"]').send_keys(PSW)
            driver.find_element(by=By.XPATH, value='//button[@name="login"]').click()

            sleep(2)

            driver.get(link)

            sleep(5)

            while (driver.title == "Facebook"):
                sleep(2)

            print("Page title was '{}'".format(driver.title))

            sleep(2)
            try:
                driver.find_element(by=By.XPATH, value='//div[@aria-label="Consenti solo i cookie essenziali"]').click()
            except:
                print("Cookies non richiesti")

            sleep(2)
            try:
                driver.find_element(by=By.XPATH, value="//div[@class='x92rtbv x10l6tqk x1tk7jg1 x1vjfegm']").click()
                sleep(2)
            except:
                print("Niente da chiudere")

            sleep(2)

            div_block = None

            while div_block is None:
                try:
                    div_block = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-pagelet="ProfileTimeline"]')))
                except:
                    div_block = None
                    sleep(2)

            i = 1
            bool = True
            element = None

            while bool:
                try:
                    if link==URL_DUBAI:
                        element = WebDriverWait(div_block, 10).until(EC.visibility_of_element_located((By.XPATH, './/div[contains(text(), "Oggi vi proponiamo")]')))
                    elif link == URL_DOC:
                        element = WebDriverWait(div_block, 10).until(EC.visibility_of_element_located((By.XPATH, './/div[contains(text(), "MENU DEL GIORNO")]')))
                    element.find_element(by=By.XPATH, value="//div[contains(text(), 'Altro...')]").click()
                    sleep(1)
                    element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[class*="x1iorvi4 x1pi30zi x1swvt13 xjkvuk6"][id]')))
                    bool = False
                except:
                    print("Except Menu")
                    driver.execute_script("window.scrollBy(0, 10);")
                    sleep(1)

            print(element.text)
            if link == URL_DOC:
                return format_doc(element.text)
            elif link == URL_DUBAI:
                return format_dubai(element.text)

        except NoSuchElementException:
            print("Elemento non trovato sulla pagina o browser già attivo.")

def write_new_menu(menu,txt):
    if txt == "menu_dubai.txt":
        global daily_dubai
        file = open(txt, 'w', encoding='utf-8')
        file.write(menu)
        file.close
        daily_dubai = False
    elif txt == "menu_doc.txt":
        global daily_doc
        file = open(txt, 'w', encoding='utf-8')
        file.write(menu)
        file.close
        daily_doc = False

def update_dubai():
    global new_menu_dubai, daily_dubai, driver
    check = True
    n = 0
    if daily_dubai:
        while check and n < 20:
            n = n + 1
            try:
                file = open("menu_dubai.txt", "r", encoding="utf-8")
            except:
                print("ERRORE APERTURA FILE MENU")
                file = None
            old_menu_dubai = file.read()
            file.close()

            new_menu_dubai = get_menu(URL_DUBAI)
            driver.close()
            driver.quit()

            driver = None


            if new_menu_dubai != old_menu_dubai:
                write_new_menu(new_menu_dubai,"menu_dubai.txt")
                send_menu(new_menu_dubai,"dubai")
                check = False
            else:
                # driver.close()
                print("attendo 10 minuti")
                sleep(600)
    else:
        file = open('menu_dubai.txt', 'r', encoding="utf-8")
        m = file.read()
        file.close()
        send_menu(m,"dubai")

def update_doc():
    global new_menu_doc, daily_doc, driver
    check = True
    n = 0
    if daily_doc:
        while check and n < 20:
            n = n + 1
            try:
                file = open("menu_doc.txt", "r", encoding="utf-8")
            except:
                print("ERRORE APERTURA FILE MENU")
                file = None
            old_menu_doc = file.read()
            file.close()

            new_menu_doc = get_menu(URL_DOC)
            driver.close()
            driver.quit()

            driver = None

            if new_menu_doc != old_menu_doc:
                write_new_menu(new_menu_doc,"menu_doc.txt")
                send_menu(new_menu_doc,"doc")
                check = False
            else:
                print("attendo 10 minuti")
                sleep(600)
    else:
        file = open('menu_doc.txt', 'r', encoding="utf-8")
        m = file.read()
        file.close()
        send_menu(m,"doc")

def update_wrapper():
    try:
        t_doc = threading.Thread(target=update_doc)
        t_doc.daemon = True
        t_doc.start()

        t_dubai = threading.Thread(target=update_dubai)
        t_dubai.daemon = True
        t_dubai.start()

    except Exception as e:
        # Cattura l'eccezione e invia un messaggio di errore
        error_message = f"Si è verificato un errore: {str(e)}"
        print(error_message)

def daily_trigger():
    global daily_dubai,daily_doc
    daily_dubai = True
    daily_doc = True

def connection_server():
    while True:
        try:
            while True:
                server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5599)))
                sleep(300)
        except Exception as e:
            print("Connessione persa. Ripristino in corso...")
            time.sleep(5)  # Attendere per 5 secondi prima di riprovare il ripristino
            continue

def connection_bot():
    while True:
        try:
            if not bot.infinity_polling():
                bot.infinity_polling()
        except Exception as e:
            print("Connessione bot persa. Ripristino in corso...")
            time.sleep(5)  # Attendere per 5 secondi prima di riprovare il ripristino
            continue

# ------------------------------------------------------------------------------
#
# Creazione della coda dei messaggi
message_queue = queue.Queue()
t5 = threading.Thread(target=process_message_queue)
t5.daemon = True
t5.start()

bot.remove_webhook()
# bot.polling()
if __name__ == "__main__":
    update_wrapper()

    TIME = "09:00"

    #schedule.every().day.at("00:00", "Europe/Rome").do(daily_trigger)

    #schedule.every().monday.at(TIME, "Europe/Rome").do(update_wrapper)
    #schedule.every().tuesday.at(TIME, "Europe/Rome").do(update_wrapper)
    #schedule.every().wednesday.at(TIME, "Europe/Rome").do(update_wrapper)
    #schedule.every().thursday.at(TIME, "Europe/Rome").do(update_wrapper)
    #schedule.every().friday.at(TIME, "Europe/Rome").do(update_wrapper)

    print("schedule passati")

    t2 = Thread(target=schedule_checker)
    t2.daemon = True
    t2.start()

    t = threading.Thread(target=connection_server)
    t.daemon = True
    #t.start()

    t_bot = threading.Thread(target=connection_bot)
    t_bot.daemon = True
    t_bot.start()

    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5599)))

#
# ------------------------------------------------------------------------------