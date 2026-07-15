from nltk.tokenize import sent_tokenize
import json

def sentence_chunk(text, max_words=50):
    """
    renvoie une liste de phrase qui font le max word
    """
    sentences = sent_tokenize(text)
    chunks, buffer, length = [], [], 0

    for sent in sentences:
        count = len(sent.split())
        if length + count > max_words and buffer:
            chunks.append(" ".join(buffer))
            buffer, length = [], 0
        buffer.append(sent)
        length += count

    if buffer:
        chunks.append(" ".join(buffer))
    return chunks
# text = "Les Parties s’engagent à ce que les informations présentes au sein de ladite convention : - soient protégées et gardées strictement confidentielles, et soient traitées avec le même degré de précaution et de protection qu’elles accordent à leurs propres La Quincaillerie Solidaire - Les Bricos du Coeur Association loi 1901 135 rue Sadi Carnot - 59790 Ronchin ✉ contact@laquincaillerie.org - 4 - informations confidentielles ; - ne soient divulguées qu’à leurs dirigeants ainsi qu’aux seuls membres de leur personnel ayant à les connaître et ne soient utilisées qu’à des fins et des circonstances liées à l’exécution de la convention ; - ne soient ni copiées, ni reproduites, ni dupliquées totalement ou partiellement sans l’autorisation expresse et préalable de l’autre Partie. Nonobstant la fin de la présente convention pour quelque cause que ce soit, les stipulations relatives à l’obligation de confidentialité survivront à la cessation de la présente convention et ce pour une durée d’au moins deux (2) ans après la cessation de la convention."

with open("./data/page_de_base.json","r",encoding="utf-8") as f:
    data = json.load(f)
    for paragraphe in data["paragraphes"]:
        chunks = sentence_chunk(paragraphe["texte"])
        print(f"titre: {paragraphe['titre']}")
        for chunk in chunks:
            print(f"  chunk ({len(chunk.split())} mots): {chunk[:100]}")
        print("---")
