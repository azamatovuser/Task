import pyjokes

# Шутки на определенном языке
joke_ru = pyjokes.get_joke(language="ru", category="all")
print(joke_ru)