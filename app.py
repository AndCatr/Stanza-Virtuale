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
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        codice = genera_codice_stanza()  # Genera un codice unico
        session['codice'] = codice
        return redirect(url_for('stanza', codice=codice))  # Reindirizza alla stanza
    return render_template('home.html')

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
            chat += f"{session.get('ruolo')}: {new_message}\n"
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

    return render_template('stanza.html', stato=stato, uomo_ha_accesso=uomo_ha_accesso, 
                           donna_ha_accesso=donna_ha_accesso, chat=chat)

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
