from bs4 import BeautifulSoup
import re


class HTMLToMarkdownConverter:
    def __init__(self):
        self.markdown = ""
        self.has_title = False
        self.count = 0

    def handle_heading(self, tag):
        level = int(tag.name[1])
        if tag.get('id') == 'title-heading':
            self.has_title = True
            self.markdown += f"\n\n{'#' * level} {tag.get_text().strip()}\n"
        elif self.has_title:
            self.markdown += f"\n\n{'#' * (level + 1)} {tag.get_text().strip()}\n"
        else:
            self.markdown += f"\n\n{'#' * level} {tag.get_text().strip()}\n"

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
                link_text = link_tag.get_text().strip() or link_tag.get('href') or 'link'
                link_href = link_tag.get('href') or link_text
                link = f"[{link_text}]({link_href})"
                if not link in processed_text:
                    processed_text = processed_text.replace(link_text, link)

            for img_tag in img_tags:
                src = img_tag.get("src", "")
                alt_text = img_tag.get("alt", "Image").strip() or src
                img = f" ![{alt_text}]({src})"
                if not img in processed_text:
                    processed_text += img

            processed_text = re.sub(r' +', ' ', processed_text)
            processed_text = re.sub(r'\n\n+', '\n\n', processed_text)
            self.markdown += f"\n{processed_text}\n\n"

    def handle_emphasis(self, tag):
        self.markdown += f"*{tag.get_text().strip()}*"

    def handle_strong(self, tag):
        self.markdown += f"**{tag.get_text().strip()}**"

    def handle_link(self, tag):
        self.markdown += f"[{tag.get_text().strip()}]({tag.get('href')})"

    def handle_image(self, tag):
        alt_text = tag.get("alt", "Image")
        src = tag.get("src", "")
        self.markdown += f"![{alt_text.strip()}]({src})"

    def handle_list(self, tag):
        list_items = [li.get_text() for li in tag.find_all("li")]
        for item in list_items:
            self.markdown += f"  - {item.strip()}\n"

    def process_cell(self, tag):
        processed_text = tag.get_text()
        link_tags = tag.find_all("a")
        img_tags = tag.find_all("img")
        em_tags = tag.find_all("em")
        stron_tags = tag.find_all("strong")

        for link_tag in link_tags:
            link_text = link_tag.get_text().strip() or link_tag.get('href') or 'link'
            link_href = link_tag.get('href') or link_text
            link = f"[{link_text}]({link_href})"
            if not link in processed_text:
                processed_text = processed_text.replace(link_text, link)

        for img_tag in img_tags:
            src = img_tag.get("src", "")
            alt_text = img_tag.get("alt", "Image") or src
            img = f"![{alt_text}]({src})"

            if img_tag.parent:
                parent = img_tag.parent.get_text().strip()
                html = str(img_tag.parent).replace(str(img_tag), img)
                soup = BeautifulSoup(html, "html.parser")
                soup_text = soup.get_text().strip()
                if soup_text not in processed_text:
                    start = processed_text.find(parent)
                    end = start + len(parent)
                    processed_text = processed_text[:start] + \
                        soup_text + processed_text[end:]

        for em_tag in em_tags:
            text = em_tag.get_text()
            em_text = f"*{text}*"
            if not em_text in processed_text:
                processed_text = processed_text.replace(text, em_text)

        for strong_tag in stron_tags:
            text = strong_tag.get_text()
            strong_text = f"**{text}**"
            if not strong_text in processed_text:
                processed_text = processed_text.replace(text, strong_text)

        processed_text = re.sub(r' +', ' ', processed_text)
        processed_text = re.sub(r'\n\n+', '\n\n', processed_text)
        processed_text = processed_text.replace('\n', '<br>')
        processed_text = re.sub(r'(<br>){2,}', '<br><br>', processed_text)
        return processed_text

    def handle_table(self, tag):

        table_title = tag.caption.get_text().strip() if tag.caption else ""
        col_widths = tag.get("data-column-widths", "").split(",")
        header_rows = int(tag.get("data-header-rows", "1"))

        self.markdown += f":::{{list-table}} {table_title}\n"

        if col_widths and all(width.strip().isdigit() for width in col_widths):
            self.markdown += f":widths: {' '.join(col_widths)}\n"

        self.markdown += f":header-rows: {header_rows}\n\n"

        rows = tag.find_all("tr")
        if rows:
            headers = [header.get_text().strip()
                       for header in rows[0].find_all(["th", "td"])]
            headers = [header.replace('\n', '<br>').replace(
                '-', ' ').strip() for header in headers]
            self.markdown += "*   - " + "\n    - ".join(headers) + "\n"

            for row in rows[1:]:
                cells = [self.process_cell(cell)
                         for cell in row.find_all(["th", "td"])]
                self.markdown += "*   - " + "\n    - ".join(cells) + "\n"

        self.markdown += ":::\n"

    def convert(self, html):
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted sections
        breadcrumb = soup.find('div', id="breadcrumb-section")
        if (breadcrumb):
            breadcrumb.decompose()
        page_section = soup.find('div', class_="pageSection group")
        if (page_section):
            page_section.decompose()
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

        return self.markdown.strip()


with open('/home/guillermo/Portal/py/md_converter/test1/ARTPLATSWS/FRs-on-apps_388495531.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

    # Convert HTML to Markdown using your custom converter
    converter = HTMLToMarkdownConverter()
    markdown_content = converter.convert(html_content)

    # Write Markdown to a file
    with open('test1/source/SOLBSW/MD_TEST.md', 'w', encoding='utf-8') as file:
        file.write(markdown_content)

    print("HTML to Markdown conversion completed.")
