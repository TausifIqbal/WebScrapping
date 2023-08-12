import os
import sys
import requests
import subprocess
import time
import json


class SlackApi:
    """ Slack Api interface for simple user notifications - event driven/ephemeral """

    def __init__(self):
        self.get_slack_bot_token()
        self.get_slack_user_token()
        self.get_slack_hook()

    def get_slack_bot_token(self):
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")

    def get_slack_user_token(self):
        self.slack_user_token = os.environ.get("SLACK_USER_TOKEN")

    def get_slack_hook(self):
        self.slack_webhook = os.environ.get("SLACK_WEBHOOK")

    def email_to_slack_id(self, email_address):
        data = {"email": email_address, "token": self.slack_user_token}
        response = requests.post(
            url="https://slack.com/api/users.lookupByEmail", data=data
        )
        if response.status_code == 200:
            json_data = response.json()
            if "user" in json_data:
                return json_data["user"]["id"]
        return None

    def post_msg(self, github_user_email, message):
        """ send msg to user """
        slack_user_id = None
        slack_user_id = self.email_to_slack_id(github_user_email)
        if not slack_user_id:
            return False

        data = {
            "token": self.slack_bot_token,
            "channel": slack_user_id,
            "as_user": True,
            "text": message,
        }
        requests.post(url="https://slack.com/api/chat.postMessage", data=data)
        return True


class GithubApiHack:
    """ cheesily run the gh tool instead of using the Github SDK """

    def __init__(self):
        pass

    def resolve_username_to_email(self, github_user):
        proc_data = subprocess.check_output(["gh", "api", "/users/" + github_user])
        return json.loads(proc_data)["email"]


def build_msg(gh_data={}):
    msg_str = []
    msg_str.append(":typingcat:")
    msg_str.append("<" + github_data["pr_uri"] + "|PR #" + github_data["pr"] + ">")
    msg_str.append("in repo " + gh_data["repo_name"])
    msg_str.append("needs your review.")
    return " ".join(msg_str)


if __name__ == "__main__":
    slack_api = SlackApi()
    github_api = GithubApiHack()
    github_data = {
        "reviewers": os.environ.get("PR_REVIEWERS"),
        "pr": os.environ.get("PR"),
        "pr_uri": os.environ.get("PR_LINK"),
        "github_token": os.environ.get("GITHUB_TOKEN"),
        "repo_name": os.environ.get("REPOSITORY_NAME"),
        "repo_branch": os.environ.get("REPOSITORY_BRANCH"),
    }
    slack_msg = build_msg(github_data)
    for github_user in github_data["reviewers"].split(","):
        reviewer_email = github_api.resolve_username_to_email(github_user)
        try:
            slack_api.post_msg(reviewer_email, slack_msg)
        except:
            sys.exit(1)
        time.sleep(1)
