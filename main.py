from flask import Flask, render_template, request
import requests

app = Flask(__name__)

NASA_API_KEY = ''  # Replace with your actual NASA API key


@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = {}
    if request.method == 'POST':
        city = request.form['city']
        api_key = ''  # Replace with your API key
        weather_url = f"https://api.openweathermap.org/data/2.5/onecall?lat=33.44&lon=-94.04&appid={api_key}"
        
        response = requests.get(weather_url)
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
                'city': 'buxton',
                'temperature': '34',
                'description': 'fuckin buxton',
                'icon': 'sun'
            }
    
    return render_template('index.html', weather=weather_data)

@app.route('/nasa')
def nasa():
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
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

if __name__ == '__main__':
    app.run(debug=True)