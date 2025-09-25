
import requests
from dotenv import load_dotenv
import os
import time

load_dotenv()

def scrape_linkedin_with_apify(profile_url: str, max_posts: int = 5, api_token: str = None):
    """
    Scrape LinkedIn profile posts using Apify's LinkedIn Profile Posts actor.

    Parameters:
        profile_url (str): The URL of the LinkedIn profile to scrape
        max_posts (int): Number of posts to scrape (default: 5)
        api_token (str): Your Apify API token (optional, will use env var if not provided)

    Returns:
        list: LinkedIn post data as JSON
    """
    if api_token is None:
        api_token = os.getenv("APIFY_API_TOKEN")
        if not api_token:
            raise ValueError("Apify API token not provided and APIFY_API_TOKEN environment variable not set")

    # Step 1: Start the actor run
    run_url = f"https://api.apify.com/v2/acts/harvestapi~linkedin-profile-posts/runs?token={api_token}"
    
    payload = {
        "includeQuotePosts": True,
        "includeReposts": True,
        "maxComments": 5,
        "maxPosts": max_posts,
        "maxReactions": 5,
        "scrapeComments": False,
        "scrapeReactions": False,
        "targetUrls": [profile_url]
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"Starting actor run for profile: {profile_url}")
    print(f"Payload: {payload}")
    
    # Start the actor run
    run_response = requests.post(run_url, headers=headers, json=payload)
    
    if run_response.status_code not in [200, 201]:
        raise Exception(f"Failed to start actor run: {run_response.status_code}, {run_response.text}")
    
    run_data = run_response.json()
    run_id = run_data.get("data", {}).get("id")
    
    if not run_id:
        raise Exception(f"No run ID returned: {run_data}")
    
    print(f"Actor run started with ID: {run_id}")
    
    # Step 2: Wait for the run to complete and get results
    max_wait_time = 300  # 5 minutes
    wait_interval = 10   # 10 seconds
    
    for attempt in range(max_wait_time // wait_interval):
        # Check run status
        status_url = f"https://api.apify.com/v2/acts/harvestapi~linkedin-profile-posts/runs/{run_id}?token={api_token}"
        status_response = requests.get(status_url)
        
        if status_response.status_code != 200:
            print(f"Status check failed: {status_response.status_code}")
            time.sleep(wait_interval)
            continue
            
        status_data = status_response.json()
        status = status_data.get("data", {}).get("status")
        
        print(f"Run status: {status}")
        
        if status == "SUCCEEDED":
            # Get the dataset ID from the run data
            dataset_id = status_data.get("data", {}).get("defaultDatasetId")
            if not dataset_id:
                raise Exception(f"No dataset ID found in run data: {status_data}")
            
            # Get the dataset items using the correct endpoint
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_token}"
            dataset_response = requests.get(dataset_url)
            
            if dataset_response.status_code == 200:
                data = dataset_response.json()
                print(f"Data received: {len(data) if isinstance(data, list) else 'Not a list'}")
                return data
            else:
                raise Exception(f"Failed to get dataset: {dataset_response.status_code}, {dataset_response.text}")
                
        elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
            raise Exception(f"Actor run {status.lower()}: {status_data}")
            
        # Wait before next check
        time.sleep(wait_interval)
    
    raise Exception("Actor run timed out")

if __name__ == "__main__":
    print(scrape_linkedin_with_apify("https://www.linkedin.com/in/satyanadella/"))

