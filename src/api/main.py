from fastapi import FastAPI   #fastapi is the class through which we can make our webpage.
from src.database.db_connection import load_config # Importing the load_config function from the db_connection module in the src.database package.
#It reads from the config.yaml file and ['api'] section of the config.yaml file and returns a dictionary containing the API configuration settings.
cfg=load_config()['api']  # Load the API configuration settings from the config.yaml file.
app = FastAPI(title=cfg['title'], version=cfg['version'])
@app.get("/")
def root():
    return {"message": "Welcome to the Supply Chain Decision Intelligence API!"}  # Return a welcome message when the root endpoint is accessed.
@app.get("/health")
def health():
    return {"status": "ok"}  # Return a health status message when the /health endpoint is accessed.