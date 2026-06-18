# Mundial Recap Pipeline

Pipeline gratuito para seguir el Mundial 2026: ingesta de datos abiertos, persistencia en SQLite, recaps automaticos, estado por seleccion y publicacion web con GitHub Actions.

## Resultados online

- [Ver reporte publicado](https://antonio-bidart.github.io/world-cup-recap-pipeline/)
- [Descargar partidos CSV](https://antonio-bidart.github.io/world-cup-recap-pipeline/matches.csv)
- [Descargar estado de selecciones JSON](https://antonio-bidart.github.io/world-cup-recap-pipeline/team_status.json)

Nota: los links funcionan despues de habilitar GitHub Pages con source `GitHub Actions` y ejecutar el workflow.

## Que demuestra

- **Automatizacion horaria:** GitHub Actions corre el pipeline cada 1 hora.
- **Datos abiertos y gratis:** usa Wikipedia/MediaWiki API, sin API key y sin servicios pagos.
- **Persistencia relacional:** guarda partidos, recaps y corridas en SQLite.
- **Idempotencia:** cada partido tiene `match_id` estable y `payload_hash` para evitar duplicados.
- **Recaps automaticos:** usa un motor local gratuito y reproducible; GitHub Models puede activarse como mejora opcional si hay acceso gratuito disponible.
- **Observabilidad:** registra corridas y contadores en SQLite y en `logs/runs.ndjson`.
- **Salida ejecutiva:** publica HTML, CSV y JSON listos para consumir.


## Uso local

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
python -m worldcup_recap run
python -m worldcup_recap latest
```

Archivos generados:

- `data/worldcup.sqlite`: base con partidos, recaps y corridas.
- `site/index.html`: reporte visual.
- `site/matches.csv`: partidos y recaps.
- `site/team_status.json`: proximo partido o estado de cada seleccion.
- `logs/runs.ndjson`: logs estructurados.

## Fuente y costo

La fuente principal es la API publica de Wikipedia/MediaWiki. El modo por defecto no requiere ninguna credencial paga. GitHub Models queda como mejora opcional con limites gratuitos, pero el pipeline no depende de eso para funcionar.
