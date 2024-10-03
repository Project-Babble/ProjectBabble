import os
import json


class LocaleStringManager:
    _instance = None
    _languages = []
    _strings = {}
    _current_language = None

    def __new__(self, locale_directory, language):
        if self._instance is None:
            self._instance = super(LocaleStringManager, self).__new__(self)
            self._instance._initialize(locale_directory, language)
        return self._instance

    def _initialize(self, locale_directory, language):
        self._instance._languages = [
            lang
            for lang in os.listdir(locale_directory)
            if os.path.isdir(os.path.join(locale_directory, lang))
        ]
        self._instance._current_language = language

        for lang in self._languages:
            self._instance._strings[lang] = {}
            lang_dir = os.path.join(locale_directory, lang)
            for file in os.listdir(lang_dir):
                if file.endswith(".json"):
                    with open(os.path.join(lang_dir, file), "r", encoding="utf-8") as f:
                        file_strings = json.load(f)
                        file_name = os.path.splitext(file)[0]
                        for key, value in file_strings.items():
                            self._instance._strings[lang][f"{file_name}.{key}"] = value

        self._load_language(language)

    def _load_language(self, language):
        self._instance._current_language = language
        if self._instance._current_language not in self._instance._languages:
            raise ValueError(
                f"Language '{self._instance._current_language}' from settings is not supported"
            )

    @classmethod
    def get_languages(self):
        return self._instance._languages

    @classmethod
    def get_string(self, pattern):
        pattern = f"locale.{pattern}"
        if pattern not in self._instance._strings[self._instance._current_language]:
            raise KeyError(
                f"String pattern '{pattern}' not found for current language '{self._instance._current_language}'"
            )
        return self._instance._strings[self._instance._current_language][pattern]

    @classmethod
    def update_language(self, config):
        self._instance._load_language(config)


#
# # If settings are updated:
# LocaleStringManager.update_language(main_config.settings)
