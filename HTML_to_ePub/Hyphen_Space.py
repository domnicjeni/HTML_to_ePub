import os
import re
import shutil
import html
import Entity_Toggle
import msvcrt as m

# Language Selection and Validation
def languageChoice(lang_list):
    def validation():
        try:
            lang_choice = int(input(f"Choose file language 1-{lang_count}: "))
            if lang_choice in range(1, lang_count + 1):
                return lang_choice
            else:
                print("Invalid Choice!\n")
                lang_choice = validation()
                return lang_choice
        except:
            print("Invalid Choice!\n")
            lang_choice = validation()
            return lang_choice

    lang_count = len(lang_list)
    n = 1
    print("\n")
    for language in lang_list:
        print(f"{n}. {language}")
        n += 1
    lang_choice = validation()
    return lang_choice


# Checking Warnings
def warning(input_file, input_content, exception_file, reference_content, lang_choice):
    warn_filename, warn_ext = os.path.splitext(input_file)
    warn_filename = warn_filename + "_warning.log"
    warning_pattern = [r"(-\s+[A-Z]+)", r"(-[a-zA-Z]+-\s+[A-Z]\w+)", r"([0-9]-\s+[0-9])", r"([A-Za-z]-\s+[0-9])", r"([0-9]+-\s+[A-Za-z])", r"(-[a-zA-Z0-9]+-\s+[a-zA-Z0-9]+)"]
    n =1
    exception_file.seek(0)
    for line in exception_file:
        if line != "\n" or line != " \n":
            exception_word = line.strip("\n")
            if lang_choice == 2:
                exception_matchs = re.findall(rf"(\w+{exception_word}[\(\[\">\s]+)", input_content, flags=re.IGNORECASE)
                input_content = re.sub(rf"({exception_word}[\(\[\">\s\.,]+)", r"<hyphen/>\1", input_content, flags=re.IGNORECASE)
            else:
                exception_matchs = re.findall(rf"([\)\]\"<\s]+{exception_word}\w+)",
                                              input_content, flags=re.IGNORECASE)
                input_content = re.sub(rf"([\)\]\"<\s]+{exception_word})", r"\1<hyphen/>", input_content,
                                       flags=re.IGNORECASE)

        if exception_matchs:
            try:
                warn_file = open(warn_filename, "x", encoding="utf8")
                warn_file.close()
            except:
                pass
            warn_file = open(warn_filename, "a", encoding="utf8")
            warn_file.write(f"{n}. Check below listed \"{exception_word}\":\n\n")
            for exception_match in exception_matchs:
                warn_file.write(f"{exception_match}\n")
            warn_file.write("\n\n")
            warn_file.close()
            n += 1
    for warning in warning_pattern:
        warn_condents = re.findall(warning, input_content, re.UNICODE)
        if warn_condents:
            try:
                warn_file = open(warn_filename, "x", encoding="utf8")
                warn_file.close()
            except:
                pass
            warn_file = open(warn_filename, "a", encoding="utf8")
            warn_file.write(f"{n}. Check below listed words without <space>:\n\n")
            for warn_condent in warn_condents:
                warn_file.write(f"{warn_condent}\n")
            warn_file.write("\n\n")
            warn_file.close()
            n += 1
    matches = re.finditer(r"(\w+)\-\s+(\w+)", input_content)
    if matches:
        try:
            warn_file = open(warn_filename, "x", encoding="utf8")
            warn_file.close()
        except:
            pass
        warn_file = open(warn_filename, "a", encoding="utf8")
        warn_file.write(f"{n}. Following words changed as Hyphen word:\n\n")
        for matach in matches:
            st1 = f"{matach.group(1)}" + f"{matach.group(2)}"
            st2 = f"{matach.group(1)}- " + f"{matach.group(2)}"
            st3 = f"{matach.group(1)}-" + f"{matach.group(2)}"
            if st3 in reference_content:
                warn_file.write(f"{st3}\n")
        warn_file.write("\n\n")
        warn_file.close()
    input_content = input_content.replace("- <hyphen/>", "-<space/>")
    input_content = input_content.replace("<hyphen/>- ", "-<space/>")
    return input_content
def entity_option(input_content):
    hexa_macthes  = len(re.findall("(&#x\w+;)", input_content, re.IGNORECASE))
    decimal_matches = len(re.findall("(&#\d+;)", input_content, re.IGNORECASE))
    sgml_matches = len(re.findall("(&[a-zA-Z]+;)", input_content, re.IGNORECASE))
    if hexa_macthes > decimal_matches and hexa_macthes > sgml_matches:
        return 5
    elif decimal_matches > hexa_macthes and decimal_matches > sgml_matches:
        return 4
    else:
        return 6



def hyphen_checking_updation(reference_content, input_content):
    input_content = re.sub(r"-\s+([A-Z0-9])", r"-\1", input_content)
    matches = re.finditer(r"\-([A-Za-z0-9]+)\-\s+([a-zA-Z0-9]+)", input_content)
    for matach in matches:
       st1 = f"{matach.group(1)}" + f"{matach.group(2)}"
       st2 = f"{matach.group(1)}- " + f"{matach.group(2)}"
       st3 = f"{matach.group(1)}-" + f"{matach.group(2)}"
       if st3 in reference_content:
           input_content = input_content.replace(st2, st3)
       else:
           input_content = input_content.replace(st2, st1)
    matches = re.finditer(r"(\w+)\-\s+(\w+)", input_content)
    for matach in matches:
        st1 = f"{matach.group(1)}" + f"{matach.group(2)}"
        st2 = f"{matach.group(1)}- " + f"{matach.group(2)}"
        st3 = f"{matach.group(1)}-" + f"{matach.group(2)}"
        if st3 in reference_content:
            input_content = input_content.replace(st2, st3)
        else:
            input_content = input_content.replace(st2, st1)
    input_content = input_content.replace("<space/>", " ")
    return input_content
# Hyphen Checking and replacing
def hyphen_replace(exception_file, reference_content, input_files, lang_choice):
    for input_file in input_files:
        print(f"\"{input_file}\" is on progress ...!")
        fhandler = open(input_file, "r", encoding="utf8")
        input_content = fhandler.read()
        fhandler.close()

        input_content = html.unescape(input_content)
        input_content = warning(input_file, input_content, exception_file, reference_content, lang_choice)
        input_content = hyphen_checking_updation(reference_content, input_content)
        fhandler = open(input_file, "wt", encoding="utf8")
        fhandler.write(input_content)
        fhandler.close()



def main():
    # Tool Starts here
    extention = [".html", ".txt", ".xhtml", ".xml", ".sgml"]
    print("######################################################################")
    print("#          This tool handle only files with following extensions     #")
    print("#          And Only (-) Hyphen <space> words                         #")
    print("#          This tool only for word file extracted from PDF with      #")
    print("#          issue in hyphen space in line end                         #")
    print("######################################################################\n")
    for only in extention:
        print(f"{only.upper()}", end=" ")

    language = ["English", "German", "Frensh"]
    lang_choice = languageChoice(language)
    print(f"The Choosen language is {language[lang_choice - 1]}!")

    while True:
        try:
            path = input("Enter file(s) path: ")
            os.chdir(path)
            break
        except FileNotFoundError:
            print("Invalid Path!")
    try:
        os.mkdir("Output")
    except FileExistsError:
        try:
            shutil.rmtree("Output")
            os.mkdir("Output")
        except PermissionError:
            print("Files are in \"Output\" folder read only mode!")
    files = os.listdir(path)
    newpath = os.path.join(path, "Output")
    try:
        for file in files:
            file_name, ext = os.path.splitext(file)
            for x in extention:
                if x == ext:
                    shutil.copy2(os.path.join(path, file), newpath)
            if language[lang_choice - 1].upper() + ".ini" == file_name.upper() + ".ini":
                exception_file = open(file, "r", encoding="utf8")

    except:
        print(f"{file} is alrady exit!")
    try:
        entity_file = open("entity.ini", "r", encoding="utf8")
    except FileNotFoundError:
        print("\"entity.ini\" is not found")
    os.chdir(newpath)
    files = os.listdir(newpath)
    input_content = ""
    for file in files:
        file_handler = open(file, "r", encoding="utf8")
        file_content = file_handler.read()
        input_content += file_content
    try:
        if exception_file:
            hyphen_replace(exception_file, input_content, files, lang_choice)
            for input_file in files:
                entity_choice = entity_option(input_content)
                Entity_Toggle.entity_replace(input_file, entity_choice, entity_file)
            exception_file.close()
            entity_file.close()
            print("\n\nPress any key to exit!")
            m.getch()
    except NameError:
        print(f"\"{language[lang_choice - 1].lower() + '.ini'}\" is missing or \"entity.ini\" is missing" )

if __name__ == '__main__':
    main()