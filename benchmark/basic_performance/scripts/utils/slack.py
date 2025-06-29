#
# MIT License
#
# Copyright (c) 2025 Jangseon Park
# Affiliation: University of California San Diego CSE
# Email: jap036@ucsd.edu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import sys

import requests
from dotenv import load_dotenv

# By default, do not send Slack message
# make the self.env file in the same directory as the script
# with the following content:
# Slack=1
# SlackURL=your_slack_webhook_url
# HOSTNAME=your_host_name
from loguru import logger

from heimdall.utils.path import get_workspace_path

path = get_workspace_path() / "benchmark" / "basic_performance" / "env_files" / "self.env"
load_dotenv(
    dotenv_path=path,
)
SLACK_ENABLED = int(os.getenv("Slack", 0))
SLACK_URL = os.getenv("SlackURL")
HOST_NAME = os.getenv("HOSTNAME", "unknown_host")


def slack_notice(slack_url, message):
    if not SLACK_ENABLED:
        logger.info(f"Skip sending Slack message: [{message}]")
        return

    if not slack_url or not message:
        logger.error("slack_notice requires both slack_url and message.")
        sys.exit(1)

    logger.info(f"Sending Slack message -- {message}")
    try:
        response = requests.post(
            slack_url,
            json={"text": message},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to send Slack message: {e}")


def slack_notice_msg(message):
    slack_notice(SLACK_URL, f"`[{HOST_NAME}]` {message}")


def slack_notice_beg(message):
    slack_notice_msg(f"`[Start   ]` {message}")


def slack_notice_progress(iteration, total):
    if iteration is None or total is None:
        logger.error("slack_notice_progress requires iteration and total.")
        sys.exit(1)

    progress = round(100 * iteration / total, 2)
    progress_string = f"`{progress:8.2f}%` `[ {iteration:3} / {total:<3} ]`"
    slack_notice_msg(f"`[Progress]` {progress_string}")


def slack_notice_end(message):
    slack_notice_msg(f"`[End     ]` `{message}`")
