import re
import unicodedata


def gerar_slug(texto: str) -> str:
    """Converte um texto livre em identificador de URL, sem acentos nem espaços."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    apenas_palavras = re.sub(r"[^a-zA-Z0-9]+", "-", sem_acento)
    return apenas_palavras.strip("-").lower()
