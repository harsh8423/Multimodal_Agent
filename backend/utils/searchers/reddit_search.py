import praw
import os
from typing import Dict, List, Any
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def create_reddit_instance() -> praw.Reddit:
    """Create and return a Reddit instance using environment variables."""
    return praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditSearchAPI/1.0')
    )


def extract_post_data(post: praw.models.Submission) -> Dict[str, Any]:
    """Extract relevant data from a Reddit post submission."""
    return {
        'id': post.id,
        'title': post.title,
        'author': str(post.author) if post.author else '[deleted]',
        'subreddit': str(post.subreddit),
        'url': post.url,
        'permalink': f"https://reddit.com{post.permalink}",
        'selftext': post.selftext,
        'upvotes': post.score,
        'upvote_ratio': post.upvote_ratio,
        'num_comments': post.num_comments,
        'created_utc': post.created_utc,
        'created_time': datetime.fromtimestamp(post.created_utc).isoformat(),
        'is_self': post.is_self,
        'over_18': post.over_18,
        'spoiler': post.spoiler,
        'stickied': post.stickied,
        'distinguished': post.distinguished,
        'link_flair_text': post.link_flair_text,
        'gilded': post.gilded,
        'locked': post.locked
    }


def search_reddit(query: str, limit: int = 50, days_back: int = 30) -> Dict[str, Any]:
    """
    Search Reddit posts using a query string.
    
    Args:
        query: Search query (e.g., "trending ai tools for coding")
        limit: Maximum number of results to return
        days_back: Number of days to search back (filters by time)
    
    Returns:
        Dictionary containing search results and metadata
    """
    reddit = create_reddit_instance()
    
    # Calculate time filter based on days_back
    if days_back <= 1:
        time_filter = 'day'
    elif days_back <= 7:
        time_filter = 'week'
    elif days_back <= 30:
        time_filter = 'month'
    elif days_back <= 365:
        time_filter = 'year'
    else:
        time_filter = 'all'
    
    try:
        # Search across all subreddits
        search_results = reddit.subreddit('all').search(
            query, 
            sort='relevance', 
            time_filter=time_filter, 
            limit=limit
        )
        
        posts = []
        cutoff_time = (datetime.now() - timedelta(days=days_back)).timestamp()
        
        for post in search_results:
            # Filter by exact days_back if needed
            if post.created_utc >= cutoff_time:
                try:
                    post_data = extract_post_data(post)
                    posts.append(post_data)
                except Exception as e:
                    print(f"Error processing post {post.id}: {str(e)}")
                    continue
        
        # Sort by score (upvotes) in descending order
        posts.sort(key=lambda x: x['upvotes'], reverse=True)
        
        return {
            'metadata': {
                'query': query,
                'total_results': len(posts),
                'limit': limit,
                'days_back': days_back,
                'time_filter_used': time_filter,
                'timestamp': datetime.now().isoformat()
            },
            'posts': posts
        }
        
    except Exception as e:
        print(f"Error searching Reddit: {str(e)}")
        return {
            'metadata': {
                'query': query,
                'total_results': 0,
                'limit': limit,
                'days_back': days_back,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            },
            'posts': []
        }


def save_results(data: Dict[str, Any], filename: str) -> None:
    """Save search results to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def display_results(data: Dict[str, Any], max_posts: int = 5) -> None:
    """Display search results in a readable format."""
    metadata = data['metadata']
    posts = data['posts'][:max_posts]
    
    print(f"\n{'='*80}")
    print(f"SEARCH RESULTS FOR: '{metadata['query']}'")
    print(f"{'='*80}")
    print(f"Total results: {metadata['total_results']}")
    print(f"Days searched: {metadata['days_back']}")
    print(f"Showing top {len(posts)} posts:")
    
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. {post['title']}")
        print(f"   r/{post['subreddit']} | Score: {post['upvotes']} | Comments: {post['num_comments']}")
        print(f"   Author: {post['author']} | Date: {post['created_time'][:10]}")
        print(f"   {post['permalink']}")
        
        if post['selftext'] and len(post['selftext']) > 0:
            preview = post['selftext'][:200] + "..." if len(post['selftext']) > 200 else post['selftext']
            print(f"   Content: {preview}")


def main():
    """Example usage of the Reddit search functionality."""
    try:
        # Example search
        print("Searching for 'trending ai tools for coding'...")
        
        results = search_reddit(
            query="trending ai tools for coding",
            limit=5,
            days_back=30
        )
        
        display_results(results, max_posts=5)
        save_results(results, 'search_results.json')
        
        print(f"\nResults saved to 'search_results.json'")
        
    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()