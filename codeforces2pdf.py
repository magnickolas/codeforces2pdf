import argparse
from dataclasses import dataclass
from enum import Enum
from html import unescape
import logging
import os
from pathlib import Path
import re
import requests
import subprocess
import sys
import tempfile
from typing import Optional, Tuple

import bs4
from weasyprint import HTML, CSS

CACHE_PATH = ".cache"
TEMP_FILES = []


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


class Mode(Enum):
    DEFAULT = 1
    FAST = 2
    GRAPHICS = 3


@dataclass(frozen=True)
class LatexFormula:
    content: str
    is_inline: bool


def remove_alert(block: bs4.Tag):
    for div in block.find_all("div", class_=['alert', 'alert-info', 'diff-notifier']):
        div.extract()


def extract_problem(contest_id, problem) -> Tuple[str, str]:
    problem_url = f"https://codeforces.com/contest/{contest_id}/problem/{problem}"
    try:
        resp = requests.get(problem_url)
    except requests.exceptions.ConnectionError:
        exception("failed to fetch problem webpage: {problem_url=}")
    if not resp.ok:
        error(f"codeforces returned error code: {problem_url=} {resp.status_code=}")
    bs = bs4.BeautifulSoup(resp.content, "html.parser")
    problem_block = bs.select_one(".problemindexholder")
    if problem_block is None:
        error("couldn't find the problem block on a webpage")
    remove_alert(problem_block)
    html = problem_block.decode_contents()

    return f"{contest_id}{problem}.pdf", html


def generate_latex_formulas_embeds_graphics(
    formulas: list[LatexFormula],
) -> Optional[list[str]]:
    if not formulas:
        return []
    Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)
    svgs_files = [
        tempfile.NamedTemporaryFile("wb+", dir=CACHE_PATH, suffix=".svg")
        for _ in formulas
    ]
    global TEMP_FILES
    TEMP_FILES += svgs_files
    embeds = []
    rendered = True
    try:
        ps = []
        for formula, svg_file in zip(formulas, svgs_files):
            extra_args = ["--inline"] * formula.is_inline
            ps.append(
                subprocess.Popen(
                    ["tex2svg", *extra_args, f" {unescape(formula.content)}"],
                    stdout=svg_file,
                )
            )
            embeds.append(f'<img src="{svg_file.name}" align="middle" />')
        for p in ps:
            if p.wait() != 0:
                rendered = False
                break
    except Exception:
        rendered = False
    finally:
        if not rendered:
            warning("converting from latex to html with tex2svg failed")
            return None
    return embeds


def generate_latex_formulas_embeds(
    formulas: list[LatexFormula],
) -> Optional[list[str]]:
    if not formulas:
        return []
    rendered = True
    html = None
    try:
        arg = " " + r" \\ ".join(unescape(f.content) for f in formulas) + r" \\"
        p = subprocess.Popen(
            ["tex2htmlcss", "--inline", arg],
            stdout=subprocess.PIPE,
        )
        html, _ = p.communicate()
        if p.returncode != 0:
            rendered = False
    except Exception:
        rendered = False
    finally:
        if not rendered:
            warning("converting from latex to html with tex2htmlcss failed")
            return None
    if html is None:
        return None
    bs = bs4.BeautifulSoup(html, "html.parser")
    embeds = bs.find_all("span", class_="mjx-block")[:-1]
    embeds = [e.find("span", class_="mjx-box") for e in embeds]
    embeds = [e for e in embeds if e]
    for e in embeds:
        e["class"] = "mjx-chtml mjx-math"
    if len(formulas) != len(embeds):
        warning("failed to render latex formulas")
        return None
    return embeds


def generate_latex_formulas_embeds_fast(
    formulas: list[LatexFormula],
) -> Optional[list[str]]:
    if not formulas:
        return []
    latex_template = (
        r"\documentclass{{minimal}}"
        r"\usepackage[utf8]{{inputenc}}"
        r"\begin{{document}}"
        "{content}"
        r"\end{{document}}"
    )
    latex_src = latex_template.format(
        content="\n\n".join(map(lambda f: f"${unescape(f.content)}$", formulas))
    )
    Path(CACHE_PATH).mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=CACHE_PATH, suffix=".tex") as f:
        f.write(latex_src)
        f.flush()
        rendered = True
        try:
            p = subprocess.Popen(
                ["make4ht", "-u", f.name, "svg"],
                cwd=os.path.split(f.name)[0],
            )
            if p.wait() != 0:
                rendered = False
        except Exception:
            rendered = False
        finally:
            if not rendered:
                warning("converting from latex to html with make4ht failed")
                return None
    output_filename = f'{f.name.removesuffix(".tex")}.html'
    bs = bs4.BeautifulSoup(open(output_filename, "r"), "html.parser")
    html_formulas_embeds = [
        par.decode_contents().strip() for par in bs.find_all("p")
    ]
    if len(formulas) != len(html_formulas_embeds):
        warning("failed to render latex formulas")
        return None
    return html_formulas_embeds


def render_formulas(html: str, mode: Mode) -> Tuple[bool, str]:
    inline_formula_pattern = re.compile(r"([^\$])\${3}([^\$]+)\${3}")
    display_formula_pattern = re.compile(r"\${6}([^\$]+)\${6}")

    inline_formulas = [
        LatexFormula(x[1], True) for x in re.findall(inline_formula_pattern, html)
    ]
    display_formulas = [
        LatexFormula(x, False) for x in re.findall(display_formula_pattern, html)
    ]
    all_formulas = inline_formulas + display_formulas

    generate_latex_formulas = generate_latex_formulas_embeds
    if mode == Mode.FAST:
        generate_latex_formulas = generate_latex_formulas_embeds_fast
    elif mode == Mode.GRAPHICS:
        generate_latex_formulas = generate_latex_formulas_embeds_graphics

    formulas_embeds = generate_latex_formulas(all_formulas)
    if formulas_embeds is None:
        return False, html

    formula_embed_map = dict(zip(all_formulas, formulas_embeds))
    html = re.sub(
        inline_formula_pattern,
        lambda x: f"{x.group(1)}{formula_embed_map[LatexFormula(x.group(2), True)]}",
        html,
    )
    html = re.sub(
        display_formula_pattern,
        lambda x: f'<div style="text-align:center;">{formula_embed_map[LatexFormula(x.group(1), False)]}</div>',
        html,
    )
    return True, html


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("contest_id", type=int)
    parser.add_argument("problem", type=str)
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-f", "--fast", action="store_true")
    group.add_argument("-g", "--graphics", action="store_true")

    parser.add_argument("-d", "--output-dir", type=str, default=".")
    return parser.parse_args()


def build_pdf_from_html(html: str, output_dir: str, file_name: str, mode: Mode):
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    extra_css = [CSS("styles/tex2html.css")] * (mode == Mode.DEFAULT)
    HTML(string=html, base_url="").write_pdf(
        p / file_name,
        stylesheets=[
            CSS("styles/ttypography.css"),
            CSS("styles/problem-statement.css"),
            CSS("styles/clear.css"),
            CSS("styles/style.css"),
            CSS("styles/font_cuprum.css"),
            CSS("styles/font_pt_sans_narrow.css"),
            *extra_css,
        ],
    )


def main():
    args = parse_args()

    contest_id = args.contest_id
    problem = args.problem
    mode = Mode.DEFAULT
    if args.fast:
        mode = Mode.FAST
    elif args.graphics:
        mode = Mode.GRAPHICS
    output_dir = args.output_dir

    debug(f"fetching problem webpage: {contest_id=} {problem=}")
    out_filename, html = extract_problem(contest_id, problem)
    info("fetched")

    debug("rendering latex")
    rendered, html = render_formulas(html, mode)
    if rendered:
        info("rendered latex")

    debug("building pdf")
    build_pdf_from_html(html, output_dir, out_filename, mode)
    info("done")


if __name__ == "__main__":
    main()
