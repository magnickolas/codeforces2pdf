# codeforces2pdf
Extract [CodeForces](https://codeforces.com/) problems to PDF files

A remake of https://github.com/AliOsm/codeforces2pdf, with Selenium replaced by requests + BeautifulSoup + either mathjax-node-cli or make4ht latex renderer.

## Prerequisites
- [Python 3.9+](https://www.python.org/)
- [mathjax-node-cli](https://github.com/mathjax/mathjax-node-cli) (for pretty mode)
- [make4ht](https://ctan.org/pkg/make4ht/) (for fast mode)

## Quickstart

Install dependencies with poetry
```console
poetry install
```
or with raw pip
```console
pip install -r requirements.txt
```

Extract a problem from a contest:
```console
python3 codeforces2pdf.py [-d OUT_DIR] [-f] <contest_id> <problem>
```

### Notes
With `-f | --fast` the utility executes faster, but produces simpler and less sane view of latex formulas.

## License
The project is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
