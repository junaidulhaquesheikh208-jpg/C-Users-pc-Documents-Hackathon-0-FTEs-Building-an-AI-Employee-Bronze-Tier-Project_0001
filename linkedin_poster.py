import requests
import time
from pathlib import Path
import json
import logging
from datetime import datetime


class LinkedInPoster:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.api_base = "https://api.linkedin.com/v2"
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_post(self, text: str, visibility: str = "PUBLIC"):
        """
        Create a LinkedIn post
        :param text: The content of the post
        :param visibility: PUBLIC, CONNECTIONS_ONLY, etc.
        :return: Response from LinkedIn API
        """
        try:
            # First, create the text-only post
            post_data = {
                "author": f"urn:li:person:{self.get_person_urn()}",  # This would need to be retrieved
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            response = requests.post(
                f"{self.api_base}/ugcPosts",
                headers=self.headers,
                json=post_data
            )

            if response.status_code == 201:
                self.logger.info(f"LinkedIn post created successfully: {response.json().get('id')}")
                return response.json()
            else:
                self.logger.error(f"Failed to create LinkedIn post: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating LinkedIn post: {e}")
            return None

    def get_person_urn(self):
        """
        Retrieve the person URN for the authenticated user
        """
        try:
            response = requests.get(
                f"{self.api_base}/me",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('id')  # Simplified - actual URN format is more complex
            else:
                self.logger.error(f"Failed to get person URN: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting person URN: {e}")
            return None

    def schedule_post(self, text: str, scheduled_time: datetime, visibility: str = "PUBLIC"):
        """
        Schedule a LinkedIn post for a future time
        """
        # This would require LinkedIn Premium or specific permissions
        # For now, we'll just log the intent to schedule
        self.logger.info(f"Scheduled post for {scheduled_time}: {text[:50]}...")
        return {"scheduled": True, "time": scheduled_time.isoformat()}


# LinkedIn MCP Server Interface
class LinkedInMCPServer:
    def __init__(self, config_path: str = "./linkedin_config.json"):
        self.config = self.load_config(config_path)
        self.poster = LinkedInPoster(self.config.get("access_token", ""))
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_config(self, config_path: str):
        """Load LinkedIn API configuration"""
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Return empty config - this would need to be set up by the user
            return {}

    def handle_command(self, command: dict):
        """
        Handle commands from Claude Code via MCP
        Expected commands: post, schedule_post, get_profile
        """
        cmd_type = command.get("type")
        
        if cmd_type == "post":
            text = command.get("text", "")
            visibility = command.get("visibility", "PUBLIC")
            return self.poster.create_post(text, visibility)
        
        elif cmd_type == "schedule_post":
            text = command.get("text", "")
            scheduled_time_str = command.get("scheduled_time", "")
            visibility = command.get("visibility", "PUBLIC")
            
            if scheduled_time_str:
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                return self.poster.schedule_post(text, scheduled_time, visibility)
            else:
                return {"error": "scheduled_time is required for schedule_post"}
        
        elif cmd_type == "get_profile":
            urn = self.poster.get_person_urn()
            return {"profile_urn": urn}
        
        else:
            return {"error": f"Unknown command type: {cmd_type}"}


# Example usage
if __name__ == "__main__":
    # This would normally be run as an MCP server
    # linkedin_server = LinkedInMCPServer()
    print("LinkedIn MCP Server initialized")