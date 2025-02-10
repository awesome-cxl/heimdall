
.PHONY: standalone
standalone:
	# Poetry may not correctly detect the sub-folder changes and decide not to build.
	rm -rf build dist
	poetry install
	poetry run pyinstaller --onefile --name=heimdall heimdall/heimdall.py
