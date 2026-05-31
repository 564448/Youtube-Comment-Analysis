def get_api_key(filename):
    try:
        with open(filename, "r") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return None
    
if __name__ == "__main__" :
    print(get_api_key("API_Key.txt"))