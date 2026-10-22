# src/priv_audit/rag_retriever.py
"""
Motor de recuperacion de chunks relevantes.
Usa TF-IDF (scikit-learn) si esta disponible.
Si no, cae en un retriever BM25-like implementado con solo stdlib.
"""
import math
import re
from collections import Counter

# --- Intentar importar scikit-learn ---
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    _SKLEARN = True
except ImportError:
    _SKLEARN = False


# ------------------------------------------------------------------ #
#  Fallback: BM25 simplificado (solo stdlib)
# ------------------------------------------------------------------ #
def _tokenizar(texto: str) -> list[str]:
    return re.findall(r'\w+', texto.lower())


class _BM25:
    """Implementacion minimalista de BM25 sin dependencias externas."""
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_tok = [_tokenizar(doc) for doc in corpus]
        self.N = len(corpus)
        self.avgdl = sum(len(d) for d in self.corpus_tok) / max(self.N, 1)

        # IDF
        df: dict[str, int] = Counter()
        for doc in self.corpus_tok:
            for term in set(doc):
                df[term] += 1
        self.idf = {
            term: math.log((self.N - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

    def score(self, consulta_tok: list[str], doc_tok: list[str]) -> float:
        dl = len(doc_tok)
        tf_doc = Counter(doc_tok)
        score = 0.0
        for term in consulta_tok:
            if term not in tf_doc:
                continue
            idf = self.idf.get(term, 0.0)
            tf = tf_doc[term]
            score += idf * (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            )
        return score

    def recuperar(self, consulta: str, top_k: int) -> list[tuple[int, float]]:
        tok = _tokenizar(consulta)
        scores = [(i, self.score(tok, doc)) for i, doc in enumerate(self.corpus_tok)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(i, s) for i, s in scores[:top_k] if s > 0]


# ------------------------------------------------------------------ #
#  Clase publica: Retriever
# ------------------------------------------------------------------ #
class Retriever:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks
        self.textos = [c["texto"] for c in chunks]

        if _SKLEARN and self.textos and any(re.search(r'\w{2,}', t) for t in self.textos):
            self._modo = "TF-IDF (scikit-learn)"
            self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
            self._matriz = self._vectorizer.fit_transform(self.textos)
        else:
            self._modo = "BM25 (stdlib)"
            self._bm25 = _BM25(self.textos)

        print(f"[Retriever] Indice construido con {self._modo}: {len(self.textos)} vectores.")

    def recuperar(self, consulta: str, top_k: int = 5) -> list[dict]:
        """Devuelve los top_k chunks mas relevantes para la consulta."""
        resultados = []

        if not self.textos:
            return []

        if hasattr(self, "_vectorizer"):
            vec = self._vectorizer.transform([consulta])
            sims = cosine_similarity(vec, self._matriz).flatten()
            indices = np.argsort(sims)[::-1][:top_k]
            for i in indices:
                if sims[i] > 0.01:
                    resultados.append({
                        "texto":  self.chunks[i]["texto"],
                        "fuente": self.chunks[i]["fuente"],
                        "pagina": self.chunks[i].get("pagina"),
                        "score":  float(sims[i]),
                    })
        else:
            for i, score in self._bm25.recuperar(consulta, top_k):
                resultados.append({
                    "texto":  self.chunks[i]["texto"],
                    "fuente": self.chunks[i]["fuente"],
                    "pagina": self.chunks[i].get("pagina"),
                    "score":  score,
                })

        return resultados
