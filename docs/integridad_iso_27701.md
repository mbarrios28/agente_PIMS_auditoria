# ISO/IEC 27701:2025: cobertura del repositorio

Comprobado el 2026-11-05. La segunda edición de octubre de 2025 es un sistema
de gestión independiente, según la [ficha oficial de ISO](https://www.iso.org/standard/27701).
La ficha declara 64 páginas de contenido. La copia aportada tiene 72 páginas PDF:
seis de portada y preliminares, 64 de cuerpo, una página en blanco y contraportada.
El original y su derivado OCR ya están versionados en Git.

| Contenido | Páginas PDF |
|---|---|
| Cláusulas 1–11 | 7–20 |
| Anexo A, normativo: controles | 21–26 |
| Anexo B, normativo: orientación de implementación | 27–56 |
| Anexo C, informativo | 57–58 |
| Anexo D, informativo | 59–61 |
| Anexo E, informativo | 62–63 |
| Anexo F, informativo | 64–69 |
| Bibliografía, página impresa 64 | 70 |

Se comprobaron los hashes SHA-256 contra `ISOS/fuentes.json`, el número de páginas
de ambos PDF, la edición, texto extraíble en todo el cuerpo y los encabezados de
los anexos. Se revisaron visualmente el índice y la página PDF 71: está en blanco,
no corresponde a contenido perdido. El OCR confunde algunos caracteres y números
(por ejemplo, el pie de la página impresa 57); no se debe interpretar como transcripción exacta.

Repetir la comprobación con `python scripts/verificar_iso_27701.py`.
Es una comprobación de integridad local y cobertura estructural, no de autenticidad
editorial ni una revisión palabra por palabra. Las citas y tablas requieren contraste
con la imagen original. No se reemplazaron ni descargaron copias de la norma.

El agente de riesgos recupera únicamente `ISO-IEC-27701-2025-OCR.pdf` como fuente
normativa. Conserva ID y página en las citas. GESTITEL proporciona activos, hechos,
matriz y controles registrados como contexto operativo; su fórmula P×I no es una
fórmula prescrita por ISO. Las correspondencias informativas y referencias a otras
normas dentro del PDF no amplían la base normativa del agente.
