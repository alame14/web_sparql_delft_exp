import time
from urllib.parse import urlparse, urlunparse, quote
from rdflib import URIRef


class URLConverter:
    """
    Classe pour convertir des URLs en URIRef, avec gestion optionnelle d'un cache,
    mesure des temps de traitement et calcul du temps total de conversion.

    Attributes:
        cache_enabled (bool): Indique si le cache est activé.
        conversion_cache (list): Liste des conversions réalisées.
        total_conversion_time (float): Temps total passé dans les conversions, en secondes.
    """

    def __init__(self, cache_enabled: bool = True):
        """
        Initialise le convertisseur avec une option pour activer ou désactiver le cache.

        Args:
            cache_enabled (bool): Si True, garde une trace des conversions dans un cache.
        """
        self.cache_enabled = cache_enabled
        self.conversion_cache = []
        self.total_conversion_time = 0.0  # Initialisation du compteur de temps total

    def _encode_url(self, url: str) -> str:
        """
        Valide et encode une URL en une chaîne compatible URI.

        Args:
            url (str): L'URL à convertir.

        Returns:
            str: L'URI valide obtenu après encodage.

        Raises:
            ValueError: Si l'URL est invalide ou si une erreur survient.
        """
        if not isinstance(url, str) or not url.strip():
            raise ValueError("L'argument 'url' doit être une chaîne non vide.")

        try:
            parsed_url = urlparse(url)
            
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"L'URL '{url}' est invalide. Schéma ou netloc manquant.")
            
            # Encodage des caractères problématiques dans chaque composant de l'URL
            encoded_path = quote(parsed_url.path, safe="/")  # Encode le chemin
            encoded_query = quote(parsed_url.query, safe="=&")  # Encode la query string
            encoded_params = quote(parsed_url.params, safe="")  # Encode les paramètres

            # Reconstruction de l'URL encodée
            sanitized_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                encoded_path,
                encoded_params,
                encoded_query,
                parsed_url.fragment
            ))

            return sanitized_url

        except Exception as e:
            raise ValueError(f"Erreur inattendue lors du traitement de l'URL '{url}': {e}")

    def url_to_uriref(self, url: str) -> URIRef:
        """
        Convertit une URL en URIRef, mesure le temps de traitement, et ajoute au cache si activé.

        Args:
            url (str): L'URL à convertir.

        Returns:
            URIRef: L'URI obtenu après conversion.
        """
        start_time = time.time()  # Mesure du temps de début
        sanitized_url = self._encode_url(url)  # Encode l'URL pour qu'elle soit valide
        uri_ref = URIRef(sanitized_url)  # Création du URIRef
        end_time = time.time()  # Mesure du temps de fin

        elapsed_time = end_time - start_time
        self.total_conversion_time += elapsed_time  # Mise à jour du temps total

        if self.cache_enabled:
            self.conversion_cache.append({
                "original_url": url,
                "converted_uri": str(uri_ref),
                "processing_time": elapsed_time
            })

        return uri_ref

    def get_cache(self) -> list:
        """
        Retourne le contenu du cache.

        Returns:
            list: Le cache des conversions effectuées.
        """
        return self.conversion_cache

    def get_total_conversion_time(self) -> float:
        """
        Retourne le temps total de conversion.

        Returns:
            float: Temps total de conversion, en secondes.
        """
        return self.total_conversion_time


# =============================================================================
#  Basic Use Test
# =============================================================================

if __name__ == '__main__':
    # Test avec le cache activé
    print("=== Test avec cache activé ===")
    converter_with_cache = URLConverter(cache_enabled=True)

    urls = [
        "https://www.purchasedirect.com/search/{search_term_string}",
        "https://example.com/path/to/resource?query=value&other=value2",
        "http://invalid-url",
        "ftp://fileserver.com/download/file.zip",
        "https://example.com/{dynamic}/path?name=test#section",
        "https://en.wikipedia.org/wiki/Eric_(novel)"
    ]
    
    for url in urls:
        try:
            converter_with_cache.url_to_uriref(url)
        except ValueError as e:
            print(e)
    
    # Affichage du cache des conversions
    print("=== Cache des conversions avec cache activé ===")
    for entry in converter_with_cache.get_cache():
        print(entry)
    
    for i in range(1000):
        for url in urls:
            converter_with_cache.url_to_uriref(url)

    total_time_with_cache = converter_with_cache.get_total_conversion_time()
    print(f"Temps total de conversion avec cache : {total_time_with_cache:.5f} secondes\n")

    # Test sans le cache
    print("=== Test sans cache activé ===")
    converter_without_cache = URLConverter(cache_enabled=False)

    for url in urls:
        try:
            converter_without_cache.url_to_uriref(url)
        except ValueError as e:
            print(e)
                
    for i in range(1000):
        for url in urls:
            converter_without_cache.url_to_uriref(url)

    total_time_without_cache = converter_without_cache.get_total_conversion_time()
    print(f"Temps total de conversion sans cache : {total_time_without_cache:.5f} secondes\n")

    # Affichage du cache des conversions
    print("=== Cache des conversions avec cache activé ===")
    # for entry in converter_with_cache.get_cache():
    #     print(entry)
