from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import string
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'  # Cambia con una chiave sicura

# Funzione per generare un codice stanza casuale (es: "A1B2C3")
def genera_codice_stanza():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/', methods=['GET', 'POST'])
def home():
    codice = None  # Inizializza il codice a None
    if request.method == 'POST':
        codice = genera_codice_stanza()  # Genera un codice univoco
        session['codice_stanza'] = codice  # Salva il codice nella sessione
        return render_template('home.html', codice=codice)  # Passa il codice alla pagina
    return render_template('home.html', codice=None)

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice_accesso = request.form['codice_accesso']
    
    # Controllo se il codice inserito è valido
    if len(codice_accesso) < 8:
        return "Codice non valido!", 403
    
    prefisso = codice_accesso[:2]  # I primi due numeri identificano il ruolo
    codice_stanza = codice_accesso[2:]  # Il resto è il codice della stanza

    # Determina il ruolo in base al prefisso
    if prefisso == "59":
        ruolo = "Penelope"
    elif prefisso == "33":
        ruolo = "Eric"
    else:
        return "Codice non valido!", 403

    session['ruolo'] = ruolo  # Salva il ruolo nella sessione
    return redirect(url_for('stanza', codice=codice_stanza))

@app.route('/stanza/<codice>', methods=['GET', 'POST'])
def stanza(codice):
    ruolo = session.get('ruolo', 'Anonimo')  # Recupera il ruolo dall'utente

    # Verifica se la stanza esiste nel database
    with sqlite3.connect('stanza_virtuale.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM stanze WHERE codice = ?", (codice,))
        stanza = c.fetchone()

    if not stanza:
        return "Codice non valido!", 403

    stato, numero_penelope, numero_eric, chat, _ = stanza[1:]
    
    if chat is None:
        chat = ""

    if request.method == 'POST':
        if 'numero' in request.form:
            numero = request.form['numero']
            if ruolo == 'Penelope':
                numero_penelope = numero
            elif ruolo == 'Eric':
                numero_eric = numero

            with sqlite3.connect('stanza_virtuale.db') as conn:
                c = conn.cursor()
                c.execute("UPDATE stanze SET numero_penelope = ?, numero_eric = ? WHERE codice = ?", 
                          (numero_penelope, numero_eric, codice))
                conn.commit()

        if 'chat' in request.form:
            new_message = request.form['chat']
            chat += f"{ruolo}: {new_message}\n"
            with sqlite3.connect('stanza_virtuale.db') as conn:
                c = conn.cursor()
                c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
                conn.commit()

        if numero_penelope and numero_eric:
            with sqlite3.connect('stanza_virtuale.db') as conn:
                c = conn.cursor()
                c.execute("DELETE FROM stanze WHERE codice = ?", (codice,))
                conn.commit()
            return "Stanza chiusa!", 200

    return render_template('stanza.html', codice=codice, stato=stato, ruolo=ruolo, chat=chat)

# Funzione per autodistruggere stanze dopo 24 ore
def autodistruzione():
    while True:
        time.sleep(3600)  # Controlla ogni ora
        with sqlite3.connect('stanza_virtuale.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM stanze WHERE timestamp < ?", (int(time.time()) - 86400,))
            conn.commit()

Thread(target=autodistruzione, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

