# data-mesh-cosmetics

Projet 32 (DS1) : Data Mesh pour une enseigne de cosmétiques. Trois domaines publient chacun un Data Product avec son Data Contract ; un pipeline CI bloque les changements qui casseraient les consommateurs.

## Lancer

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py
```

Ou avec Docker : `docker compose up --build`.

| Service | Adresse |
|---|---|
| Data Catalog | http://localhost:8080 |
| Governance Registry | http://localhost:8000/docs |
| Merchandising | http://localhost:8001/docs |
| Fulfillment | http://localhost:8002/docs |
| Customer Finance | http://localhost:8003/docs |

## Tests

Les services doivent tourner.

```bash
cd validators && python -m pytest -v
cd governance && python -m pytest -v
python governance/check_contract_changes.py
```

## Démo du breaking change

```bash
cp governance/proposals/merchandising-products-rename-price.yaml contracts/merchandising-products.yaml
python governance/check_contract_changes.py    # FAILED
git checkout contracts/merchandising-products.yaml
```

## Notes

- Chaque service a sa base SQLite, créée au démarrage. Supprimer les fichiers `.db` pour repartir des données de départ.
- L'assistant IA du catalog utilise `ANTHROPIC_API_KEY`. Sans clé, il affiche un résumé sans IA.
