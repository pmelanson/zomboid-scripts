# zomboid-scripts
When you start splitting out into more than one hacky python script, that's when you know you need a repo

## The scraper

`scrape-scriptfiles.py` will scrape the contents of a workshop directory and output various breakdowns into `output/`.

### Installing

1. Install [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) and [python](https://www.python.org/downloads/).

1. In a terminal run:

```
$ cd Documents  # Or whever you want to download this repo
$ git clone https://github.com/pmelanson/zomboid-scripts.git
$ cd zomboid-scripts
$ pip install -r requirements.txt
$ python3 scrape-scriptfiles.py --help
```

### Usage

Check `python3 scrape-scriptfiles.py --help` for usage.

Examples:

For Linux-On-Windows, you can use

```
python3 scrape-scriptfiles.py  -d '/mnt/c/Program Files (x86)/Steam/steamapps/workshop'
```

For Windows, you can use

```
python3 scrape-scriptfiles.py -d '\Program Files (x86)\Steam\steamapps\workshop'
```

### Features

There is a [partner spreadsheet](https://docs.google.com/spreadsheets/d/1VBMSYLmkI2A7kZRT4cdJNUCLgGhWb60XCGUmeedNELQ) to these python scripts! Here's how you (yes, you git user!) can update it:

1. Run `scrape-scriptfiles.py` and get an output

1. Make a pull request to this repository to update the files in `output/`

1. Get the pull request accepted and merged

1. Click the "🧟‍♀️ Import Zomboid Modded Data 🧟‍♂️" button in the spreadsheet--the new data will be imported into the spreadsheet! Hey presto!

## Helpful modules

The `parse_scriptfile` module will take a Zomboid scriptfile (as a string) and parse it as a JSON object (a dict, in python lingo). This is used by the `scrape-scriptfiles.py` scraper.