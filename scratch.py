import requests

r = requests.get("https://store.steampowered.com/api/featured/")
print(r)

# import requests
# login = {'Username':'admin','Password':'Time12line?'}
# s = requests.Session()
# response = s.post('http://192.168.1.1/',data=login)
# print(response.content)