from bs4 import BeautifulSoup
import re
import urllib.parse


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
                    link = f"[{link_text.strip()}]({replace_filename(link_href.strip(), self.table)})"
                    if not link in processed_text:
                        self.processed_links.append(link)
                        processed_text = processed_text.replace(
                            link_text, link)

            for img_tag in img_tags:
                src = img_tag.get("src", "")
                alt_text = img_tag.get("alt", "Image").strip() or src
                img = f" ![{alt_text}]({src})"
                if self.check_url(src):
                    if not img in processed_text:
                        self.processed_links.append(img)
                        processed_text += img

            processed_text = re.sub(r' +', ' ', processed_text)
            processed_text = re.sub(r'\n\n+', '\n\n', processed_text)
            self.markdown += f"\n{processed_text}\n\n"

    def handle_emphasis(self, tag):
        self.markdown += f"*{tag.get_text().strip()}*"

    def handle_strong(self, tag):
        text = tag.get_text().strip()
        if text:
            self.markdown += f"**{tag.get_text().strip()}**"

    def handle_link(self, tag):
        link_href = tag.get('href')
        link_text = tag.get_text() or 'link'
        if self.check_url(link_href):
            link = f"[{link_text.strip()}]({replace_filename(link_href.strip(), self.table)})"
            self.processed_links.append(link)
            self.markdown += link

    def handle_image(self, tag):
        alt_text = tag.get("alt", "Image")
        src = tag.get("src", "")
        if self.check_url(src):
            self.markdown += f"![{alt_text.strip()}]({src})"

    def handle_list(self, tag):
        list_items = [li.get_text() for li in tag.find_all("li")]
        for item in list_items:
            self.markdown += f"  - {item.strip()}\n"

    def check_url(self, url):
        if not url or url.strip() == '' or url.strip() == '#':
            return False
        invalid_url = ['.', '/', '(', '[', 'attachments', 'image']
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
                    link = f"[{link_text.strip()}]({replace_filename(link_href.strip(), self.table)})"
                    if not link in processed_text:
                        self.processed_links.append(link)
                        processed_text = processed_text.replace(
                            link_text, link)

        for img_tag in img_tags:
            src = img_tag.get("src", "")
            alt_text = img_tag.get("alt", "Image") or src
            img = f"![{alt_text}]({src})"
            if self.check_url(src):

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

        processed_text = re.sub(r' +', ' ', processed_text)
        processed_text = re.sub(r'\n\n+', '\n\n', processed_text)
        processed_text = processed_text.replace('\n', '<br>')
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
                processed_headers = [self.process_cell(header) for header in rows[0].find_all(["th", "td"])]
                self.markdown += "*   - " + "\n    - ".join(processed_headers) + "\n"
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


def convert_to_valid_url(input_string):
    url_string = re.sub(
        r' +', ' ', input_string.replace('\n', ' ')).replace(' ', '_')
    url_string = urllib.parse.quote(url_string, safe=':()?&=#')
    return url_string.replace('.html', '.md')


def replace_filename(name, table):
    if name in table:
        return table[name]
    return name.replace('.html', '.md')


with open('/home/guillermo/Portal/py/md_converter/test1/ARTPLATSWS/How-to-measure-in-Slipstream-Rig_350226574.html', 'r', encoding='utf-8') as file:
    html_content = file.read()
    table = build_url_table()
    # Convert HTML to Markdown using your custom converter
    converter = HTMLToMarkdownConverter(table)
    markdown_content = converter.convert(html_content)

    # Write Markdown to a file
    with open('test1/source/SOLBSW/MD_TEST.md', 'w', encoding='utf-8') as file:
        file.write(markdown_content)

    print("HTML to Markdown conversion completed.")
