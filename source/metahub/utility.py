from urllib.parse import urlparse, quote, urlunparse

def sanitize_url(url: str) -> str:
    """
    Vérifie et encode une URL pour la rendre valide.
    
    Args:
        url (str): L'URL à vérifier et encoder.
        
    Returns:
        str: L'URL corrigée et encodée.
    """
    try:
        # Analyse l'URL en ses composants
        parsed_url = urlparse(url)
        
        # Si le schéma ou le netloc est manquant, c'est une URL invalide
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"L'URL {url} est invalide.")
        
        # Encode uniquement le chemin et les paramètres problématiques
        encoded_path = quote(parsed_url.path, safe="/")
        encoded_query = quote(parsed_url.query, safe="=&")
        
        # Reconstruit l'URL
        sanitized_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            encoded_path,
            parsed_url.params,
            encoded_query,
            parsed_url.fragment
        ))
        
        return sanitized_url
    except Exception as e:
        raise ValueError(f"Erreur lors de la validation de l'URL {url}: {e}")


# =============================================================================
#  Base Use Test
# =============================================================================

if __name__ == "__main__":
    invalid_url = 'https://www.wordplays.com/crossword-solver/"Baudolino"-author'
    fixed_url = sanitize_url(invalid_url)
    print(fixed_url)
