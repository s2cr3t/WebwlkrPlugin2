from baidusearch import search  # Import baidusearch library
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

import logging
import re
import os
import shutil
import yaml

from . import mux, webpilot

backend_mapping = {
    "webpilot": webpilot.process,
    "native": mux.process,
}

process: callable = None
config: dict = None

# Register plugin
@register(name="Webwlkr", description="基于GPT的函数调用能力，为QChatGPT提供联网功能", version="0.1.4", author="RockChinQ")
class WebwlkrPlugin(Plugin):

    # Triggered when plugin is loaded
    def __init__(self, plugin_host: PluginHost):
        global process, config
        # Check if webwlkr.yaml exists
        if not os.path.exists("webwlkr.yaml"):
            shutil.copyfile("plugins/WebwlkrPlugin/config-template.yaml", "webwlkr.yaml")
        
        # Read configuration file
        with open("webwlkr.yaml", "r", encoding="utf-8") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        process = backend_mapping[config["backend"]]

    @func("search_the_web")
    def _(search_string: str, brief_len: int = None):
        """Call this function to search about the question before you answer any questions.but DO NOT use this function to visite website
        - Do not search through google.com at any time.
        - Summary the plain content result by yourself

        Args:
            search_string(str): things to search
            brief_len(int): max length of the plain text content, recommend 1024-4096, prefer 4096. If not provided, default value from config will be used.

        Returns:
            str: plain text content of the web page or error message(starts with 'error:')
        """
        try:
            if brief_len is None:
                brief_len = config.get("brief_len", 4096)

            if search_string.startswith(("http://", "https://")):
                return process(search_string, brief_len)
            else:
                search_results = search(search_string)
                return process_search_results(search_results, brief_len)
        except Exception as e:
            logging.error("[Webwlkr] error visit web: {}".format(e))
            return "error visit web:{}".format(e)

    # Triggered when plugin is uninstalled
    def __del__(self):
        pass

def process_search_results(search_results: list, brief_len: int):
    """Process search results and return text content"""
    brief_text = ""
    for result in search_results:
        title = result['title']
        abstract = result['abstract']
        url = result['url']
        # 将标题和摘要添加到brief_text中
        brief_text += f"Title: {title}\nSnippet: {abstract}\nurl:{url}\n\n "
    

    return brief_text.strip() if brief_text else "No relevant results found."
