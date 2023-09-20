from bs4 import BeautifulSoup
import re

import os
import shutil

import logging

import urllib.parse

source_folder = '/home/guillermo/Portal/py/md_converter/test1/ARTPLATSWS'
destination_folder = '/home/guillermo/Portal/py/md_converter/test1/source/ARTPLATSWS'
index_file = '/home/guillermo/Portal/py/md_converter/test1/ARTPLATSWS/index.html'
toctree_rst_file = '/home/guillermo/Portal/py/md_converter/test1/source/ARTPLATSWS/index.rst'
index_rst = '/home/guillermo/Portal/py/md_converter/test1/source/ARTPLATSWS/index.rst'


class HTMLToMarkdownConverter:
    def __init__(self, table):
        self.markdown = ""
        self.has_title = False
        self.count = 0
        self.processed_links = []
        self.table = table

    def handle_heading(self, tag):
        level = int(tag.name[1])
        if tag.get('id') == 'title-heading':
            self.has_title = True
            title = tag.get_text().strip()
            # Parse title removing unwanted part
            match = re.search(r'[^:]+:\s(.*?)$', title)
            if match:
                title = match.group(1)
            self.markdown += f"\n\n{'#' * level} {title}\n\n"
        elif self.has_title:
            self.markdown += f"\n\n{'#' * (level + 1)} {tag.get_text().strip()}\n\n"
        else:
            self.markdown += f"\n\n{'#' * level} {tag.get_text().strip()}\n\n"

    def handle_paragraph(self, tag):
        if tag.get_text().strip() == 'TOC':
            tag.decompose()
        elif tag.has_attr('style'):
            tag['style'] == ''
        else:
            link_tags = tag.find_all("a")
            img_tags = tag.find_all("img")
            processed_text = tag.get_text().strip()

            for link_tag in link_tags:
                link_href = link_tag.get('href')
                link_text = link_tag.get_text() or 'link'
                if self.check_url(link_href):
                    link = f"[{link_text.strip()}]({replace_filename(link_href.strip(), self.table)}) "
                    if not link in processed_text:
                        self.processed_links.append(link)
                        processed_text = processed_text.replace(
                            link_text, link)

            for img_tag in img_tags:
                src = img_tag.get("src", "")
                alt_text = img_tag.get("alt", "Image").strip() or src
                img = f" ![{alt_text}]({src}) "
                if self.check_url(src) and not '/thumbnail/' in src:
                    if not img in processed_text:
                        self.processed_links.append(img)
                        processed_text += img

            processed_text = re.sub(r' +', ' ', processed_text)
            processed_text = re.sub(r'\n\n+', '\n\n', processed_text)
            self.markdown += f"\n{processed_text}\n\n"

    def handle_emphasis(self, tag):
        self.markdown += f"*{tag.get_text().strip()}* "

    def handle_strong(self, tag):
        text = tag.get_text().strip()
        if text:
            self.markdown += f"**{tag.get_text().strip()}** "

    def handle_link(self, tag):
        link_href = tag.get('href')
        link_text = tag.get_text() or 'link'
        if self.check_url(link_href):
            link = f"[{link_text.strip()}]({replace_filename(link_href.strip(), self.table)}) "
            self.processed_links.append(link)
            self.markdown += link

    def handle_image(self, tag):
        alt_text = tag.get("alt", "Image")
        src = tag.get("src", "")
        if self.check_url(src) and not '/thumbnail/' in src:
            self.markdown += f"![{alt_text.strip()}]({src}) "

    def handle_list(self, tag):
        list_items = [li.get_text() for li in tag.find_all("li")]
        for item in list_items:
            self.markdown += f"  - {item.strip()}\n"

    def check_url(self, url):
        if not url or url.strip() == '' or url.strip() == '#':
            return False
        invalid_url = ['.', '/', '(', '[', 'rest/']
        for invalid in invalid_url:
            if url.strip().startswith(invalid):
                return False
        return True

    def process_cell(self, tag):
        processed_text = tag.get_text()
        link_tags = tag.find_all("a")
        img_tags = tag.find_all("img")
        em_tags = tag.find_all("em")
        stron_tags = tag.find_all("strong")
        overlined = tag.find_all("s")
        code_tags = tag.find_all("code")

        for link_tag in link_tags:
            if not link_tag.find_all('img') and not link_tag.find_all('a'):
                link_href = link_tag.get('href')
                link_text = link_tag.get_text() or 'link'
                if self.check_url(link_href):
                    link = f"[{link_text.strip()}]({replace_filename(link_href.strip(), self.table)}) "
                    if not link in processed_text:
                        self.processed_links.append(link)
                        processed_text = processed_text.replace(
                            link_text, link)

        for img_tag in img_tags:
            src = img_tag.get("src", "")
            alt_text = img_tag.get("alt", "Image") or src
            img = f"![{alt_text}]({src}) "
            if self.check_url(src) and not '/thumbnail/' in src:

                if img_tag.parent:
                    parent = img_tag.parent.get_text().strip()
                    html = str(img_tag.parent).replace(str(img_tag), img)
                    soup = BeautifulSoup(html, "html.parser")
                    soup_text = soup.get_text().strip()
                    if soup_text not in processed_text:
                        self.processed_links.append(img)
                        start = processed_text.find(parent)
                        end = start + len(parent)
                        processed_text = processed_text[:start] + \
                            soup_text + processed_text[end:]

        for em_tag in em_tags:
            text = em_tag.get_text()
            em_text = f"*{text}*"
            if text and not em_text in processed_text:
                processed_text = processed_text.replace(text, em_text)

        for strong_tag in stron_tags:
            text = strong_tag.get_text()
            strong_text = f"**{text}** "
            if text:
                if not strong_text in processed_text:
                    processed_text = processed_text.replace(text, strong_text)

        for overline in overlined:
            text = overline.get_text()
            for link in self.processed_links:
                if text == link:
                    continue
            overlined_text = f"~~{text}~~ "
            if text and not overlined_text in processed_text:
                processed_text = processed_text.replace(text, overlined_text)

        for code in code_tags:
            text = code.get_text()
            code_text = f"`{text}` "
            if text:
                if not code_text in processed_text:
                    processed_text = processed_text.replace(text, code_text)

        processed_text = clean_text(processed_text).replace('\n', '<br>')
        processed_text = re.sub(r'(<br>){2,}', '<br><br>', processed_text)
        return processed_text

    def handle_table(self, tag):
        rows = tag.find_all("tr")
        if rows:
            table_title = tag.caption.get_text().strip() if tag.caption else ""
            col_widths = tag.get("data-column-widths", "").split(",")
            header_rows = int(tag.get("data-header-rows", "1"))

            self.markdown += f"\n\n:::{{list-table}} {table_title}\n"

            if col_widths and all(width.strip().isdigit() for width in col_widths):
                self.markdown += f":widths: {' '.join(col_widths)}\n"

            self.markdown += f":header-rows: {header_rows}\n\n"
            # Find the maximum number of columns in any row
            max_columns = max(len(row.find_all(["th", "td"])) for row in rows)

            headers = [header.get_text().strip()
                       for header in rows[0].find_all(["th", "td"])]
            headers = [header.replace('\n', ' <br> ').replace(
                '-', ' ').strip() for header in headers]

            # Add empty headers for any missing columns
            while len(headers) < max_columns:
                headers.append("")

            if len(rows) < 2:
                processed_headers = [self.process_cell(
                    header) for header in rows[0].find_all(["th", "td"])]
                self.markdown += "*   - " + \
                    "\n    - ".join(processed_headers) + "\n"
                for i, _ in enumerate(processed_headers):
                    if i == 0:
                        self.markdown += "*   - " + "\n"
                    else:
                        self.markdown += "    - " + "\n"

            else:
                self.markdown += "*   - " + "\n    - ".join(headers) + "\n"
                for row in rows[1:]:
                    cells = [self.process_cell(cell)
                             for cell in row.find_all(["th", "td"])]

                    # Add empty cells for any missing columns
                    while len(cells) < max_columns:
                        cells.append("")

                    self.markdown += "*   - " + "\n    - ".join(cells) + "\n"

            self.markdown += ":::\n\n"

    def convert(self, html):
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted sections
        breadcrumb = soup.find('div', id="breadcrumb-section")
        if (breadcrumb):
            breadcrumb.decompose()
        page_sections = soup.find_all("div", {"class": "pageSection"})
        attachments = soup.find_all(
            "div", {"class": "plugin_attachments_container"})
        if (page_sections):
            for div in page_sections:
                div.decompose()
        if (attachments):
            for div in attachments:
                div.decompose()

        footer = soup.find('div', id="footer")
        if (footer):
            footer.decompose()

        for tag in soup.find_all("ul", {'class': 'toc-indentation'}):
            tag.decompose()

        for tag in soup.find_all():
            if tag.find_parent("table"):
                continue  # Skip processing tags within tables
            if tag.name == "h1" or tag.name == "h2" or tag.name == "h3":
                self.handle_heading(tag)
            elif tag.name == "p":
                self.handle_paragraph(tag)
            elif tag.name == "em":
                self.handle_emphasis(tag)
            elif tag.name == "strong":
                self.handle_strong(tag)
            elif tag.name == "a":
                if tag.find_parent("p"):
                    continue  # Skip processing links within paragraphs
                self.handle_link(tag)
            elif tag.name == "img":
                if tag.find_parent("p"):
                    continue  # Skip processing imgs within paragraphs
                self.handle_image(tag)
            elif tag.name == "ul" or tag.name == "ol":
                self.handle_list(tag)
            elif tag.name == "table":
                self.handle_table(tag)

        return re.sub(r'\n\n+', '\n\n', self.markdown.strip())


# ----------------- MAIN -------------------

def build_url_table():
    index_path = '/home/guillermo/Portal/py/md_converter/test1/ARTPLATSWS/index.html'
    table = {}

    with open(index_path, 'r', encoding='utf-8') as file:
        html = file.read()
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all('a')

        for link in links:
            url = link.get('href')
            text = link.get_text() or url
            if url not in table:
                table[url] = convert_to_valid_url(text) + '.md'

        # print(table)
        return table


def clean_text(text):
    return re.sub(r' +', ' ', re.sub(r'\n\n+', '\n\n', text.strip()))


def replace_filename(name, table):
    if name in table:
        return table[name]
    return name.replace('.html', '.md')


def extract_toc_structure(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    def calculate_indentation(tag):
        indentation = 0
        parent = tag.find_parent(['ul'])
        while parent:
            indentation += 1
            parent = parent.find_parent(['ul'])
        return indentation

    toc_structure = []

    for anchor in soup.find_all('a', href=True):
        link = anchor['href']
        if link.endswith('.html'):
            text = re.sub(r' +', ' ', anchor.get_text().replace('\n', ' '))
            indentation = calculate_indentation(anchor)

            url = convert_to_valid_url(text)

            toc_structure.append(
                {'text': text, 'link': url, 'indentation': indentation})

    return toc_structure


def create_toc_tree(toc_structure):
    toc_tree = []
    stack = []

    for item in toc_structure:
        while stack and stack[-1]['indentation'] >= item['indentation']:
            stack.pop()

        if not stack:
            toc_tree.append(item)
        else:
            parent = stack[-1]
            if 'subitems' not in parent:
                parent['subitems'] = []
            parent['subitems'].append(item)

        stack.append(item)

    # print(toc_tree)
    return toc_tree


def convert_to_valid_url(input_string):
    url_string = re.sub(
        r' +', ' ', input_string.replace('\n', ' ')).replace(' ', '_')
    url_string = urllib.parse.quote(url_string, safe=':()?&=#').replace('~', '').replace('*', '')
    return url_string.replace('.html', '.md')


def write_toctree(toc_tree, file, name):
    page = find_value_recursive(toc_tree, name.replace('.md', ''))
    if page and 'subitems' in page:
        file.write("\n\n```{toctree}\n")
        file.write("   :hidden:\n\n")

        for item in page['subitems']:
            file.write('   ' + f"{item['text']} <{item['link']}>\n")

        file.write("```\n")


def write_index_rst(toc_tree, path, title):
    tree = f"{title}\n" + '=' * \
        len(title) + '\n\n' + ".. toctree::\n   :hidden:\n\n"
    for item in toc_tree:
        if 'subitems' in item:
            for subitem in item['subitems']:
                tree += f'   {subitem["text"]} <{convert_to_valid_url(subitem["link"])}>\n'
    with open(path, 'w', encoding='utf-8') as file:
        file.write(tree)


def find_value_recursive(data, target_key):
    if isinstance(data, dict):
        if 'link' in data and data['link'] == target_key:
            return data
        for key, value in data.items():
            result = find_value_recursive(value, target_key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_value_recursive(item, target_key)
            if result is not None:
                return result
    return None


def check_local_files(path):
    # Check if the link path is local and the file exists
    # If not exists, change the path in order to take the file/page from Confluence
    with open(path, 'r', encoding='utf-8') as file:
        if file:
            return True


def run_conversion():
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    os.makedirs(destination_folder)
    n = 0
    n_errors = 0
    table = build_url_table()
    toc_structure = extract_toc_structure(index_file)
    toc_tree = create_toc_tree(toc_structure)
    filename_len = 20
    image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.log', '.yaml', '.eml']

    write_index_rst(toc_tree, index_rst, 'ARTPLATSWS')

    for root, _, files in os.walk(source_folder):
        for file_name in files:
            try:
                print(f"[{n+1}/{len(files)}] Processing: {file_name}" +
                      ' '*filename_len, end='\r')
                filename_len = len(file_name)

                source_file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(
                    source_file_path, source_folder)
                destination_file_path = os.path.join(
                    destination_folder, relative_path)

                os.makedirs(os.path.dirname(
                    destination_file_path), exist_ok=True)

                if file_name.endswith('.html'):
                    with open(source_file_path, 'r', encoding='utf-8') as file:
                        html_content = file.read()

                    converter = HTMLToMarkdownConverter(table)
                    markdown_content = converter.convert(html_content)

                    updated_filename = replace_filename(file_name, table)
                    destination_file = destination_folder + '/' + updated_filename

                    with open(destination_file, 'w', encoding='utf-8') as file:
                        file.write(markdown_content)
                        if file_name in table:
                            write_toctree(toc_tree, file, table[file_name])

                else:
                    for format in image_formats:
                        if file_name.endswith(format) or (file_name.isdigit() and not '.' in file_name):
                            shutil.copyfile(source_file_path,
                                            destination_file_path)
                n += 1

            except Exception as e:
                logging.error(
                    f"\033[91m An error occurred in {file_name}: {str(e)} \033[0m")
                n += 1
                n_errors += 1

    if n_errors == 0:
        print(
            f"HTML to Markdown conversion completed.\n\033[92m{n_errors} Errors.")
    else:
        print(
            f"HTML to Markdown conversion completed.\n\033[91m{n_errors} Errors.")


run_conversion()
