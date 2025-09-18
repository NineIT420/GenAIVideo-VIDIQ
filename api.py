'''
Definition of the API to be used by the vidIQ scraper.
The API is defined using the fastapi framework.
'''
###### Imports #######
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

# Custom imports
import VidIQ as viq

login_manager = None  # Placeholder

@asynccontextmanager
async def lifespan(app: FastAPI):
    global login_manager
    login_manager = await viq.VidIQLogin.create()
    isLoggedIn = await login_manager.is_logged_in()
    if not isLoggedIn:
        try:
            print("🔄 Logging in at startup...")
            await login_manager.login_to_email()
            print("🔄 Logging in to vidIQ...")
            await login_manager.login_to_vidiq()
            print("✅ Logged in successfully at startup.")
        except Exception as e:
            print(f"❌ Error during login at startup: {str(e)}")
    else:
        print("✅ Already logged in with saved credentials.")
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/vidiq/keyword/{keyword}")
async def get_keywords_scores(keyword: str):
    ''' 
    returns following vidIQ metrics:
        - overall score, 
        - score category (high, medium, low, etc.)
        - search volume
        - search volume category
        - competition score
        - competition category
    '''
    page = await login_manager.is_logged_in()
    results = []
    results = await login_manager.find_keywords(page=page,keyword=keyword)
    if not results:
        return {"message": "No results found for the given keyword."}
    return results

@app.get("/vidiq/most_popular/{keyword}")
async def get_most_popular(keyword: str):
    '''
    returns list of VidIQ 'outlier' videos w.r.t. a keyword, each as a dict
    '''
    page = await login_manager.is_logged_in()
    results = []
    results = await login_manager.find_trending_videos(page=page,keyword=keyword)
    if not results:
        return {"message": "No results found."}
    return results

if __name__ == "__main__":
   uvicorn.run(app, host="0.0.0.0", port=9090)