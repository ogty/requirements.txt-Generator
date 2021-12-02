import json
import os
import platform
import inspect


# Module Extractor
class ModuleExtractor:
    def python(self, source: str) -> list:
        result, embedded = self.common(source)
        result = list(map(lambda m: "" if m in embedded else m, result))
        return result
    
    def pythonipynb(self, ipynb_data: str) -> list:
        result, embedded = self.common(ipynb_data, ipynb=True)
        result = list(map(lambda m: "" if m in embedded else m, result))
        return result
    
    def julia(self, source: str) -> list:
        result, embedded = self.common(source)
        result = list(map(lambda m: m.replace(":", "").replace(";", ""), result))
        result = list(map(lambda m: "" if m in embedded else m, result))
        return result

    def juliaipynb(self, ipynb_data: str) -> list:
        result, embedded = self.common(ipynb_data, ipynb=True)
        result = list(map(lambda m: m.replace(":", "").replace(";", ""), result))
        result = list(map(lambda m: "" if m in embedded else m, result))
        return result

    def go(self, source: str) -> list:
        result = []
        embedded = settings["languages"]["go"][2]

        splited_source = source.split()
        start = splited_source.index("import")

        if splited_source[start+1] == "(":
            count = start+2
            while True:
                module = splited_source[count]
                if module == ")":
                    break
                result.append(module)
                count += 1
        else:
            result.append(splited_source[start+1])

        result = list(map(lambda x: x.replace("\"", ""), result))
        result = list(map(lambda x: "" if x.split("/")[0] in embedded else x, result))

        return result

    def common(self, source: str, ipynb=False) -> tuple:
        if ipynb:
            ipynb_data = json.loads(source)
            source_list = []
            for cell in ipynb_data["cells"]:
                source_list += cell["source"]
            source = "".join(source_list)

        if "python" in str(inspect.stack()[1].function):
            prefixes: list = settings["languages"]["python"][1]
            embedded: list = settings["languages"]["python"][2]
        elif "julia" in str(inspect.stack()[1].function):
            prefixes: list = settings["languages"]["julia"][1]
            embedded: list = settings["languages"]["julia"][2]

        process = [f"x.startswith('{prefix}')" for prefix in prefixes]
        process_word = " or ".join(process)

        splited_source = source.split("\n")
        module_line = [x for x in splited_source if eval(process_word)]
        modules = list(map(lambda m: m.split()[1], module_line))
        result = list(map(lambda m: m.split(".")[0] if not m.startswith(".") else "", modules))

        return (result, embedded)

class Operate:
    # Get all directories in the selected directory.
    def get_dirs(self, path: str) -> None:
        base = os.listdir(path)
        files_dir = [f for f in base if os.path.isdir(os.path.join(path, f))]

        for dir in files_dir:
            self.all_dir.append(f"{path}{split_word}{dir}")
            self.get_dirs(f"{path}{split_word}{dir}")

    # Retrieves a specific file in the retrieved directory.
    def get_files(self, lang: str) -> None:
        if "ipynb" in lang:
            index = lang.find("ipynb")
            lang = f"{lang[:index]}-{lang[index:]}"

        for dir in self.all_dir:
            base = os.listdir(dir)
            files = [f for f in base if os.path.isfile(os.path.join(dir, f))]
            files = list(filter(lambda f: f.endswith(settings["languages"][lang][0]), files))
            files = list(map(lambda f: f"{dir}{split_word}{f}", files))

            self.all_file += files

class RequirementsGenerator(Operate):
    # initialize valiables and run function
    def __init__(self, path="", lang="") -> None:
        self.path = path
        self.lang = lang
        self.all_dir = [path]
        self.all_file = []

    # Main process(generate)
    def generate(self) -> None:
        self.get_dirs(self.path)
        self.get_files(self.lang)

        # Module extract
        module_extractor = ModuleExtractor()
        module_list = []

        for file_path in self.all_file:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            module_list += getattr(module_extractor, self.lang)(source)

        # Generate
        if module_list:
            module_list = list(set(module_list))
            module_list.sort()

            with open(f"{self.path}{split_word}requirements.txt", "w", encoding="utf-8") as f:
                data = "\n".join(module_list)
                f.write(data)

    def detail(self, dirs: list) -> dict:
        result = {}

        for dir in dirs:
            supported_extension = {
                "py": 0,
                "jl": 0,
                "go": 0,
                "ipynb": 0,
                "other": 0
            }
            
            if self.all_dir.count(""):
                self.all_dir.remove("")

            self.all_dir.append(dir)
            self.get_dirs(dir)

            for middle_dir in self.all_dir:
                base = os.listdir(middle_dir)
                files = [f for f in base if os.path.isfile(os.path.join(middle_dir, f))]

                for extension in supported_extension:
                    supported_extension[extension] += len(list(filter(lambda f: f.endswith(extension), files)))

            values = [v for v in supported_extension.values()]
            values_sum = sum(values)

            if values_sum > 0:
                supported_extension = {e: round((v/values_sum)*100, 2) for e, v in zip(supported_extension, values)}
            else:
                supported_extension["other"] = 100

            display_dir = dir.split(split_word)[-1]
            result[display_dir] = supported_extension
            self.all_dir.clear()
        
        return result

def generate_tree():
    # Get all directory information directly under the default path written in settings.json
    os_name = platform.system()
    user_name = os.getlogin()
    path = settings["os"][os_name].replace("<user_name>", user_name)

    # Store the retrieved information in a dict
    main_data = {"data": []}
    for data in os.walk(path):
        base_dict = {}
        
        if not ".git" in data[0]:
            dir_constract = data[0]
            dir_list = dir_constract.split(split_word)
            base_dict["id"] = dir_constract
            base_dict["text"] = dir_list[-1]
            base_dict["parent"] = split_word.join(dir_list[:-1])

            if path == data[0]:
                base_dict["parent"] = "#"

            main_data["data"].append(base_dict)

    with open(f"{os.getcwd()}{split_word}static{split_word}tree.json", "w", encoding="utf-8") as f:
        json.dump(main_data, f, ensure_ascii=False, indent=2)

split_word = "\\" if platform.system() == "Windows" else "/"
data = open(f"{os.getcwd()}{split_word}static{split_word}settings.json", "r")
settings = json.load(data)
