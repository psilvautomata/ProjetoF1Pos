"""Interface de linha de comando simples."""

import argparse
import json
import logging

from openf1_pipeline.pipelines import IngestionPipeline


def main() -> None:
    """Executa ingestão de meeting ou sessão."""
    parser = argparse.ArgumentParser(description="Ingere dados históricos da OpenF1")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--meeting", help="meeting_key a ingerir")
    group.add_argument("--session", help="session_key a ingerir")
    group.add_argument("--year", type=int, help="temporada histórica a preparar para o dashboard")
    parser.add_argument("--verbose", action="store_true", help="habilita logs informativos")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    pipeline = IngestionPipeline()
    if args.year is not None:
        result = pipeline.ingest_year(args.year)
    elif args.meeting:
        result = pipeline.ingest_meeting(args.meeting)
    else:
        result = pipeline.ingest_session(args.session)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
