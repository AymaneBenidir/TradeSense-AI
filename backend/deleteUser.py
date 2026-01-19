from flask import Flask, request, jsonify
import os
import logging
from typing import Dict, Any, Optional, List
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

BASE44_API_KEY = os.environ.get('BASE44_API_KEY')
BASE44_API_URL = os.environ.get('BASE44_API_URL', 'https://api.base44.com')

class Base44Client:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    async def create_client_from_request(self, req) -> 'Base44Client':
        return self
    
    async def get_user_from_request(self, req) -> Optional[Dict[str, Any]]:
        """Get authenticated user from request"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/auth/me",
                headers={"Authorization": auth_header}
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    # Service role operations - using service key
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/entities/User/{user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/entities/User/{user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                return response.status == 200
    
    async def filter_challenges(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter challenges using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/entities/Challenge/filter",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=filters
            ) as response:
                if response.status == 200:
                    return await response.json()
                return []
    
    async def delete_challenge(self, challenge_id: str) -> bool:
        """Delete challenge using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/entities/Challenge/{challenge_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                return response.status == 200
    
    async def filter_trades(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter trades using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/entities/Trade/filter",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=filters
            ) as response:
                if response.status == 200:
                    return await response.json()
                return []
    
    async def delete_trade(self, trade_id: str) -> bool:
        """Delete trade using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/entities/Trade/{trade_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                return response.status == 200
    
    async def filter_community_posts(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter community posts using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/entities/CommunityPost/filter",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=filters
            ) as response:
                if response.status == 200:
                    return await response.json()
                return []
    
    async def delete_community_post(self, post_id: str) -> bool:
        """Delete community post using service role"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/entities/CommunityPost/{post_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                return response.status == 200

base44_client = Base44Client(
    api_key=BASE44_API_KEY,
    base_url=BASE44_API_URL
)

@app.route('/delete_user', methods=['POST'])
async def delete_user():
    try:
        # Get authenticated user from request
        user = await base44_client.get_user_from_request(request)
        
        # Only admins can delete users
        if not user or user.get('role') != 'admin':
            return jsonify({
                'error': 'Forbidden: Admin access required'
            }), 403

        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400

        user_id = data.get('userId')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400

        # Get user email before deletion using service role
        user_to_delete = await base44_client.get_user(user_id)
        if not user_to_delete:
            return jsonify({'error': 'User not found'}), 404
        
        user_email = user_to_delete.get('email')
        if not user_email:
            return jsonify({'error': 'User email not found'}), 404

        # Track deletion statistics
        deleted_challenges = 0
        deleted_trades = 0
        deleted_posts = 0

        # 1. Delete all challenges and their trades
        challenges = await base44_client.filter_challenges({'user_email': user_email})
        
        for challenge in challenges:
            # Delete all trades for this challenge
            trades = await base44_client.filter_trades({'challenge_id': challenge['id']})
            for trade in trades:
                success = await base44_client.delete_trade(trade['id'])
                if success:
                    deleted_trades += 1
            
            # Delete the challenge
            success = await base44_client.delete_challenge(challenge['id'])
            if success:
                deleted_challenges += 1

        # 2. Delete all community posts
        posts = await base44_client.filter_community_posts({'author_email': user_email})
        for post in posts:
            success = await base44_client.delete_community_post(post['id'])
            if success:
                deleted_posts += 1

        # 3. Finally, delete the user
        user_deleted = await base44_client.delete_user(user_id)
        if not user_deleted:
            return jsonify({
                'error': 'Failed to delete user',
                'success': False
            }), 500

        return jsonify({
            'success': True,
            'message': 'User and all related data deleted successfully',
            'deleted_data': {
                'challenges': deleted_challenges,
                'trades': deleted_trades,
                'community_posts': deleted_posts
            }
        })

    except json.JSONDecodeError:
        return jsonify({
            'error': 'Invalid JSON in request body'
        }), 400
    
    except KeyError as e:
        return jsonify({
            'error': f'Missing required field: {str(e)}'
        }), 400
    
    except Exception as error:
        logging.error(f'Error deleting user: {error}', exc_info=True)
        return jsonify({
            'error': str(error)
        }), 500

# Helper function for batch deletion
async def delete_user_data_concurrently(user_email: str, base44_client: Base44Client):
    """Delete user data concurrently for better performance"""
    import asyncio
    
    # Get all data first
    challenges_task = base44_client.filter_challenges({'user_email': user_email})
    posts_task = base44_client.filter_community_posts({'author_email': user_email})
    
    challenges, posts = await asyncio.gather(challenges_task, posts_task)
    
    # Delete trades for each challenge
    trade_deletion_tasks = []
    for challenge in challenges:
        trades = await base44_client.filter_trades({'challenge_id': challenge['id']})
        for trade in trades:
            trade_deletion_tasks.append(base44_client.delete_trade(trade['id']))
    
    # Wait for all trade deletions
    trade_results = await asyncio.gather(*trade_deletion_tasks, return_exceptions=True)
    deleted_trades = sum(1 for result in trade_results if result is True)
    
    # Delete challenges
    challenge_deletion_tasks = [base44_client.delete_challenge(c['id']) for c in challenges]
    challenge_results = await asyncio.gather(*challenge_deletion_tasks, return_exceptions=True)
    deleted_challenges = sum(1 for result in challenge_results if result is True)
    
    # Delete posts
    post_deletion_tasks = [base44_client.delete_community_post(p['id']) for p in posts]
    post_results = await asyncio.gather(*post_deletion_tasks, return_exceptions=True)
    deleted_posts = sum(1 for result in post_results if result is True)
    
    return deleted_challenges, deleted_trades, deleted_posts

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'user_deletion_service'
    }), 200

if __name__ == '__main__':
    if not BASE44_API_KEY:
        logging.warning("BASE44_API_KEY environment variable is not set")
    
    port = int(os.environ.get('PORT', 3009))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')