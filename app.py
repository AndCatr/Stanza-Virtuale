from flask import Flask, render_template, request, redirect, url_for, session
import random
import string

app = Flask(__name__)
app.secret_key = 'chiave_super_segreta'  # Cambia con una chiave sicura

# Simuliamo un database con un dizionario
stanze = {}

# Funzione per generare un codice stanza casuale (alfanumerico di 6 caratteri)
def genera_codice_stanza():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) 

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'codice' not in session:
        session['codice'] = genera_codice_stanza()  # Genera un codice stanza alla prima visita
    
    codice = session['codice']  # Recupera il codice dalla sessione

    # Crea la stanza se non esiste
    if codice not in stanze:
        stanze[codice] = {"chat": [], "numeri": {"Penelope": "", "Eric": ""}}

    return render_template('home.html', codice=codice)

@app.route('/ingresso', methods=['POST'])
def ingresso():
    codice_accesso = request.form.get('codice_accesso')
    
    # Verifica se il codice di accesso ha la lunghezza corretta (2 prefisso + 6 codice stanza)
    if len(codice_accesso) != 8 or not codice_accesso[2:].isalnum():
        return "Codice non valido!", 403

    # Estrai la parte del codice stanza
    codice_stanza = codice_accesso[2:]

    # Controlla che il codice della stanza sia quello generato
    if codice_stanza != session.get('codice'):
        return "Codice di accesso non valido!", 403

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
    ruolo = session.get('ruolo', 'Sconosciuto')

    if codice not in stanze:
        return "Stanza non trovata!", 404

    # Gestione chat
    if request.method == 'POST' and 'messaggio' in request.form:
        messaggio = request.form['messaggio']
        stanze[codice]["chat"].append((ruolo, messaggio))

    # Gestione numeri di telefono
    if request.method == 'POST' and 'numero' in request.form:
        numero = request.form['numero']
        stanze[codice]["numeri"][ruolo] = numero

    return render_template(
        'stanza.html',
        codice=codice,
        ruolo=ruolo,
        chat=stanze[codice]["chat"],
        numeri=stanze[codice]["numeri"]
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
