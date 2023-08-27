import os
import shutil
import re
import msvcrt as m
from bs4 import BeautifulSoup
from time import sleep
def error_log(type, matches, file, currentfile_content, log_path, error_file_name):
    try:
        error_log = os.open(f"{log_path}{error_file_name}_error.log", "x", encoding="utf8")
        error_log.close()
    except:
        pass
    error_logname = f"{log_path}{error_file_name}_error.log"
    if matches:
        error_logflie = open(error_logname, "a", encoding="utf8")
        error_logflie.write(f'\n{type} are not converted in "{file}":\n')
        for i, match in enumerate(matches):
            error_logflie.write(f"{i+1}. {match}\n")
        error_logflie.close()


def Hexa_errorlog(file, currentfile_content):
    matches = re.findall("&#x\w+;", currentfile_content, re.IGNORECASE)
    if matches:
        error_log("Hexa-decimal Entities", matches, file, currentfile_content)


def decima_errorlog(file, currentfile_content):
    matches = re.findall("&#\d+;", currentfile_content, re.IGNORECASE)
    if matches:
        error_log("Decimal Entities", matches, file, currentfile_content)


def SGML_errorlog(file, currentfile_content):
    matches = re.findall("&\w+;", currentfile_content, re.IGNORECASE)
    if matches:
        error_log("SGML Entities", matches, file, currentfile_content)


def UTF8_Char_errorlog(file, currentfile_content, log_path, error_file_name):
    matches = re.findall(r"[^\x00-\x7F]+", currentfile_content, re.IGNORECASE)
    if matches:
        error_log("UTF8 Characters", matches, file, currentfile_content, log_path, error_file_name)


def hexa_replace(text_value, replace_value, entity_file, currentfile_content, file):
    currentfile_content = currentfile_content.replace("&#x00A0;", "&#160;")
    currentfile_content = currentfile_content.replace("&#x00a0;", "&#160;")
    currentfile_content = currentfile_content.replace("&#x0A0;", "&#160;")
    currentfile_content = currentfile_content.replace("&#xA0;", "&#160;")
    currentfile_content = currentfile_content.replace("&#x0a0;", "&#160;")
    currentfile_content = currentfile_content.replace("&#xa0;", "&#160;")
    for eachline in entity_file:
        if '\t' in eachline:
            entity = eachline.strip().split("\t")
            patern = re.compile(re.escape(entity[text_value]), re.IGNORECASE)
            currentfile_content = patern.sub(entity[replace_value], currentfile_content)

            for i in range(0, 2):
                entity[text_value] = entity[text_value].replace("&#x0", "&#x")
                patern = re.compile(re.escape(entity[text_value]), re.IGNORECASE)
                currentfile_content = patern.sub(entity[replace_value], currentfile_content)
        else:
            pass
    Hexa_errorlog(file, currentfile_content)
    return currentfile_content


def Junk_SGML_Decimal_replace(text_value, replace_value, entity_file, currentfile_content, file):
    for eachline in entity_file:
        if '\t' in eachline:
            entity = eachline.split("\t")
            entity[text_value] = entity[text_value].strip()
            entity[replace_value] = entity[replace_value].strip()
            currentfile_content = currentfile_content.replace(entity[text_value], entity[replace_value])
        else:
            pass
    return currentfile_content


def entity_replace(file, n, entity_file, log_path, error_file_name):
    currentfile = open(file, "r", encoding='utf8')
    currentfile_content = currentfile.read()
    currentfile.close()
    if n == 1:
        entity_file.seek(0)
        currentfile_content = hexa_replace(2, 1, entity_file, currentfile_content, file)
    elif n == 2:
        entity_file.seek(0)
        currentfile_content = hexa_replace(2, 0, entity_file, currentfile_content, file)
    elif n == 3:
        entity_file.seek(0)
        currentfile_content = hexa_replace(2, 3, entity_file, currentfile_content, file)
    elif n == 4:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(3, 1, entity_file, currentfile_content, file)
        currentfile_content = re.sub(r'\u00A0', '&#160;', currentfile_content)
        UTF8_Char_errorlog(file, currentfile_content, log_path, error_file_name)
    elif n == 5:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(3, 2, entity_file, currentfile_content, file)
        currentfile_content = re.sub(r'\u00A0', '&nbsp;', currentfile_content)
        UTF8_Char_errorlog(file, currentfile_content, log_path, error_file_name)
    elif n == 6:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(3, 0, entity_file, currentfile_content, file)
        currentfile_content = re.sub(r'\u00A0', '&#x00A0;', currentfile_content)
        UTF8_Char_errorlog(file, currentfile_content, log_path, error_file_name)
    elif n == 7:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(1, 2, entity_file, currentfile_content, file)
        currentfile_content = currentfile_content.replace("&#160;", "&#x00A0;")
        currentfile_content = currentfile_content.replace("&#38;", "&#x0026;")
        currentfile_content = currentfile_content.replace("&#60;", "&#x003C;")
        currentfile_content = currentfile_content.replace("&#62;", "&#x003E;")

        decima_errorlog(file, currentfile_content)
    elif n == 8:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(1, 0, entity_file, currentfile_content, file)
        currentfile_content = currentfile_content.replace("&#160;", "&nbsp;")
        currentfile_content = currentfile_content.replace("&#38;", "&amp;")
        currentfile_content = currentfile_content.replace("&#60;", "&lt;")
        currentfile_content = currentfile_content.replace("&#62;", "&gt;")
        decima_errorlog(file, currentfile_content)
    elif n == 9:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(1, 3, entity_file, currentfile_content, file)
        decima_errorlog(file, currentfile_content)
    elif n == 10:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(0, 2, entity_file, currentfile_content, file)
        currentfile_content = currentfile_content.replace("&nbsp;", "&#x00A0;")
        currentfile_content = currentfile_content.replace("&amp;", "&#x0026;")
        currentfile_content = currentfile_content.replace("&lt;", "&#x003C;")
        currentfile_content = currentfile_content.replace("&gt;", "&#x003E;")
        SGML_errorlog(file, currentfile_content)
    elif n == 11:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(0, 1, entity_file, currentfile_content, file)
        currentfile_content = currentfile_content.replace("&nbsp;", "&#160;")
        currentfile_content = currentfile_content.replace("&amp;", "&#38;")
        currentfile_content = currentfile_content.replace("&lt;", "&#60;")
        currentfile_content = currentfile_content.replace("&gt;", "&#62;")
        SGML_errorlog(file, currentfile_content)
    elif n == 12:
        entity_file.seek(0)
        currentfile_content = Junk_SGML_Decimal_replace(0, 3, entity_file, currentfile_content, file)
        SGML_errorlog(file, currentfile_content)

    currentfile = open(file, "w", encoding='utf8')
    currentfile.write(currentfile_content)
    currentfile.close()
    return currentfile_content



def userchoice_validation(n):
    while True:
        try:
            choice = int(input("Enter your choice: "))
            if choice in range(1, n + 1):
                return choice
                break
            else:
                print("Invalid Choice")
                choice = userchoice_validation(12)
        except:
            print("Invalid!")



def main():
    extention = [".html", ".txt", ".xhtml", ".xml", ".sgml"]
    print("This tool handle only files with following extensions: ")
    for only in extention:
        print(f"{only.upper()}", end=" ")

    while True:
        try:
            path = input("\n\nEnter path: ")
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

    print("\n\t 1. Hexa Decimal to Decimal\n\t 2. Hexa Decimal to SGML\n\t 3. Hexa Decimal to UTF8 Character\n\t"
          " 4. Junk to Decimal\n\t 5. Junk to Hexa Decimal\n\t 6. Junk to SGML\n\t"
          " 7. Decimal to Hexa Decimal\n\t 8. Decimal to SGML\n\t 9. Decimal to UTF8 Character\n\t"
          "10. SGML to Hexa Decimal\n\t11. SGML to Decimal\n\t12. SGML to UTF8 Character\n")
    userchoice = userchoice_validation(12)

    try:
        entities = open("entity.ini", "r", encoding="utf8")
        # entities = ini_file.read()
        files = os.listdir(path)
        newpath = os.path.join(path, "Output")

        for file in files:
            filename, ext = os.path.splitext(file)
            for x in extention:
                if x == ext:
                    try:
                        shutil.copy2(os.path.join(path, file), newpath)
                    except FileExistsError:
                        print(f"{file} already exit!")
                    break
        os.chdir(newpath)
        files = os.listdir(newpath)
        log_path = os.getcwd()
        for file in files:
            error_file_name = file
            print(f"Processing... \"{file}\"")
            entity_replace(file, userchoice, entities, log_path, error_file_name)
        entities.close()
        print("\nCompleted....!\n")
        sleep(1)
    except FileNotFoundError:
        print("\"entity.ini\" file is missing in the current path!")
if __name__ == "__main__":
   main()