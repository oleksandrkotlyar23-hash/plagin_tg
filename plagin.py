import urllib.request
import urllib.parse
import json
import re
from base_plugin import BasePlugin, MethodHook
from hook_utils import find_class
from android_utils import log

id = "alex_fasttranslator"
name = "Fast Translator"
description = "Translates messages starting with .tr <lang> <text>"
author = "@flyffyx"
version = "1.0.0"
icon = ""

class SendMessageHook(MethodHook):
    def init(self, plugin):
        self.plugin = plugin

    def before_hooked_method(self, param):
        try:
            # Припускаємо, що перший аргумент (args[0]) - це текст повідомлення (CharSequence/String)
            # Тобі може знадобитися змінити індекс залежно від точної сигнатури методу в ExteraGram
            original_text = str(param.args[0])
            
            match = re.match(r'^\.tr\s+([a-zA-Z-]{2,5})\s+(.+)', original_text, re.IGNORECASE | re.DOTALL)
            if not match:
                return

            input_lang = match.group(1).lower()
            text_to_translate = match.group(2)

            # Обробка ua -> uk
            target_lang = "uk" if input_lang == "ua" else input_lang

            # Робимо запит до Google Translate API
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text_to_translate)}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Збираємо перекладений текст докупи
                translated_text = "".join([part[0] for part in data[0]])
                
                # Підміняємо аргумент: тепер Telegram відправить перекладений текст
                # Залежно від API, можливо доведеться конвертувати рядок у Java String
                param.args[0] = translated_text
                
                log(f"FastTranslator: успішно перекладено на {target_lang}")

        except Exception as e:
            log(f"FastTranslator error: {e}")

class FastTranslatorPlugin(BasePlugin):
    def on_plugin_load(self):
        try:
            # Шукаємо клас, який відповідає за відправку повідомлень
            # Зазвичай це org.telegram.messenger.SendMessagesHelper
            SendMessagesHelperClass = find_class("org.telegram.messenger.SendMessagesHelper")
            
            if not SendMessagesHelperClass:
                log("FastTranslator: SendMessagesHelper class not found")
                return
                
            # Хукаємо метод sendMessage (назва може відрізнятися через обфускацію або версію)
            # Тут треба знати точну назву методу, який приймає текст повідомлення
            self.hook_all_methods(SendMessagesHelperClass, "sendMessage", SendMessageHook(self))
            log("FastTranslator: hooked sendMessage successfully")
            
        except Exception as e:
            log(f"FastTranslator: failed to hook: {e}")

    def on_plugin_unload(self):
        log("FastTranslator: unloaded")
