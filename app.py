from flask import Flask, render_template, request
import numpy as np

app = Flask(__name__)

# Funktion zur Berechnung des Fehlers basierend auf den aktuellen Blockzahlen
def berechne_fehler(block_counts, block_weights, pizza_weights):
    total_weight = sum(np.array(block_counts) * np.array(block_weights))  # Gesamtgewicht der Käsemenge
    
    if total_weight == 0:
        return float('inf')  # Vermeide Division durch 0
    
    error = 0
    
    for i in range(len(block_counts)):
        ratio = (block_counts[i] * block_weights[i]) / total_weight  # Verhältnis für jede Käsesorte
        ideal_ratio = pizza_weights[i] / sum(pizza_weights)  # Ideales Verhältnis
        error += (ratio - ideal_ratio) ** 2  # Quadratische Abweichung zum Ideal
    
    return error

# Funktion zur Berechnung der optimalen Anzahl der Blöcke
def berechne_optimal_bloecke(block_weights, pizza_weights, maxb):
    n = len(block_weights)
    block_counts = np.ones(n, dtype=int)

    # Iteration, um die Blöcke zu optimieren (suche nach der besten Kombination)
    min_error = float('inf')  # Anfangswert für minimalen Fehler
    optimal_counts = block_counts.copy()

    # Iteriere durch mögliche Blockanzahlen (z.B. 1 bis 20 Blöcke für jede Käsesorte)
    for counts in np.ndindex(*([maxb] * n)):  # Alle Kombinationen bis zu 20 Blöcke pro Käsesorte
        block_counts = np.array(counts) + 1  # Verschiebe um 1, da wir ab 1 Block zählen
            
        # Berechne den Fehler für diese Kombination
        current_error = berechne_fehler(block_counts, block_weights, pizza_weights)
        
        # Aktualisiere, wenn der Fehler kleiner ist als der bisherige minimale Fehler
        if current_error < min_error:
            min_error = current_error
            optimal_counts = block_counts.copy()

    return optimal_counts

# Funktion zur Berechnung der Anzahl der Pizzen, die mit den Blöcken gemacht werden können
def berechne_pizzen(optimal_counts, block_weights, pizza_weights):
    pizzen_pro_sorte = []
    for i in range(len(optimal_counts)):
        # Gesamtgewicht des Käses für jede Sorte (Anzahl der Blöcke * Blockgewicht)
        gesamtgewicht_kaese = optimal_counts[i] * block_weights[i] * 1000  # Umwandlung in Gramm
        # Anzahl der Pizzen: Gesamtgewicht geteilt durch den Käsebedarf pro Pizza
        pizzen = gesamtgewicht_kaese // pizza_weights[i]
        pizzen_pro_sorte.append(int(pizzen))
    return pizzen_pro_sorte

# Funktion zur gleichmäßigen Aufteilung der Blöcke in Gruppen
import math

def aufteilen_in_gruppen(optimal_counts, max_total):
    total = sum(optimal_counts)

    if max_total <= 0 or total <= max_total:
        return None  # Keine Aufteilung nötig

    # Anzahl der Gruppen berechnen
    num_gruppen = math.ceil(total / max_total)

    # Jede Sorte gleichmäßig auf die Gruppen verteilen
    gruppen = []
    for g in range(num_gruppen):
        gruppe = []
        for bloecke in optimal_counts:
            basis = int(bloecke) // num_gruppen
            rest = int(bloecke) % num_gruppen
            # Die ersten 'rest' Gruppen bekommen einen Block mehr
            if g < rest:
                gruppe.append(basis + 1)
            else:
                gruppe.append(basis)
        gruppen.append(gruppe)

    return gruppen

@app.route('/käse')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    # Anzahl der Käsesorten ermitteln
    num_sorten = int(request.form['num_sorten'])
    maxb = int(request.form['max'])
    max_total = int(request.form['max_total'])
    # Lese die Eingabedaten für alle Käsesorten
    pizza_name = []
    block_weights = []
    pizza_weights = []
    for i in range(num_sorten):
        block_weights.append(float(request.form[f'block_weight_{i+1}'].replace(",", ".")))
        pizza_weights.append(float(request.form[f'pizza_weight_{i+1}'].replace(",", ".")))
        pizza_name.append(request.form.get(f'name_{i+1}'))
        pizza_name[i] = pizza_name[i] + "(" + str(block_weights[i]) + "kg)"
    # Optimierung der Blöcke durchführen
    optimal_counts = berechne_optimal_bloecke(block_weights, pizza_weights, maxb)

    # Berechnung der Pizzen (Gesamt)
    pizzen_pro_sorte = berechne_pizzen(optimal_counts, block_weights, pizza_weights)

    # Prüfe ob Aufteilung in Gruppen nötig ist
    gruppen = aufteilen_in_gruppen(optimal_counts, max_total)

    if gruppen is not None:
        # Pizzen pro Gruppe berechnen
        gruppen_pizzen = []
        for gruppe in gruppen:
            pizzen = berechne_pizzen(gruppe, block_weights, pizza_weights)
            gruppen_pizzen.append(pizzen)

        return render_template('result.html',
            optimal_counts=optimal_counts,
            pizzen_pro_sorte=pizzen_pro_sorte,
            num_sorten=num_sorten,
            name=pizza_name,
            gruppen=gruppen,
            gruppen_pizzen=gruppen_pizzen,
            num_gruppen=len(gruppen))
    else:
        return render_template('result.html',
            optimal_counts=optimal_counts,
            pizzen_pro_sorte=pizzen_pro_sorte,
            num_sorten=num_sorten,
            name=pizza_name,
            gruppen=None,
            gruppen_pizzen=None,
            num_gruppen=0)

if __name__ == '__main__':
    app.run(debug=True)
