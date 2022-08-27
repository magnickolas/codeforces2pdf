# codeforces2pdf
Extract [CodeForces](https://codeforces.com/) problems to PDF files

A remake of https://github.com/AliOsm/codeforces2pdf, with Selenium replaced by requests + BeautifulSoup + either mathjax or make4ht latex renderer.

## Prerequisites
- [Python 3.9+](https://www.python.org/)
- [mathjax-node-cli](https://github.com/mathjax/mathjax-node-cli) (for default and graphics mode)
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
python3 codeforces2pdf.py [-d OUT_DIR] [-f|-g] <contest_id> <problem>
```

### Notes
With `-f | --fast` the utility executes a tiny bit faster and requires only TexLive distribution, but produces simpler and much less sane views of latex formulas.
With `-g | --graphics` the formulas are rendered to SVGs, one may prefer this rendering, but it consumes lots of CPU time.


## License
The project is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
