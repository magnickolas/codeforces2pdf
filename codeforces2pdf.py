import argparse
import logging
import os
import re
import requests
import subprocess
import sys
import tempfile
from typing import Tuple

import bs4
from weasyprint import HTML, CSS


class Formatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.INFO:
            self._style._fmt = "[\033[0;32m%(message)s\033[0m]"
        elif record.levelno == logging.ERROR:
            self._style._fmt = "\033[0;31mERROR: %(message)s\033[0m"
        elif record.levelno == logging.WARNING:
            self._style._fmt = "\033[0;34mWARNING: %(message)s\033[0m"
        else:
            self._style._fmt = "%(message)s"
        return super().format(record)


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(Formatter())
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def error(message):
    logger.error(message)
    sys.exit(1)


def exception(message):
    logger.exception(message)
    sys.exit(1)


def warning(message):
    logger.warning(message)


def info(message):
    logger.info(message)


def debug(message):
    logger.debug(message)


def remove_spans(block: bs4.Tag):
    spans = list(block.find_all("span"))
    for span in spans:
        span.replace_with(span.encode_contents().decode())


def extract_problem(contest_id, problem) -> Tuple[str, str]:
    problem_url = f"https://codeforces.com/contest/{contest_id}/problem/{problem}"
    try:
        resp = requests.get(problem_url)
    except requests.exceptions.ConnectionError:
        exception("failed to fetch problem webpage: {problem_url=}")
    if not resp.ok:
        error(f"codeforces returned error code: {problem_url=} {resp.status_code=}")
    bs = bs4.BeautifulSoup(resp.content, 'html.parser')
    problem_block = bs.select_one(".problemindexholder")
    if problem_block is None:
        error("couldn't find the problem block on a webpage")
    remove_spans(problem_block)
    html = problem_block.encode_contents().decode()

    return f"{contest_id}{problem}.pdf", html


def render_formulas(html: str) -> Tuple[bool, str]:
    formula_pattern = re.compile(r"\$\$(\$[^\$]*\$)\$\$")
    latex_template = (
        r"\documentclass{{article}}"
        r"\usepackage[utf8]{{inputenc}}"
        r"\begin{{document}}"
        "{content}"
        r"\end{{document}}"
    )
    formulas = re.findall(formula_pattern, html)
    latex_src = latex_template.format(content="\n\n".join(formulas))
    with tempfile.NamedTemporaryFile("w", suffix=".tex") as f:
        f.write(latex_src)
        f.flush()
        rendered = True
        try:
            p = subprocess.Popen(
                ["make4ht", "-u", f.name],
                cwd=os.path.split(f.name)[0],
                stdout=subprocess.DEVNULL,
            )
            if p.wait() != 0:
                rendered = False
        except Exception:
            rendered = False
        finally:
            if not rendered:
                warning("converting from latex to html with make4ht failed")
                return False, html

    output_filename = f'{f.name.removesuffix(".tex")}.html'
    bs = bs4.BeautifulSoup(open(output_filename, "r"), "html.parser")
    html_formulas_embeds = [
        par.encode_contents().decode().strip() for par in bs.find_all("p")
    ]
    if len(formulas) != len(html_formulas_embeds):
        warning("failed to render latex formulas")
        return False, html
    formula_embed_map = dict(zip(formulas, html_formulas_embeds))
    return True, re.sub(formula_pattern, lambda x: formula_embed_map[x.group(1)], html)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("contest_id", type=int)
    parser.add_argument("problem", type=str)
    return parser.parse_args()


def build_pdf_from_html(html: str, file_name: str):
    HTML(string=html, base_url="https://codeforces.com/").write_pdf(
        file_name,
        stylesheets=[
            CSS("styles/ttypography.css"),
            CSS("styles/problem-statement.css"),
            CSS("styles/clear.css"),
            CSS("styles/style.css"),
        ],
    )


def main():
    args = parse_args()

    contest_id = args.contest_id
    problem = args.problem

    debug(f"fetching problem webpage: {contest_id=} {problem=}")
    out_filename, html = extract_problem(contest_id, problem)
    info("fetched")

    debug("rendering latex")
    rendered, html = render_formulas(html)
    if rendered:
        info("rendered latex")

    debug("building pdf")
    build_pdf_from_html(html, out_filename)
    info(f"done")


if __name__ == "__main__":
    main()
