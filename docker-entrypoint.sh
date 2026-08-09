#!/bin/sh
set -e

WORKING_DIR="/app/lightrag_pdf_otimizado"
SEED_DIR="/app/seed_data/lightrag_pdf_otimizado"

mkdir -p "$WORKING_DIR"

# Primeiro boot com um Volume vazio (ou sem Volume nenhum): semeia a base
# indexada que veio embutida na imagem. Depois disso o Volume manda.
if [ ! -f "$WORKING_DIR/graph_chunk_entity_relation.graphml" ] && [ -d "$SEED_DIR" ]; then
  echo "Base vazia em $WORKING_DIR — copiando semente de $SEED_DIR"
  cp -r "$SEED_DIR"/. "$WORKING_DIR"/
fi

exec uvicorn backend.server:app --host 0.0.0.0 --port "${PORT:-8001}"
