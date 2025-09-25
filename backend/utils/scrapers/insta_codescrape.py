import json
import httpx
from urllib.parse import quote
from typing import Optional, List, Dict, Any
import asyncio
import re
import time

class InstagramScraper:
    """
    Modern Instagram scraper that handles current API requirements.
    Note: Instagram actively prevents scraping. This is for educational purposes only.
    """
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/',
            'X-IG-App-ID': '936619743392459',  # Instagram Web App ID
        }
        self.csrf_token = None
        
    async def initialize_session(self):
        """Initialize session and get CSRF token"""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers=self.headers
        )
        
        # Get initial page to extract CSRF token
        try:
            response = await self.session.get('https://www.instagram.com/')
            
            # Extract CSRF token from response
            csrf_match = re.search(r'"csrf_token":"([^"]+)"', response.text)
            if csrf_match:
                self.csrf_token = csrf_match.group(1)
                self.headers['X-CSRFToken'] = self.csrf_token
                print(f"CSRF Token obtained: {self.csrf_token[:20]}...")
            else:
                print("Warning: Could not extract CSRF token")
                
            # Extract session cookies
            cookies = response.cookies
            if cookies:
                print("Session cookies obtained")
                
        except Exception as e:
            print(f"Error initializing session: {e}")
            
    async def get_user_info(self, username: str) -> Optional[Dict]:
        """Get basic user information using the web interface"""
        try:
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            
            response = await self.session.get(
                url,
                headers={
                    **self.headers,
                    'X-IG-WWW-Claim': '0',
                    'X-ASBD-ID': '129477',
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('user')
            else:
                print(f"Error getting user info: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching user info: {e}")
            return None
            
    async def scrape_user_posts_alternative(
        self, 
        username: str, 
        max_posts: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Alternative method using the web profile endpoint.
        This is more reliable but returns limited data.
        """
        await self.initialize_session()
        
        user_info = await self.get_user_info(username)
        
        if not user_info:
            print(f"Could not find user: {username}")
            return []
            
        posts = []
        
        # Extract basic post information from user data
        edge_media = user_info.get('edge_owner_to_timeline_media', {})
        edges = edge_media.get('edges', [])
        
        for edge in edges[:max_posts]:
            node = edge.get('node', {})
            post_data = {
                'id': node.get('id'),
                'shortcode': node.get('shortcode'),
                'display_url': node.get('display_url'),
                'thumbnail_src': node.get('thumbnail_src'),
                'is_video': node.get('is_video'),
                'caption': node.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', ''),
                'comment_count': node.get('edge_media_to_comment', {}).get('count', 0),
                'like_count': node.get('edge_liked_by', {}).get('count', 0),
                'timestamp': node.get('taken_at_timestamp'),
                'owner_username': node.get('owner', {}).get('username', username),
            }
            posts.append(node)
            
        await self.session.aclose()
        return posts

async def main():
    """Example usage of the updated scraper"""
    scraper = InstagramScraper()
    
    username = "tanyarathi.02"
    
    print(f"Attempting to scrape posts from @{username}...")
    print("=" * 50)
    
    # Try the alternative method (more reliable)
    print("\nUsing web profile method:")
    posts = await scraper.scrape_user_posts_alternative(username, max_posts=8)
    
    if posts:
        print(f"\nSuccessfully scraped {len(posts)} posts")
        
        # Save to file
        output_file = f"{username}_posts.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {output_file}")
        
        # Display first post as example
        if posts:
            print("\nFirst post details:")
            first_post = posts[0]
            print(f"- ID: {first_post.get('id')}")
            print(f"- Shortcode: {first_post.get('shortcode')}")
            print(f"- Likes: {first_post.get('like_count')}")
            print(f"- Comments: {first_post.get('comment_count')}")
            caption = first_post.get('caption', '')
            if caption:
                print(f"- Caption: {caption[:100]}...")
    else:
        print("No posts found or scraping failed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")