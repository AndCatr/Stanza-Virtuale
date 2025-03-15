from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import string
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'  # Cambia con una chiave sicura

# Funzione per generare un codice stanza casuale
def genera_codice_stanza():
    return ''.join(random.choices(string.digits, k=4))  # Genera una stanza a 4 cifre

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        codice_stanza = genera_codice_stanza()  # Genera un codice stanza univoco (es: 1212)
        session['codice_stanza'] = codice_stanza
        return render_template('home.html', codice_stanza=codice_stanza)  # Mostra il codice della stanza
    return render_template('home.html')

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice_ingresso = request.form['codice']
    
    if len(codice_ingresso) < 6:
        return "Codice non valido!", 403

    codice_prefix = codice_ingresso[:2]  # Prendi i primi due numeri
    codice_stanza = codice_ingresso[2:]  # Prendi gli ultimi quattro numeri

    with sqlite3.connect('stanza_virtuale.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM stanze WHERE codice = ?", (codice_stanza,))
        stanza = c.fetchone()

        if not stanza:
            return "Codice stanza non valido!", 403

        # Assegna il ruolo in base al codice di ingresso
        if codice_prefix == "59":
            session['ruolo'] = 'F'  # Penelope
        elif codice_prefix == "33":
            session['ruolo'] = 'M'  # Eric
        else:
            return "Codice di ingresso errato!", 403

        session['codice_stanza'] = codice_stanza
        return redirect(url_for('stanza', codice=codice_stanza))  # Reindirizza alla stanza

@app.route('/stanza/<codice>', methods=['GET', 'POST'])
def stanza(codice):
    with sqlite3.connect('stanza_virtuale.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM stanze WHERE codice = ?", (codice,))
        stanza = c.fetchone()

    if not stanza:
        return "Codice non valido!", 403

    stato, uomo_ha_accesso, donna_ha_accesso, numero_uomo, numero_donna, chat, _ = stanza[1:]
    
    if chat is None:
        chat = ""

    if request.method == 'POST':
        if 'numero' in request.form:
            numero = request.form['numero']
            if session.get('ruolo') == 'M':
                numero_uomo = numero
            else:
                numero_donna = numero
            with sqlite3.connect('stanza_virtuale.db') as conn:
                c = conn.cursor()
                c.execute("UPDATE stanze SET numero_uomo = ?, numero_donna = ? WHERE codice = ?", 
                          (numero_uomo, numero_donna, codice))
                conn.commit()

        if 'chat' in request.form:
            new_message = request.form['chat']
            chat += f"{'Penelope' if session.get('ruolo') == 'F' else 'Eric'}: {new_message}\n"
            with sqlite3.connect('stanza_virtuale.db') as conn:
                c = conn.cursor()
                c.execute("UPDATE stanze SET chat = ? WHERE codice = ?", (chat, codice))
                conn.commit()

        if numero_uomo and numero_donna:
            with sqlite3.connect('stanza_virtuale.db') as conn:
                c = conn.cursor()
                c.execute("DELETE FROM stanze WHERE codice = ?", (codice,))
                conn.commit()
            return "Stanza chiusa!", 200

    return render_template('stanza.html', codice=codice, stato=stato, 
                           uomo_ha_accesso=uomo_ha_accesso, donna_ha_accesso=donna_ha_accesso, chat=chat)

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
