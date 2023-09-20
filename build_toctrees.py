import bs4
import re
import urllib.parse

def extract_toc_structure(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = bs4.BeautifulSoup(file, 'html.parser')

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

            toc_structure.append({'text': text, 'link': url, 'indentation': indentation})

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

    print(toc_tree)
    return toc_tree

def convert_to_valid_url(input_string):
    url_string = re.sub(r' +', ' ', input_string.replace('\n', ' ')).replace(' ', '_')
    url_string = urllib.parse.quote(url_string, safe=':()?&=#')
    return url_string.replace('.html', '.md')

def write_toc_to_rst(toc_tree, file_path):
    with open(file_path, 'w', encoding='utf-8') as rst_file:
        write_toc_tree_to_rst(toc_tree, rst_file)

def write_toc_tree_to_rst(toc_tree, rst_file, depth=0):
    if depth == 0:
        title = 'ARTPLATSWS'
        rst_file.write(f"{title}\n")
        rst_file.write("=" * len(title) + "\n\n")
        rst_file.write(".. toctree::\n")
        rst_file.write("   :hidden:\n\n")

    for item in toc_tree:
        rst_file.write('   ' * (depth+1) + f"{item['text']} <{item['link']}>\n")
        if 'subitems' in item:
            write_toc_tree_to_rst(item['subitems'], rst_file, depth + 1)


if __name__ == "__main__":
    html_file = '/home/guillermo/Portal/py/md_converter/test1/ARTPLATSWS/index.html'
    toc_structure = extract_toc_structure(html_file)
    toc_tree = create_toc_tree(toc_structure)
    toctree_rst_file = '/home/guillermo/Portal/py/md_converter/test1/source/ARTPLATSWS/index.rst'
    write_toc_to_rst(toc_tree, toctree_rst_file)
    print('Done.')
