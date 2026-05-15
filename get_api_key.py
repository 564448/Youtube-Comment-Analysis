def get_api_key(filename):
    with open(filename,mode='r') as file:
        line = file.readline()
    return line
    
if __name__ == "__main__" :
    print(get_api_key("API_Key.txt"))