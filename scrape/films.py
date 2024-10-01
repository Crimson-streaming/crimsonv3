import requests
from bs4 import BeautifulSoup
import re
import time
import json

# Fichier qui stocke le numéro actuel du sitemap
sitemap_number_file = "sitemap_number.txt"
max_sitemap_number = 22  # Limite à 22

# Fonction pour lire le numéro actuel du sitemap
def load_sitemap_number():
    try:
        with open(sitemap_number_file, "r") as file:
            number = int(file.read().strip())
        return number
    except FileNotFoundError:
        return 1  # Si le fichier n'existe pas, commencer à 1

# Fonction pour sauvegarder le nouveau numéro de sitemap
def save_sitemap_number(number):
    with open(sitemap_number_file, "w") as file:
        file.write(str(number))

# Fonction pour lire les titres de films à partir d'un fichier
def load_film_titles(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            titles = [line.strip() for line in file.readlines() if line.strip()]  # Enlever les espaces vides
        return titles
    except FileNotFoundError:
        print(f"Le fichier {filename} n'a pas été trouvé.")
        return []

# Fonction pour mettre à jour le fichier après suppression d'un film
def update_film_titles(filename, titles):
    with open(filename, 'w', encoding='utf-8') as file:
        for title in titles:
            file.write(f"{title}\n")

# Fonction pour scraper les liens des balises iframe
def scrape_links(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    try:
        # Envoyer une requête GET à la page web
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Vérifie si la requête s'est bien déroulée
        
        # Parser le contenu HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trouver tous les <iframe> avec src correspondant au format demandé
        iframes = soup.find_all('iframe', src=True)
        
        # Filtrer les iframes qui contiennent l'URL au format spécifique
        filtered_links = [iframe['src'] for iframe in iframes if re.match(r'https://lecteurvideo\.com/embed\.php\?id=\d+', iframe['src'])]
        
        return filtered_links

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'accès à la page {url} : {e}")
        return []

# Fonction pour stocker les informations dans un fichier texte
def save_to_file(filename, film_title, links):
    with open(filename, 'a', encoding='utf-8') as file:
        for link in links:
            file.write(f"{film_title} : {link}\n")

# Fonction pour traiter le nom du film (remplacer les tirets par des espaces)
def format_title(title):
    return title.replace('-', ' ').strip()

# Lire le fichier txt et transformer le contenu en JSON
def txt_to_json(txt_file, json_file):
    data = []
    existing_data = []  # Initialiser existing_data comme une liste vide
    
    # Lire les données existantes depuis le fichier JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as jsonf:
            existing_data = json.load(jsonf)  # Charger les données existantes
            existing_titles = {film['title'] for film in existing_data}  # Créer un ensemble de titres existants
    except FileNotFoundError:
        existing_titles = set()  # Si le fichier n'existe pas, créer un ensemble vide
    
    # Lire le fichier txt
    with open(txt_file, 'r', encoding='utf-8') as file:
        for line in file:
            if ':' in line:
                # Diviser à la première occurrence de ':' pour obtenir le titre et l'URL
                title, url = line.split(':', 1)
                formatted_title = format_title(title)
                
                # Vérifier si le titre n'est pas déjà dans les titres existants
                if formatted_title not in existing_titles:
                    film_data = {
                        "title": formatted_title,
                        "url": url.strip()
                    }
                    data.append(film_data)
    
    # Écrire les nouvelles données dans un fichier JSON
    if data:
        # Ajouter les nouvelles données aux données existantes
        existing_data.extend(data)

        with open(json_file, 'w', encoding='utf-8') as jsonf:
            json.dump(existing_data, jsonf, indent=4)
        print(f"{len(data)} nouveau(x) film(s) ajouté(s) dans {json_file}.")
    else:
        print("Aucun nouveau film à ajouter.")

# Fonction principale pour scraper plusieurs films récents
def scrape_movies(film_titles, base_url, filename):
    for film in film_titles:
        # Construire l'URL du film
        url = f"{base_url}/{film}"
        print(f"Scraping la page : {url}")
        
        # Scraper les liens
        page_links = scrape_links(url)
        
        # Si des liens ont été trouvés, les stocker dans le fichier
        if page_links:
            save_to_file('films.txt', film, page_links)
            print(f"Liens trouvés pour {film} et stockés.")

            # Convertir le fichier texte en JSON après avoir ajouté les liens
            txt_to_json('films.txt', '../films.json')
            
            # Supprimer le film de la liste
            film_titles.remove(film)
            update_film_titles(filename, film_titles)
            print(f"Le film '{film}' a été supprimé de la liste.")
        else:
            print(f"Aucun lien trouvé pour {film}.")
        
        # Attendre un peu pour éviter d'être bloqué
        time.sleep(1)

    # Vérifier si la liste est vide et lancer le programme de traitement des noms de films
    if not film_titles:
        print("Tous les films ont été traités.")

# Charger le numéro actuel
sitemap_number = load_sitemap_number()

# Si le numéro actuel est inférieur ou égal à la limite
if sitemap_number <= max_sitemap_number:
    # Créer l'URL du sitemap basé sur le numéro actuel
    sitemap_url = f"https://coflix.plus/movies-sitemap{sitemap_number}.xml"
    print(f"Scraping {sitemap_url}...")

    # Effectuer une requête pour récupérer le sitemap
    response = requests.get(sitemap_url)

    # Vérifier que la requête a réussi
    if response.status_code == 200:
        # Utiliser BeautifulSoup pour analyser le contenu XML
        soup = BeautifulSoup(response.content, 'lxml-xml')

        # Liste pour stocker les noms de films
        movie_names = []

        # Extraire les URLs des films à partir des balises <loc>
        for loc in soup.find_all('loc'):
            movie_url = loc.text
            if '/film/' in movie_url:
                # Extraire le nom du film à partir de l'URL
                movie_name = movie_url.split('/film/')[-1].rstrip('/')  # Supprimer le slash final
                movie_names.append(movie_name)

        # Écrire les noms des films dans un fichier texte en mode ajout
        with open("noms_de_films.txt", "a", encoding="utf-8") as file:
            for name in movie_names:
                file.write(name + "\n")

        print(f"Noms des films récupérés et ajoutés à noms_de_films.txt depuis {sitemap_url}.")

        # Incrémenter le numéro de sitemap et sauvegarder le nouveau numéro
        sitemap_number += 1
        save_sitemap_number(sitemap_number)

        # Charger les titres de films depuis le fichier
        film_titles = load_film_titles('noms_de_films.txt')

        # Vérifier si des films ont été chargés
        if film_titles:
            # URL de base du site à scraper
            base_url = "https://coflix.plus/film"

            # Lancer le scraping sur les films
            scrape_movies(film_titles, base_url, 'noms_de_films.txt')
        else:
            print("Aucun titre de film à scraper.")
    else:
        print(f"Erreur lors de la récupération du sitemap {sitemap_url}: {response.status_code}")
else:
    print("Le numéro de sitemap a atteint la limite de 22. Scraping terminé.")
