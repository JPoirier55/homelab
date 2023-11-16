from flask import Flask, redirect, request, session, url_for, render_template, jsonify
import requests
from requests_oauthlib import OAuth2Session
from dotenv import dotenv_values
import os 

config = dotenv_values(".env") 
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = config['app_secret_key']

REDIRECT_URI = 'http://localhost:5000/google-callback'
GOOGLE_AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://www.googleapis.com/oauth2/v4/token'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    """Function to login and authorize access to Google Books API."""
    google_client_id = config['google_client_id']
    google = OAuth2Session(google_client_id, redirect_uri=REDIRECT_URI, scope=['https://www.googleapis.com/auth/books'])
    authorization_url, state = google.authorization_url(GOOGLE_AUTHORIZATION_URL, access_type="offline", prompt="select_account")
    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/google-callback')
def callback():
    """Callback route for handling the response from Google."""
    google_client_id = config['google_client_id']
    google_client_secret = config['google_client_secret']
    google = OAuth2Session(google_client_id, state=session['oauth_state'], redirect_uri=REDIRECT_URI)
    token = google.fetch_token(GOOGLE_TOKEN_URL, client_secret=google_client_secret, authorization_response=request.url)
    session['oauth_token'] = token
    return redirect(url_for('book'))

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    weather_data = {}
    if request.method == 'POST':
        city = request.form['city']
        api_key = config['open_weather_key']  # Replace with your API key
        city_lat_long = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={api_key}"
        lat_long_resp = requests.get(city_lat_long).json()
        lat = lat_long_resp[0]['lat']
        long = lat_long_resp[0]['lon']
        print(lat)
        print(long)
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={long}&units=imperial&appid={api_key}"
        
        response = requests.get(weather_url)
        print(response.text)
        if response.ok:
            data = response.json()
            weather_data = {
                'city': city,
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon']
            }
        else:
            weather_data = {
                'city': 'NA',
                'temperature': '0',
                'description': 'No results',
                'icon': 'NA'
            }
    
    return render_template('weather.html', weather=weather_data)

@app.route('/nasa')
def nasa():
    nasa_key = config['nasa_key']
    url = f"https://api.nasa.gov/planetary/apod?api_key={nasa_key}"
    response = requests.get(url)
    image_data = {}
    if response.ok:
        data = response.json()
        image_data = {
            'title': data['title'],
            'image_url': data['url'],
            'explanation': data['explanation']
        }
    else:
        image_data = {
            'title': 'asdf',
            'image_url': 'sdfsdf',
            'explanation': 'gggg'
        }
    return render_template('nasa.html', image_data=image_data)

@app.route('/book')
def book():
    api_key = config['books_key']
    query = 'bestsellers'  # Example query
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}&maxResults=10&orderBy=relevance"

    response = requests.get(url)
    books_data = []
    if response.ok:
        data = response.json()
        items = data.get('items', [])
        for book in items:
            books_data.append({
                'title': book['volumeInfo']['title'],
                'authors': book['volumeInfo'].get('authors', []),
                'averageRating': book['volumeInfo'].get('averageRating', 'Not available'),
                'thumbnail': book['volumeInfo']['imageLinks']['thumbnail']
            })

    return render_template('book.html', books=books_data)

def get_books(query, search_type, page):
    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Construct the query based on the search type
    if search_type == 'title':
        search_query = f'intitle:{query}'
    elif search_type == 'author':
        search_query = f'inauthor:{query}'
    elif search_type == 'genre':
        search_query = f'insubject:{query}'
    else:
        return jsonify({"error": "Invalid search type"}), 400

    api_url = f"https://www.googleapis.com/books/v1/volumes?q={search_query}&startIndex={page}"

    response = requests.get(api_url)
    if response.ok:
        books = response.json()
        books_data = books['items']
        return books_data, 200
    else:
        return jsonify({"error": "Failed request"}), 400


@app.route('/search-books', methods=['GET'])
def search_books():
    return render_template('search_books.html')
    

@app.route('/get-books', methods=['GET'])
def fetch_books():
    query = request.args.get('query')  # User's search query
    search_type = request.args.get('type', 'title')  # 'title', 'author', or 'genre'
    page = request.args.get('page', 1)

    books_data = get_books(query, search_type, page)

    if books_data[1] == 200:
        return books_data[0]
    else:
        return books_data

@app.route('/add-book', methods=['POST'])
def add_book():
    if 'oauth_token' not in session:
        return redirect(url_for('login'))
    token = session['oauth_token']['access_token']
    volume_id = request.form.get('volume_id')
    shelf_id = '4' 
    request_url = f'https://www.googleapis.com/books/v1/my_library/bookshelves/{shelf_id}/addVolume'

    response = requests.post(request_url, headers={'Authorization': f"Bearer {token}", 'Content-type': 'application/json'}, params={'volumeId': volume_id})
    if not 'results' in response or len(response['results']) == 0:
        return redirect(url_for('my_library'))
    else:
        return jsonify({"success": False, "message": "Failed to add book."})
        
        

@app.route('/book/my_library')
def my_library():
    token = session['oauth_token']['access_token']
    print(token)
    url = f"https://www.googleapis.com/books/v1/my_library/bookshelves/4/volumes"

    response = requests.get(url, headers={'Authorization': f"Bearer {token}"})
    books_data = []
    print(response.text)
    if response.ok:
        data = response.json()
        items = data.get('items', [])
        for book in items:
            books_data.append({
                'title': book['volumeInfo']['title'],
                'authors': book['volumeInfo'].get('authors', []),
                'averageRating': book['volumeInfo'].get('averageRating', 'Not available'),
                'thumbnail': book['volumeInfo']['imageLinks']['thumbnail']
            })

    return render_template('my_library.html', books=books_data)

@app.route('/book/recommend')
def book_recommend():
    api_key = config['books_key']
    user_id = config['user_id']
    url = f"https://www.googleapis.com/books/v1/users/{user_id}/bookshelves/4/volumes?key={api_key}"

    response = requests.get(url)
    books_data = []
    print(response.text)
    if response.ok:
        data = response.json()
        items = data.get('items', [])
        for book in items:
            books_data.append({
                'title': book['volumeInfo']['title'],
                'authors': book['volumeInfo'].get('authors', []),
                'averageRating': book['volumeInfo'].get('averageRating', 'Not available'),
                'thumbnail': book['volumeInfo']['imageLinks']['thumbnail']
            })

    return render_template('book.html', books=books_data)

if __name__ == '__main__':
    app.run(debug=True)