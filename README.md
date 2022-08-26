# codeforces2pdf
Extract [CodeForces](https://codeforces.com/) problems to PDF files

A remake of https://github.com/AliOsm/codeforces2pdf, with Selenium replaced by requests+BeautifulSoup+make4ht latex renderer.

## Prerequisites
- [Python 3.7+](https://www.python.org/)
- [make4ht](https://ctan.org/pkg/make4ht/)
- [WeasyPrint](https://weasyprint.org/)
- The code in this repository has been tested on Ubuntu 22.04.1 LTS

## Quickstart

Extract a problem from a contest:
```console
python3 codeforces2pdf.py <contest_id> <problem>
```

## License
The project is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).

