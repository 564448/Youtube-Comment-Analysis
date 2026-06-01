import ollama
def model_list():
    models = ollama.list()
    model_list=[]
    for model in models.models:
        model_list.append(model.model)
    return model_list