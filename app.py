from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import string
import time
from threading import Thread

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'  # Cambia con una chiave sicura

# Funzione per generare un codice stanza casuale (solo numeri)
def genera_codice_stanza():
    return ''.join(random.choices(string.digits, k=4))  # Codice stanza di 4 cifre

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'codice' not in session:
        session['codice'] = genera_codice_stanza()  # Genera un codice stanza alla prima visita
    
    codice = session['codice']  # Recupera il codice dalla sessione
    return render_template('home.html', codice=codice)  # Passa il codice al template

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice_accesso = request.form.get('codice_accesso')
    
    # Verifica che il codice sia nel formato corretto (59XXXX per Penelope, 33XXXX per Eric)
    if len(codice_accesso) != 6 or not codice_accesso.isdigit():
        return "Codice non valido!", 403

    # Estrai la parte del codice stanza
    codice_stanza = codice_accesso[2:]

    # Determina il personaggio in base al prefisso
    if codice_accesso.startswith('59'):
        session['ruolo'] = 'Penelope'
    elif codice_accesso.startswith('33'):
        session['ruolo'] = 'Eric'
    else:
        return "Codice di accesso non valido!", 403

    return redirect(url_for('stanza', codice=codice_stanza))

@app.route('/stanza/<codice>', methods=['GET', 'POST'])
def stanza(codice):
    return f"Benvenuto nella stanza {codice}. Sei {session.get('ruolo', 'Sconosciuto')}."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
