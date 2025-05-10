import opencc
import unicodedata

converter = opencc.OpenCC('s2tw.json')
def convert_simplified_to_traditional(text: str) -> str:
    """
    Convert simplified Chinese to traditional Chinese.
    :param text: The text to convert.
    :return: The converted text.
    """
    if text is None:
        return text
    
    text = text.strip()
    text = ' '.join([unicodedata.normalize('NFKC', t) for t in text.split(' ')])

    return converter.convert(text)