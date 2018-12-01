norwegian_stop_words = {
    'og', 'i', 'jeg', 'det', 'at', 'en', 'et', 'den', 'til', 'er', 'som',
    'på', 'de', 'med', 'han', 'av', 'ikke', 'ikkje', 'der', 'så', 'var', 'meg',
    'seg', 'men', 'ett', 'har', 'om', 'vi', 'min', 'mitt', 'ha', 'hadde', 'hun',
    'nå', 'over', 'da', 'ved', 'fra', 'du', 'ut', 'sin', 'dem', 'oss', 'opp',
    'man', 'kan', 'hans', 'hvor', 'eller', 'hva', 'skal', 'selv', 'sjøl', 'her', 'alle',
    'vil', 'bli', 'ble', 'blei', 'blitt', 'kunne', 'inn', 'når', 'være', 'kom', 'noen',
    'noe', 'ville', 'dere', 'som', 'deres', 'kun', 'ja', 'etter', 'ned', 'skulle', 'denne',
    'for', 'deg', 'si', 'sine', 'sitt', 'mot', 'å', 'meget', 'hvorfor', 'dette', 'disse',
    'uten', 'hvordan', 'ingen', 'din', 'ditt', 'blir', 'samme', 'hvilken', 'hvilke', 'sånn', 'inni',
    'mellom', 'vår', 'hver', 'hvem', 'vors', 'hvis', 'både', 'bare', 'enn', 'fordi', 'før',
    'mange', 'også', 'slik', 'vært', 'være', 'båe', 'begge', 'siden', 'dykk', 'dykkar', 'dei',
    'deira', 'deires', 'deim', 'di', 'då', 'eg', 'ein', 'eit', 'eitt', 'elles', 'honom',
    'hjå', 'ho', 'hoe', 'henne', 'hennar', 'hennes', 'hoss', 'hossen', 'ikkje', 'ingi', 'inkje',
    'korleis', 'korso', 'kva', 'kvar', 'kvarhelst', 'kven', 'kvi', 'kvifor', 'me', 'medan', 'mi',
    'mine', 'mykje', 'no', 'nokon', 'noka', 'nokor', 'noko', 'nokre', 'si', 'sia', 'sidan',
    'so', 'somt', 'somme', 'um', 'upp', 'vere', 'vore', 'verte', 'vort', 'varte', 'vart',
    'alle', 'andre', 'arbeid', 'at', 'av', 'bare', 'begge', 'ble', 'blei', 'bli', 'blir',
    'blitt', 'bort', 'bra', 'bruke', 'både', 'båe', 'da', 'de', 'deg', 'dei', 'deim',
    'deira', 'deires', 'dem', 'den', 'denne', 'der', 'dere', 'deres', 'det', 'dette', 'di',
    'din', 'disse', 'ditt', 'du', 'dykk', 'dykkar', 'då', 'eg', 'ein', 'eit', 'eitt',
    'eller', 'elles', 'en', 'ene', 'eneste', 'enhver', 'enn', 'er', 'et', 'ett', 'etter',
    'folk', 'for', 'fordi', 'forsûke', 'fra', 'få', 'før', 'fûr', 'fûrst', 'gjorde', 'gjûre',
    'god', 'gå', 'ha', 'hadde', 'han', 'hans', 'har', 'hennar', 'henne', 'hennes', 'her',
    'hjå', 'ho', 'hoe', 'honom', 'hoss', 'hossen', 'hun', 'hva', 'hvem', 'hver', 'hvilke',
    'hvilken', 'hvis', 'hvor', 'hvordan', 'hvorfor', 'i', 'ikke', 'ikkje', 'ingen', 'ingi', 'inkje',
    'inn', 'innen', 'inni', 'ja', 'jeg', 'kan', 'kom', 'korleis', 'korso', 'kun', 'kunne',
    'kva', 'kvar', 'kvarhelst', 'kven', 'kvi', 'kvifor', 'lage', 'lang', 'lik', 'like', 'makt',
    'man', 'mange', 'me', 'med', 'medan', 'meg', 'meget', 'mellom', 'men', 'mens', 'mer',
    'mest', 'mi', 'min', 'mine', 'mitt', 'mot', 'mye', 'mykje', 'må', 'måte', 'navn',
    'ned', 'nei', 'no', 'noe', 'noen', 'noka', 'noko', 'nokon', 'nokor', 'nokre', 'ny',
    'nå', 'når', 'og', 'også', 'om', 'opp', 'oss', 'over', 'part', 'punkt', 'på',
    'rett', 'riktig', 'samme', 'sant', 'seg', 'selv', 'si', 'sia', 'sidan', 'siden', 'sin',
    'sine', 'sist', 'sitt', 'sjøl', 'skal', 'skulle', 'slik', 'slutt', 'so', 'som', 'somme',
    'somt', 'start', 'stille', 'så', 'sånn', 'tid', 'til', 'tilbake', 'tilstand', 'um', 'under',
    'upp', 'ut', 'uten', 'var', 'vart', 'varte', 'ved', 'verdi', 'vere', 'verte', 'vi',
    'vil', 'ville', 'vite', 'vore', 'vors', 'vort', 'vår', 'være', 'vært', 'vöre', 'å'}


def remove_stopwords(tokens, stop_words):
    return (w for w in tokens if w not in stop_words)


def remove_stopwords_nb(tokens):
    return remove_stopwords(tokens, norwegian_stop_words)


def normalize(tokens):
    return (w.lower() for w in tokens if w.isalnum())
