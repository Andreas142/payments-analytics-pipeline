.PHONY: fetch ingest clean

fetch:
	python scripts/fetch_data.py

ingest:
	python scripts/ingest.py

clean:
	rm -f data/landing/*.parquet