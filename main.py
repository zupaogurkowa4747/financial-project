from datetime import date
import os
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for, flash
from database import init_db, pobierz_wszystkie_transakcje, pobierz_opis, zapisz_opis, dodaj_transakcje, pobierz_sume, pobierz_wplaty, pobierz_wyplaty, usun_transakcje, pobierz_wydatki, dodaj_wydatek, pobierz_sume_wydatkow, pobierz_wydatki_wg_kategorii, pobierz_wydatki_miesiaca, pobierz_pozycje_miesiaca, zapisz_zarobki, pobierz_zarobki, usun_wydatek
from google import genai
from livereload import Server
load_dotenv()  
client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))  

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

model = "gemini-3.8-flash"

def dane_strony(ai_rada=""):
    return {
        "transakcje": pobierz_wszystkie_transakcje(),
        "suma": pobierz_sume(),
        "wplaty": pobierz_wplaty(),
        "wyplaty": pobierz_wyplaty(),
        "ai_rada": ai_rada,
    }

def zapytaj_ai(prompt):
    try:
        ai_response = client.models.generate_content(model=model, contents=prompt)
        return ai_response.text
    except Exception as e:
        print("Błąd ai: ", e)
        return "Nie udało się wygenerować tekstu AI."

@app.route('/')
def index():
    return render_template('index.html', **dane_strony())

@app.route('/wplata', methods=['POST'])
def wplata():
    kwota = request.form.get('kwota')
    if kwota and 0 < float(kwota) <= 1000000000:
        dodaj_transakcje(str(date.today()), float(kwota), "wpłata")
    return redirect(url_for('index'))

@app.route('/wyplata', methods=['POST'])
def wyplata():
    kwota = request.form.get('kwota')
    if kwota and float(kwota) > 0:
        if float(kwota) <= pobierz_sume():
            dodaj_transakcje(str(date.today()), -float(kwota), "wypłata")
        else:
            flash("Nie masz wystarczających środków na wypłatę tej kwoty.")
    return redirect(url_for('index'))

@app.route('/rada', methods=['POST'])
def rada():
    suma = pobierz_sume()
    prompt = f"Użytkownik ma w skarbcu {suma} zł. Daj mu jedną krótką radę finansową po polsku."
    ai_rada = zapytaj_ai(prompt)
    return render_template('index.html', **dane_strony(ai_rada=ai_rada))

@app.route('/usun', methods=['POST'])
def usun():
    id = request.form.get('id')
    if id:
        usun_transakcje(int(id))
    return redirect(url_for('index'))

@app.route('/wydatki')
def wydatki():
    return render_template('wydatki.html', **dane_wydatkow())

@app.route('/dodaj_wydatek', methods=["POST"])
def dodaj_wydatek_trasa():
    kwota = request.form.get('kwota')
    kategoria = request.form.get('kategoria')
    opis = request.form.get('opis')
    if kwota and 0 < float(kwota) <= 1000000000:
        dodaj_wydatek(str(date.today()), float(kwota), kategoria, opis)
    return(redirect(url_for('wydatki')))

def opis_wydatkow(grupy):
    return ", ".join(f"{k}: {s:.2f} zł" for k, s in grupy)

def opis_pozycji(pozycje):
    return "; ".join(f"{k} {c:.2f} zł ({o or 'bez opisu'})" for k, c, o in pozycje)

@app.route('/rada_wydatki', methods=["POST"])
def rada_wydatki():
    miesiac = date.today().strftime("%Y-%m")
    grupy = pobierz_wydatki_miesiaca(miesiac)
    if not grupy:
        ai_rada = 'Nie mam danych z tego miesiąca do wygenerowania rady AI'
    else:
        pozycje = pobierz_pozycje_miesiaca(miesiac)
        razem = sum(s for k, s in grupy)
        zarobki = pobierz_zarobki()
        opis = pobierz_opis()
        kontekst = ""
        if zarobki > 0:
            kontekst += f"Miesięczny dochód użytkownika: {zarobki:.2f} zł."
        if opis:
            kontekst += f"Opis sytuacji użytkownika: {opis} "
        prompt = f"""W miesiącu {miesiac} użytkownik wydał łącznie {razem: .2f} zł. Wydatki wg kategorii: {opis_wydatkow(grupy)}.
        {kontekst}
        Pojedyncze wydatki: {opis_pozycji(pozycje)}
    Na koncie oszczędnościowym (skarbcu) ma {pobierz_sume():.2f} zł. 
    Oceń krótko po polsku, co robi dobrze, co źle, i stwierdź, które kategorie można byłoby ograniczyć w następnym miesiącu. Ocena to przypuszczenie.
    Oceń, które wydatki były potrzebne, a które impulsywne i były stratą pieniędzy
    Odpowiedz zwykłym tekstem: bez gwiazdek, bez markdown, bez nagłówków. Maksymalnie 4 zdania. Uwzględnij sytuacje użytkownika."""
        ai_rada = zapytaj_ai(prompt)
    return render_template('wydatki.html', **dane_wydatkow(ai_rada=ai_rada))

@app.route('/usun_wydatek', methods=['POST'])
def usun_caly_wydatek():
    id = request.form.get('id')
    if id:
        usun_wydatek(int(id))
    return redirect(url_for('wydatki'))


@app.route('/zarobki', methods=['POST'])
def zarobki_trasa():
    kwota = request.form.get('zarobki')
    if kwota and 0 < float(kwota) <= 1000000000:
        zapisz_zarobki(float(kwota))
    return redirect(url_for('wydatki'))

@app.route('/opis', methods=["POST"])
def opis_trasa():
    opis = request.form.get('opis')
    zapisz_opis(opis.strip())
    return redirect(url_for('wydatki'))

def dane_wydatkow(ai_rada=""):
    return {
        "lista": pobierz_wydatki(),
        "wynik_grupowania": pobierz_wydatki_wg_kategorii(),
        "suma_wydatkow": pobierz_sume_wydatkow(),
        "ai_rada": ai_rada,
        "zarobki": pobierz_zarobki(),
        "opis": pobierz_opis()
    }

if __name__ == '__main__':
    init_db()
    server = Server(app.wsgi_app)

    server.watch('templates/*.html')
    server.watch('static/*.css')
    server.serve(port=5000, debug=True)

