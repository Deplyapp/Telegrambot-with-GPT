import datetime
import re
from urllib.parse import urlparse
import aiohttp
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from readability import Document
from itertools import islice

class WebSearch:
    def __init__(self, lang):
        self.lang = lang
    async def ddg_search(self, prompt, template_message, news=False):
        with DDGS() as ddgs:
            if re.search(r"(https?://\S+)", prompt) or len(prompt) > 1000:
                return
            if prompt is not None:
                results = ddgs.text(
                    keywords=prompt, region="wt-wt", safesearch="off", backend="api"
                ) if not news else ddgs.text(keywords=prompt, region="wt-wt", safesearch="off")
                results_list = [result for result in islice(results, 3)]
                blob = f"{template_message.format(prompt)} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n\n"
                template = '[{index}] "{snippet}"\nURL: {link}\n'
                for i, result in enumerate(results_list):
                    blob += template.format(
                        index=i, snippet=result["body"], link=result["href"]
                    )
                return blob
            else:
                return "No search query is needed for a response"
    async def search_ddg(self, prompt):
        return await self.ddg_search(prompt, "Search results for '{}'")
    async def news_ddg(self, prompt="latest world news"):
        return await self.ddg_search(prompt, "News results for '{}'")
    async def extract_text_from_website(self, url):
        parsed_url = urlparse(url)
        if parsed_url.scheme == "" or parsed_url.netloc == "":
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    soup = BeautifulSoup(content, "html.parser")
                    extracted_text = soup.get_text()
                    return extracted_text.strip() or None
        except:
            return None
    async def generate_keyboard(self, key):
        markup = ReplyKeyboardMarkup(row_width=5)
        if key == "lang":
            markup.add(
                *(
                    KeyboardButton(f"{self.lang['languages'][lang_code]}({lang_code})")
                    for lang_code in self.lang["available_lang"]
                )
            )
        return markup
    async def generate_query(self, response, plugins_dict):
        opening_bracket = response.find("[")
        closing_bracket = response.find("]")
        if opening_bracket != -1 and closing_bracket != -1:
            plugin_text = response[opening_bracket + 1 : closing_bracket]
            plugin_parts = plugin_text.split()
            plugin_name = plugin_parts[0]
            query = " ".join(plugin_parts[1:])
            if plugin_name is not None and query is not None:
                if plugin_name.lower() == "wolframalpha":
                    return (
                        "wolframalpha plugin is not yet implemented so provide a response yourself",
                        plugin_name,
                    )
                elif plugin_name.lower() == "duckduckgosearch":
                    return await self.search_ddg(query), plugin_name
                elif plugin_name.lower() == "duckduckgonews":
                    return await self.news_ddg(query), plugin_name
                else:
                    return None, None
            else:
                return None, None
        else:
            return None, None