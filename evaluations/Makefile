%.csv : %.yaml
	cd .. && venv/bin/python dataontosearch.py evaluate "evaluations/$<" --format csv > "evaluations/$@"
