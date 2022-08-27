# codeforces2pdf
Extract [CodeForces](https://codeforces.com/) problems to PDF files

A remake of https://github.com/AliOsm/codeforces2pdf, with Selenium replaced by requests + BeautifulSoup + make4ht latex renderer.

## Prerequisites
- [Python 3.9+](https://www.python.org/)
- [make4ht](https://ctan.org/pkg/make4ht/)

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
python3 codeforces2pdf.py <contest_id> <problem>
```

## License
The project is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).
