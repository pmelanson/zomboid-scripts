# zomboid-scripts
When you start splitting out into more than one hacky python script, that's when you know you need a repo

## Scripts you can run

`scrape-scripts-to-csv.py` will scrape some hardcoded fields into a csv, when provided a directory that contains a bunch of .txt script files.

`scrape-scriptfiles-to-json.py` will scrape the contents of a workshop directory.  
Example: `python3 scrape-scriptfiles-to-json.py  -d '/mnt/c/Program Files (x86)/Steam/steamapps/workshop'`

## Helpful modules

`parse_scriptfile.py` will take a scriptfile (as a string) and parse it as a JSON object (a dict, in python lingo).