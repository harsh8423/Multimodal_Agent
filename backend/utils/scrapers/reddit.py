import praw
import os
from functools import partial, reduce
from typing import Dict, List, Optional, Callable, Any
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# Configuration
def create_reddit_instance() -> praw.Reddit:
    """Create and return a Reddit instance using environment variables."""
    return praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditAPI/1.0')
    )


# Pure functions for data transformation
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


def extract_comment_data(comment: praw.models.Comment) -> Optional[Dict[str, Any]]:
    """Extract relevant data from a Reddit comment."""
    if isinstance(comment, praw.models.MoreComments):
        return None
    
    return {
        'id': comment.id,
        'author': str(comment.author) if comment.author else '[deleted]',
        'body': comment.body,
        'score': comment.score,
        'created_utc': comment.created_utc,
        'created_time': datetime.fromtimestamp(comment.created_utc).isoformat(),
        'is_submitter': comment.is_submitter,
        'distinguished': comment.distinguished,
        'gilded': comment.gilded,
        'stickied': comment.stickied,
        'depth': comment.depth if hasattr(comment, 'depth') else 0,
        'parent_id': comment.parent_id,
        'permalink': f"https://reddit.com{comment.permalink}"
    }


def filter_valid_comments(comments: List[Optional[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Filter out None comments and return only valid ones."""
    return [comment for comment in comments if comment is not None]


def sort_comments_by_score(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort comments by score in descending order."""
    return sorted(comments, key=lambda x: x['score'], reverse=True)


def limit_comments(limit: int) -> Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]:
    """Return a function that limits the number of comments."""
    return lambda comments: comments[:limit]


def get_top_comments(post: praw.models.Submission, limit: int = 10) -> List[Dict[str, Any]]:
    """Get top comments for a post using functional composition."""
    # Ensure comments are loaded
    post.comments.replace_more(limit=0)
    
    # Functional pipeline for processing comments
    process_comments = lambda comments: (
        limit_comments(limit)(
            sort_comments_by_score(
                filter_valid_comments([
                    extract_comment_data(comment) 
                    for comment in comments
                ])
            )
        )
    )
    
    return process_comments(post.comments.list())


# Main functions for fetching data
def get_posts_by_category(reddit: praw.Reddit, subreddit_name: str, 
                         category: str, limit: int = 25) -> List[praw.models.Submission]:
    """Get posts from subreddit by category (hot, rising, new, top)."""
    subreddit = reddit.subreddit(subreddit_name)
    
    category_map = {
        'hot': subreddit.hot,
        'rising': subreddit.rising,
        'new': subreddit.new,
        'top': subreddit.top
    }
    
    if category not in category_map:
        raise ValueError(f"Invalid category: {category}. Must be one of {list(category_map.keys())}")
    
    return list(category_map[category](limit=limit))


def enrich_post_with_comments(comment_limit: int) -> Callable[[praw.models.Submission], Dict[str, Any]]:
    """Return a function that enriches post data with top comments."""
    def enrich_post(post: praw.models.Submission) -> Dict[str, Any]:
        post_data = extract_post_data(post)
        post_data['top_comments'] = get_top_comments(post, comment_limit)
        return post_data
    
    return enrich_post


def fetch_subreddit_posts(reddit: praw.Reddit, subreddit_name: str, 
                         category: str = 'hot', post_limit: int = 25, 
                         comment_limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch posts from a subreddit with their top comments.
    
    Args:
        reddit: Reddit instance
        subreddit_name: Name of the subreddit
        category: Category of posts ('hot', 'rising', 'new', 'top')
        post_limit: Number of posts to fetch
        comment_limit: Number of top comments per post
    
    Returns:
        List of dictionaries containing post and comment data
    """
    try:
        # Get posts using functional composition
        posts = get_posts_by_category(reddit, subreddit_name, category, post_limit)
        
        # Transform posts to include comments using map and functional composition
        enrich_with_comments = enrich_post_with_comments(comment_limit)
        enriched_posts = list(map(enrich_with_comments, posts))
        
        return enriched_posts
    
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return []


# Utility functions for filtering and processing
def filter_posts_by_score(min_score: int) -> Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]:
    """Return a function that filters posts by minimum score."""
    return lambda posts: [post for post in posts if post['upvotes'] >= min_score]


def filter_posts_by_comment_count(min_comments: int) -> Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]:
    """Return a function that filters posts by minimum comment count."""
    return lambda posts: [post for post in posts if post['num_comments'] >= min_comments]


def compose(*functions):
    """Compose multiple functions into a single function."""
    return reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)


# Main API function
def get_reddit_data(subreddit_name: str, category: str = 'hot', 
                   post_limit: int = 25, comment_limit: int = 10,
                   min_score: int = 0, min_comments: int = 0) -> Dict[str, Any]:
    """
    Main function to get Reddit data with filtering options.
    
    Args:
        subreddit_name: Name of the subreddit
        category: Category of posts ('hot', 'rising', 'new', 'top')
        post_limit: Number of posts to fetch
        comment_limit: Number of top comments per post
        min_score: Minimum score for posts
        min_comments: Minimum comment count for posts
    
    Returns:
        Dictionary containing metadata and posts data
    """
    reddit = create_reddit_instance()
    
    # Fetch raw data
    posts_data = fetch_subreddit_posts(
        reddit, subreddit_name, category, post_limit, comment_limit
    )
    
    # Apply filters using functional composition
    filter_pipeline = compose(
        filter_posts_by_comment_count(min_comments),
        filter_posts_by_score(min_score)
    )
    
    filtered_posts = filter_pipeline(posts_data)
    
    return {
        'metadata': {
            'subreddit': subreddit_name,
            'category': category,
            'requested_posts': post_limit,
            'fetched_posts': len(posts_data),
            'filtered_posts': len(filtered_posts),
            'comment_limit_per_post': comment_limit,
            'timestamp': datetime.now().isoformat(),
            'filters': {
                'min_score': min_score,
                'min_comments': min_comments
            }
        },
        'posts': filtered_posts
    }


# Example usage and testing functions
def save_data_to_json(data: Dict[str, Any], filename: str) -> None:
    """Save data to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    """Example usage of the Reddit API functions."""
    
    try:
        # Example: Get hot posts from r/python
        data = get_reddit_data(
            subreddit_name='python',
            category='hot',
            post_limit=10,
            comment_limit=5,
            min_score=10,
            min_comments=2
        )
        
        print(f"Fetched {len(data['posts'])} posts from r/{data['metadata']['subreddit']}")
        
        # Save to file
        save_data_to_json(data, 'reddit_data.json')
        
        # Print first post as example
        if data['posts']:
            first_post = data['posts'][0]
            print(f"\nFirst post: {first_post['title']}")
            print(f"Score: {first_post['upvotes']}")
            print(f"Comments: {first_post['num_comments']}")
            print(f"Top comment: {first_post['top_comments'][0]['body'][:100]}..." 
                  if first_post['top_comments'] else "No comments")
    
    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()