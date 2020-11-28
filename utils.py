import os
import requests
import sys

main_file = "main.py"
checkers_file = "checkers.py"

def wait_for_internet(prompt=None):
    printed_once = False
    while True:
        try:
            requests.get("https://www.google.com/")
        except requests.exceptions.ConnectionError:
            if prompt:
                if not printed_once:
                    print(prompt)
                    printed_once = True
        else:
            os.system("cls")
            break


def wait_key(prompt=None, end='\n'):
    """ Wait for a key press on the console and return it. """

    if prompt:
        print(prompt, end=end)

    result = None
    if os.name == 'nt':
        import msvcrt
        result = msvcrt.getch()
    else:
        import termios
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        try:
            result = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return result


def see_in_browser(html_text, file="test.html"):
    with open(file, 'w', encoding='utf8') as f:
        f.write(html_text)
    os.system(file)


def restart(fp, py_executable="python"):
    """restart the caller python script of this func"""
    os.system(f"{py_executable} {fp}")
    exit(0)


def install(key, checker_name, url_structure, checker):
    _install_at_main(key, checker_name, checker)
    _install_at_checkers(checker_name, url_structure, checker)
    print(f"Installed {checker_name} with key={key} successfully.")


def _install_at_checkers(checker_name, url_structure, checker):
    with open('test.py', 'r') as f:
        lines = f.readlines()

    first = 0
    last = 0
    for i, line in enumerate(lines):
        if "def checker(url):" in line:
            first = i + 1
        if "return" in line:
            last = i + 1
            break
    raw_def_lines = [f"def {checker_name}(url):\n", f'    """ {url_structure} """\n\n']
    raw_def_lines.extend(lines[first:last])
    refined_def_lines = [line for line in raw_def_lines if '    #' not in line and line != '\n']

    with open(checkers_file, 'r', encoding='utf8') as a:
        codes = a.read()
    with open(checkers_file, 'w', encoding='utf8') as f:
        codes += "\n\n" + ''.join(refined_def_lines)
        f.write(codes)


def _install_at_main(key, checker_name, checker):

    def create_checker_str(checkers):
        string = "installed_checkers = {\n"
        for web_key, func in checkers.items():
            if web_key == key:
                string += f'    "{web_key}": {checker_name},\n'
            else:
                string += f'    "{web_key}": {func.__name__},\n'
        string += "}\n"
        return string

    from main import installed_checkers
    installed_checkers[key] = checker

    # replace old literal codes with new codes
    with open(main_file, 'r') as f:
        lines = f.readlines()
    first_line_index = 0
    last_line_index = 0
    for i, line in enumerate(lines):
        if "from checkers import *" in line:
            first_line_index = i + 1
        if '}' in line:
            last_line_index = i + 1
            break

    checker_str = create_checker_str(installed_checkers)
    new_code_lines = lines[:first_line_index]
    new_code_lines.append(checker_str)
    new_code_lines.extend(lines[last_line_index:])
    with open(main_file, 'w') as f:
        f.writelines(new_code_lines)


def compare(checker, info):
    """
    :param checker: function for each website that returns int(all eps on site), str(link to latest ep)
    :param info: info is read from a line in {gv.info_file}
        info = {
            'url': str,
            'ep': int or None,
            'title': str
        }
    :return: CompareResult if found new ep else None
    """

    try:
        current_ep, current_link = checker(info['url'])
    except requests.exceptions.ConnectionError:
        input("Check your internet, then try again.\n"
              "Enter to exit\n")
        exit(1)
    except:
        print(f"cannot check {info['title']}, ({info['url']}) checker = {checker.__name__}")
        return None
    else:
        saved_ep = info['ep']
        title = info['title']
        if saved_ep is None:
            return CompareResult(info['url'], title, current_ep)
        else:
            if saved_ep != current_ep:
                return CompareResult(info['url'], title, current_ep, current_link, saved_ep)
            else:
                return None


class CompareResult:
    def __init__(self, url, title, current_ep, current_link=None, old_ep=None):
        self.title = title
        self.current_ep = current_ep
        self.url = url
        self.current_link = current_link
        self.old_ep = old_ep

    def is_found(self):
        if self.old_ep:
            return self.old_ep != self.current_ep
        else:
            return False

    def __repr__(self):
        return f"{self.__class__.__name__}(title='{self.title}', current_ep={self.current_ep}, " \
               f"current_link='{self.current_link}', old_ep={self.old_ep})"
