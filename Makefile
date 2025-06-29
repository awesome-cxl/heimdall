
.PHONY: standalone
standalone:
	# UV may not correctly detect the sub-folder changes and decide not to build.
	rm -rf build dist
	uv run pyinstaller --onefile --name=heimdall heimdall/heimdall.py
