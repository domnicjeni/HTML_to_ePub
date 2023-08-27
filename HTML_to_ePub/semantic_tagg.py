import string

from epubcheck import EpubCheck
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from tkinter import PhotoImage
import requests
import threading
import xml.etree.ElementTree as Et
from lxml import etree
from bs4 import BeautifulSoup, Tag
import os
import zipfile
import shutil
import re
import Entity_Toggle
import Hyphen_Space
import pandas
from datetime import datetime

from Tools.scripts.objgraph import flat
from tkinter import font



# Tag mapping subfunction
def attribute_squence(new_attribute, file_content):
    file_array = file_content.split("\n")
    n = 1
    new_filecontent = ""
    for item in file_array:
        if "\[\[seq\]\]" in item:
            item = item.replace("\[\[seq\]\]", f"{n}".zfill(4))
            n += 1
        new_filecontent += f"{item}\n"
    return new_filecontent


def multiple_attribute(add_p_attr, add_p_attr_val):
    add_p_attr_group = add_p_attr.split("|")
    add_p_attr_val_group = add_p_attr_val.split("|")
    new_attrb = ""
    attrb_count = len(add_p_attr_val_group)
    for i in range(attrb_count):
        new_attrb = new_attrb + " " + f'{add_p_attr_group[i]}="{add_p_attr_val_group[i]}"'
    return new_attrb


def replace_element(match, file_content):
    find_tag, find_tag_selfclose, find_attrib, find_prefix, find_classname = match[0], match[1], match[2], match[3], match[4]
    replace_htmltag, add_attr, attr_val, newtag_self_close = match[5], match[6], match[7], match[8]
    add_parent, add_p_attr, add_p_attr_val = match[9], match[10], match[11]
    add_child, add_c_attr, add_c_attr_val, child_self_close = match[12], match[13], match[14], match[15]
    content_before, content_after = match[16], match[17]
    find_tag = "p" if find_tag == "" else find_tag
    find_attrb = "class" if find_attrib == "" else find_attrib
    replace_htmltag = "p" if replace_htmltag == "" else replace_htmltag
    find_element = f'{find_prefix}[^<"]*' if find_classname == "" else find_classname
    new_attribute = f' {add_attr}="{attr_val}"' if "|" not in add_attr else multiple_attribute(add_attr, attr_val)
    new_tag = replace_htmltag if attr_val == "" else f"{replace_htmltag}\n{new_attribute}"


    newparent_attribute = f' {add_p_attr}="{add_p_attr_val}"' if "|" not in add_p_attr else multiple_attribute(
        add_p_attr, add_p_attr_val)
    newparent_tag = add_parent if add_p_attr == "" else f"{add_parent}\n{newparent_attribute}"

    newchild_attribute = f' {add_c_attr}="{add_c_attr_val}"' if "|" not in add_c_attr else multiple_attribute(
        add_c_attr, add_c_attr_val)
    newchild_tag = add_child if add_c_attr == "" else f"{add_child}\n{newchild_attribute}"

    if add_parent and add_child:
        if child_self_close:
            replace_tag = fr'<{newparent_tag}>\n<{new_tag}\1{find_attrb}="\2"\3><{newchild_tag}/> \4</{replace_htmltag}>\n</{add_parent}>'
        else:
            replace_tag = fr'<{newparent_tag}>\n<{new_tag}\1{find_attrb}="\2"\3><{newchild_tag}>\4</{add_child}></{replace_htmltag}>\n</{add_parent}>'
    elif add_parent:
        if find_tag_selfclose.upper() == 'Y' or find_tag_selfclose.upper() == 'YES' or find_tag_selfclose.upper() == 'TRUE':
            replace_tag = fr'<{newparent_tag}>\n<{new_tag}\1{find_attrb}="\2"\3>\n</{add_parent}>'
        else:
            replace_tag = fr'<{newparent_tag}>\n<{new_tag}\1{find_attrb}="\2"\3>\4</{replace_htmltag}>\n</{add_parent}>'
    elif add_child:
        if child_self_close:
            replace_tag = fr'<{new_tag}\1{find_attrb}="\2"\3><{newchild_tag}/> \4</{replace_htmltag}>'
        else:
            replace_tag = fr'<{new_tag}\1{find_attrb}="\2"\3><{newchild_tag}>\4</{add_child}></{replace_htmltag}>'
    elif find_tag_selfclose.upper() == 'Y' or find_tag_selfclose.upper() == 'YES' or find_tag_selfclose.upper() == 'TRUE':
        replace_tag = fr'<{new_tag}\1{find_attrb}="\2"\3>'
    else:
        replace_tag = fr'<{new_tag}\1{find_attrb}="\2"\3>\4</{replace_htmltag}>'
    if find_tag_selfclose.upper() == 'Y' or find_tag_selfclose.upper() == 'YES' or find_tag_selfclose.upper() == 'TRUE':

        file_content = re.sub(fr"<{find_tag}([^<]*){find_attrb}=\"({find_element})\"([^<]*)>",rf'{replace_tag}', file_content, flags=re.IGNORECASE)
    else:
        file_content = re.sub(
            fr"<{find_tag}([^<]*){find_attrb}=\"({find_element})\"([^<]*)>((?:(?!<\/{find_tag}>).)*(?=<\/{find_tag}>))<\/{find_tag}>",
            rf'{replace_tag}', file_content, flags=re.IGNORECASE)
    sequance_check = [new_attribute, newparent_attribute, newchild_attribute]
    newline_check = [replace_htmltag, add_parent, add_child]
    for item in sequance_check:
        if "\[\[seq\]\]" in item:
            file_content = attribute_squence(item, file_content)
    for item in newline_check:
        if item:
            file_content = file_content.replace(f'<{item}\n', f'<{item}')
    return file_content


def multiple_parent(parent_tag):
    parent_tag_group = parent_tag.split("|")
    new_tag = ""
    attrb_count = len(parent_tag_group)
    for i in range(attrb_count):
        if i == 0:
            new_tag = f'</{parent_tag_group[i]}>'
        else:
            new_tag = f'{new_tag}' + "|" + f'</{parent_tag_group[i]}>'
    return new_tag


def nested_opentag(match, file_content):
    find_tag, find_attrib, prefix, find_classname = match[0], match[1], match[2], match[3]
    nest_tag, nest_attrib, nest_attr_val, = match[4], match[5], match[6]
    nested_type, nested_level, nest_parent = match[7], match[8], match[9]
    find_tag = "p" if find_tag == "" else find_tag
    fint_att = f'{prefix}([^<"]*)' if find_classname == "" else find_classname
    find_attrib = "class" if find_attrib == "" else find_attrib
    new_attribute = f' {nest_attrib}="{nest_attr_val}"' if "|" not in nest_attrib else multiple_attribute(nest_attrib,
                                                                                                          nest_attr_val)

    open_nest_tag = f"{nest_tag}1" if nested_level == "" else f"{nest_tag}" + f"{nested_level}"
    new_tag = open_nest_tag if nest_attr_val == "" else f"{open_nest_tag}\n{new_attribute}"
    file_content = re.sub(rf"<{find_tag}", f"\n<{find_tag}", file_content, flags=re.IGNORECASE)
    file_content = re.sub(rf"([\n\n]+)", f"\n", file_content, flags=re.IGNORECASE)
    file_array = file_content.split("\n")
    for x in range(len(file_array)):
        open_tag = re.findall(rf'<{find_tag}([^<]*){find_attrib}="({fint_att})"([^<]*)>', file_array[x],
                              flags=re.IGNORECASE)
        if open_tag:
            file_array[x] = re.sub(rf'<{find_tag}([^<]*){find_attrib}="({fint_att})"([^<]*)>',
                                   rf'<{new_tag}>\n<{find_tag}\1{find_attrib}="\2"\3>', file_array[x],
                                   flags=re.IGNORECASE)
    file_content = ""
    for line in file_array:
        file_content += f"{line}\n"
    if "\[\[seq\]\]" in new_attribute:
        file_content = attribute_squence(new_attribute, file_content)
    if open_nest_tag:
        file_content = file_content.replace(f'<{open_nest_tag}\n', f'<{open_nest_tag}')
    return file_content


def nested_closetag(match, file_content):
    nest_tag, nest_attrib, nest_attr_val, = match[4], match[5], match[6]
    nested_type, nested_level, nest_parent = match[7], match[8], match[9]
    nest_parent = f'</{nest_parent}>' if "|" not in nest_parent else multiple_parent(nest_parent)
    open_nest_tag = f"{nest_tag}1" if nested_level == "" else f"{nest_tag}{nested_level}"
    close_tag = f"</{open_nest_tag}>"
    new_file_array = file_content.split("\n")
    line = 0
    need_to_close = 0

    for x in range(len(new_file_array)):
        if need_to_close == 0 and line < len(new_file_array):
            find_tag_possible = re.findall(rf'(<{open_nest_tag})', new_file_array[line],
                                           flags=re.IGNORECASE)
            if find_tag_possible:
                need_to_close = 1
                line += 1
        if find_tag_possible and need_to_close == 1 and line < len(new_file_array):
            close_tag_possible = re.findall(rf"(<{open_nest_tag}|{nest_parent})", new_file_array[line],
                                            flags=re.IGNORECASE)
            if close_tag_possible and need_to_close == 1:
                new_file_array[line] = re.sub(rf"(<{open_nest_tag}|{nest_parent})", rf"{close_tag}\n\1",
                                              new_file_array[line],
                                              flags=re.IGNORECASE)
                need_to_close = 0
                line -= 1
        line += 1
    file_content = ""
    for line in new_file_array:
        file_content += f"{line}\n"
    return file_content


def nesting(matches, file_content):
    for match in matches:
        file_content = nested_opentag(match, file_content)
    completed_level = []
    for match in matches:
        nest_tag = match[4]
        nested_level = match[8]
        open_nest_tag = f"{nest_tag}1" if nested_level == "" else f"{nest_tag}{nested_level}"
        if open_nest_tag not in completed_level:
            file_content = nested_closetag(match, file_content)
            completed_level.append(open_nest_tag)
    return file_content


def footnote(match, file_content):
    find_tag, find_attrib, find_att_value_prefix, find_att_value = match[0], match[1], match[2], match[3]
    group_tag, gt_attrib, gt_attrib_value = match[4], match[5], match[6]
    to_move_under, move_before, move_after = match[7], match[8], match[9]
    find_tag = "p" if find_tag == "" else find_tag
    find_attrib = "class" if find_attrib == "" else find_attrib
    find_att_value = f"({find_att_value})" if find_att_value_prefix == "" else f"({find_att_value_prefix})([^\"]*)"
    new_attribute = f' {find_attrib}="{find_att_value}"'
    new_tag = find_tag if find_att_value == "" else rf"{find_tag}([^<]*){new_attribute}"
    replace_tag = rf'<1{find_tag}\1{find_attrib}="\2"\3>' if find_att_value_prefix == "" else rf'<1{find_tag}\1 {find_attrib}="\2\3"\4>'
    group_tag_attribute = f' {gt_attrib}="{gt_attrib_value}"' if "|" not in gt_attrib else multiple_attribute(
        gt_attrib, gt_attrib_value)
    newgroup_tag = group_tag if gt_attrib == "" else f"<{group_tag}\n{group_tag_attribute}>"

    newgroupclose_tag = f"</{group_tag}>"
    file_content = file_content.replace(f"<{find_tag}", f"\n<{find_tag}")
    file_content = re.sub(f"(\n\n+)", f"\n", file_content)
    file_array = file_content.split("\n")
    new_footnote = ""

    n = 0
    for line in file_array:
        file_array[n] = re.sub(rf"<{new_tag}([^<]*)>", rf"{replace_tag}", line, flags=re.IGNORECASE)
        n += 1
    n = 0
    for line in file_array:
        footnotes = re.findall(rf"(<1(?:(?!<\/{find_tag}>).*(?=<\/{find_tag}>))<\/{find_tag}>)", line,
                               flags=re.IGNORECASE)
        file_array[n] = re.sub(rf"(<1(?:(?!<\/{find_tag}>).*(?=<\/{find_tag}>))<\/{find_tag}>)", "", line,
                               flags=re.IGNORECASE)
        if footnotes:
            for note in footnotes:
                new_footnote += f"{note}\n"
        footnote_content = f"{newgroup_tag}\n{new_footnote}\n{newgroupclose_tag}"

        if to_move_under != "":
            if "|" in to_move_under:
                to_move_under_array = to_move_under.split("|")
                for x in to_move_under_array:
                    if x in line:
                        if new_footnote:
                            file_array[n] = re.sub(rf"</{x}>", rf"{footnote_content}\n</{x}>", line,
                                                   flags=re.IGNORECASE)
                            new_footnote = ""
            else:
                if to_move_under in line:
                    if new_footnote:
                        file_array[n] = re.sub(rf"</{to_move_under}>", rf"{footnote_content}\n</{to_move_under}>", line,
                                               flags=re.IGNORECASE)
                        new_footnote = ""
        elif move_before != "":
            if "|" in move_before:
                move_before_array = move_before.split("|")
                for x in move_before_array:
                    if f"<{x}" in line:
                        if new_footnote:
                            file_array[n] = re.sub(rf"<{x}([^<]*)>", rf"{footnote_content}\n<{x}\1>", line,
                                                   flags=re.IGNORECASE)
                        new_footnote = ""
            else:
                if f"<{move_before}" in line:
                    if new_footnote:
                        file_array[n] = re.sub(rf"<{move_before}([^<]*)>", rf"{footnote_content}\n<{move_before}\1>",
                                               line,
                                               flags=re.IGNORECASE)
                new_footnote = ""
        elif move_after != "":
            if "|" in move_after:
                move_after_array = move_after.split("|")
                for x in move_after_array:
                    if f"</{x}>" in line:
                        if new_footnote:
                            file_array[n] = re.sub(rf"</{x}>", rf"</{x}>\n{footnote_content}", line,
                                                   flags=re.IGNORECASE)
                            new_footnote = ""
            else:
                if f"</{move_after}>" in line:
                    if new_footnote:
                        file_array[n] = re.sub(rf"</{move_after}>", rf"</{move_after}>\n{footnote_content}", line,
                                               flags=re.IGNORECASE)
                        new_footnote = ""

        n += 1
    file_content = ""
    for line in file_array:
        file_content += f"{line}\n"
    if "\[\[seq\]\]" in new_attribute:
        file_content = attribute_squence(new_attribute, file_content)
    if "\[\[seq\]\]" in group_tag_attribute:
        file_content = attribute_squence(group_tag_attribute, file_content)
    if group_tag:
        file_content = file_content.replace(f'<{group_tag}\n', f'<{group_tag}')
    file_content = file_content.replace(f"<1{find_tag}", f"<{find_tag}")
    return file_content


def clean_up(match, file_content, input_FileSplit):
    nest_tag, nest_attrib, nest_attr_val, = match[4], match[5], match[6]
    if input_FileSplit == "Level 1":
        file_content = file_content.replace(f"<{nest_tag}1", f"\n<!--File Split-->\n<{nest_tag}1")
    elif input_FileSplit == "Level 2":
        file_content = file_content.replace(f"<{nest_tag}1", f"\n<!--File Split-->\n<{nest_tag}1")
        file_content = file_content.replace(f"<{nest_tag}2", f"\n<!--File Split-->\n<{nest_tag}2")
    elif input_FileSplit == "Level 3":
        file_content = file_content.replace(f"<{nest_tag}1", f"\n<!--File Split-->\n<{nest_tag}1")
        file_content = file_content.replace(f"<{nest_tag}2", f"\n<--File Split-->\n<{nest_tag}2")
        file_content = file_content.replace(f"<{nest_tag}3", f"\n<!--File Split-->\n<{nest_tag}3")
    file_content = re.sub(rf"<{nest_tag}\d+", rf"<{nest_tag}", file_content, flags=re.IGNORECASE)
    file_content = re.sub(rf"</{nest_tag}\d+>", rf"</{nest_tag}>", file_content, flags=re.IGNORECASE)
    file_content = re.sub(r"(\n\n+)", r"\n", file_content, flags=re.IGNORECASE)
    return file_content


def listgroup_open(file_content, match, x, visited):
    find_tag = "p" if match[0] == "" else match[0]
    find_attrib = "class" if match[1] == "" else match[1]
    find_prefix = match[2]
    list_attrib = "" if match[8] == "" else f'{match[8]}="{match[9]}"'
    list_attrib = list_attrib if "|" not in list_attrib else multiple_attribute(match[8], match[9])
    list_findtag = f'list{x}-{match[7]}'
    list_tag = f'<list{x}-{match[7]}>' if list_attrib == "" else f'<list{x}-{match[7]} {list_attrib}>'
    if find_prefix and not visited:
        find_element = f'(<{find_tag}([^<"]*){find_attrib}="{find_prefix}([^<"]*)"([^<"]*)>(?:(?!<\/{find_tag}>).)*(?=<\/{find_tag}>)<\/{find_tag}>)'
        repl_element = rf'{list_tag}\n\1\n</{list_findtag}>'
        file_content = re.sub(find_element, repl_element, file_content, flags=re.IGNORECASE)
        file_content = file_content.replace(f"\n</{list_findtag}>\n{list_tag}", "")

    find_att_value = match[3]
    listItem_attrib = "" if match[5] == "" else f'{match[5]}="{match[6]}"'
    listItem_attrib = listItem_attrib if "|" not in listItem_attrib else multiple_attribute(match[5], match[6])
    listItem_findtag = f'{match[4]}{x}'
    listItem_tag = f'<{listItem_findtag}>' if listItem_attrib == "" else f'<{match[4]}{x} {listItem_attrib}>'
    find_element = rf'<{find_tag}([^<"]*){find_attrib}="{find_att_value}"([^<"]*)>'
    repl_element = rf'{listItem_tag}<{find_tag}\1{find_attrib}="{find_att_value}"\2>'
    file_content = re.sub(find_element, repl_element, file_content, flags=re.IGNORECASE)

    return file_content


def listgroup_open1(file_content, maxlevel):
    file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
    file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
    file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
    file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
    file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
    file_array = file_content.split("\n")
    nestClose = False
    parCheck = False
    list_Type = ""
    parentList = ""
    for x in range(maxlevel, 0, -1):
        if x - 1 > 0:
            for y in range(x - 1, 0, -1):
                n = 0
                for line in file_array:
                    seacrhes = re.findall(rf'</list{y}\-(\w+)><list{x}\-', line, re.IGNORECASE)
                    if seacrhes:
                        for sr in seacrhes:
                            list_Type = sr
                            file_array[n] = re.sub(rf'</list{y}\-(\w+)><list{x}\-', rf'<list{x}-', line,
                                                   flags=re.IGNORECASE)
                            nestClose = True
                    if nestClose and f"</list{x}-" in file_array[n]:
                        nestClose = False
                        file_array[n] = re.sub(rf'<\/list{x}\-(\w+)>', rf'</list{x}-\1>\n</list{y}-{list_Type}>', line,
                                               flags=re.IGNORECASE)
                        parCheck = True
                        file_array[n] = f"{file_array[n]}{file_array[n + 1]}"
                        file_array.pop(n + 1)
                    for reLine in range(n - 1, 0, -1):
                        if parCheck and f"<list{y}-{list_Type}" in file_array[reLine]:
                            find_parent_element = re.findall(rf"(<list{y}-{list_Type}[^<]*)", file_array[reLine],
                                                             flags=re.IGNORECASE)
                            for find in find_parent_element:
                                parentList = find
                            parCheck = False
                            break
                    if parentList:
                        file_array[n] = file_array[n].replace(f"</list{y}-{list_Type}>{parentList}", "")
                        parentList = ""
                    n += 1
    file_content = ""
    for line in file_array:
        file_content += f"{line}\n"
    return file_content


def listgroup_close(file_content, match, x):
    file_array = file_content.split("\n")
    n = 0
    close = 0
    find_tag = f"<{match[4]}{x}"
    for line in file_array:
        if close == 0 and find_tag in file_array[n]:
            close = 1
            n += 1
        if close == 1:
            if find_tag in file_array[n]:
                close = 0
                file_array[n] = file_array[n].replace(f"{find_tag}", f"</{match[4]}{x}>\n{find_tag}")
                n -= 1
            elif f"</list{x}-" in file_array[n]:
                close = 0
                file_array[n] = file_array[n].replace(f"</list{x}-", f"</{match[4]}{x}>\n</list{x}-")
                n -= 1
        n += 1
    file_content = ""
    for line in file_array:
        file_content += f"{line}\n"
        file_content = file_content.replace(f"</{match[4]}{x}>", f"</{match[4]}>")
        file_content = file_content.replace(f"<{match[4]}{x}", f"<{match[4]}")
        file_content = file_content.replace(f"<list{x}-", f"<")
        file_content = file_content.replace(f"</list{x}-", f"</")
    return file_content


def string_replace(match, file_content):
    find_what, replace_with, case_senstive, regex = rf"{match[0]}", rf"{match[1]}", match[2], match[3]
    isRegex = regex if regex else "no"
    regex_find = ["\[", "\]"]
    regex_replace = ["[", "]"]
    if "'" in find_what or "'" in replace_with:
        find_what = find_what.replace("'", '"')
        replace_with = replace_with.replace("'", '"')
    for n in range(len(regex_find)):
        find_what = find_what.replace(f"{regex_find[n]}", f"{regex_replace[n]}")
        replace_with = replace_with.replace(f"{regex_find[n]}", f"{regex_replace[n]}")
    if isRegex.lower() != "no":
        if case_senstive.lower() == "no":
            file_content = re.sub(rf"{find_what}", rf"{replace_with}", file_content, flags=re.IGNORECASE)
        else:
            file_content = re.sub(rf"{find_what}", rf"{replace_with}", file_content)
    else:
        if case_senstive.lower() == "no":
            file_content = re.sub(re.escape(find_what), replace_with, file_content, flags=re.IGNORECASE)
        else:
            file_content = file_content.replace(find_what, replace_with)
    if "[[seq]]" in replace_with:
        file_content = file_content.replace("[[seq]]", "\[\[seq\]\]")
        file_content = file_content.replace(replace_with, f"\n{replace_with}")
        file_content = attribute_squence(replace_with, file_content)
        file_content = file_content.replace(f"\n{replace_with}", replace_with)

    return file_content

def romanNumberGenartion(num):
    roman_numerals = {
        1000: 'm',
        900: 'cm',
        500: 'd',
        400: 'cd',
        100: 'c',
        90: 'xc',
        50: 'l',
        40: 'xl',
        10: 'x',
        9: 'ix',
        5: 'v',
        4: 'iv',
        1: 'i'
        }
    result = ''
    for value, numeral in roman_numerals.items():
        while num >= value:
            result += numeral
            num -= value
    return result

# Main Function
def post_replace(inputfiles, mapping_content):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r'<post_replace find_what=\"([^\"]*)\" replace_with=\"([^\"]*)\" case_sentive=\"([^\"]*)\" regex=\"([^\"]*)\"\/>',
            mapping_content, flags=re.IGNORECASE)
        for match in matches:
            newfile_content = string_replace(match, file_content)
            file_content = newfile_content
        file_handler1 = open(file, "w", encoding="UTF-8")
        file_handler1.write(file_content)
        file_handler1.close()


def pre_replace(inputfiles, mapping_content):
    for file in inputfiles:

        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        pre_matches = re.findall(
            r'<pre_replace find_what=\"([^\"]*)\" replace_with=\"([^\"]*)\" case_sentive=\"([^\"]*)\" regex=\"([^\"]*)\"\/>',
            mapping_content, flags=re.IGNORECASE)
        for prematch in pre_matches:
            newfile_content = string_replace(prematch, file_content)
            file_content = newfile_content
        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def tag_nested_cleanup(inputfiles, mapping_content, input_FileSplit):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r"<nested findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" nested_type=\"([^\"]*)\" nested_level=\"([^\"]*)\" nest_parent=\"([^\"]*)\"\/>",
            mapping_content, flags=re.IGNORECASE)

        for match in matches:
            file_content = clean_up(match, file_content, input_FileSplit)
        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def tag_nested(inputfiles, mapping_content):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r"<nested findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" nested_type=\"([^\"]*)\" nested_level=\"([^\"]*)\" nest_parent=\"([^\"]*)\"\/>",
            mapping_content, flags=re.IGNORECASE)

        file_content = nesting(matches, file_content)
        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def list_format(mapping_content, file_content, listlevel):
    visited_prefix = []
    visited = False
    for x in range(1, listlevel + 1):
        matches = re.findall(
            rf"<listing findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" list_type=\"([^\"]*)\" list_attr=\"([^\"]*)\" list_attr_val=\"([^\"]*)\" list_level=\"{x}\"\/>",
            mapping_content, flags=re.IGNORECASE)
        for match in matches:
            if match[2] not in visited_prefix:
                visited_prefix.append(match[2])
                visited = False
            else:
                visited = True
            file_content = listgroup_open(file_content, match, x, visited)
    file_content = listgroup_open1(file_content, listlevel)
    for x in range(1, listlevel + 1):
        matches = re.findall(
            rf"<listing findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" list_type=\"([^\"]*)\" list_attr=\"([^\"]*)\" list_attr_val=\"([^\"]*)\" list_level=\"{x}\"\/>",
            mapping_content, flags=re.IGNORECASE)

        for match in matches:
            file_content = listgroup_close(file_content, match, x)
    return file_content


def list_tagcleaup(inputfiles, mapping_content):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r"<listing findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" list_type=\"([^\"]*)\" list_attr=\"([^\"]*)\" list_attr_val=\"([^\"]*)\" list_level=\"([^\"]*)\"\/>",
            mapping_content, flags=re.IGNORECASE)
        for match in matches:
            if match[4]:
                file_content = re.sub(rf"<{match[4]}([^<]*)>\n", rf"<{match[4]}\1>", file_content, flags=re.IGNORECASE)
                file_content = re.sub(rf"<{match[4]}([^<]*)>\n", rf"<{match[4]}\1>", file_content, flags=re.IGNORECASE)
            file_content = file_content.replace(f"\n</{match[4]}>", f"</{match[4]}>")
        file_content = file_content.replace("  ", " ")
        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def listing(inputfiles, mapping_content):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        listlevel = 0

        matches = re.findall(
            r"<listing findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" list_type=\"([^\"]*)\" list_attr=\"([^\"]*)\" list_attr_val=\"([^\"]*)\" list_level=\"([^\"]*)\"\/>",
            mapping_content, flags=re.IGNORECASE)
        if matches[0][0] != "":
            file_content = file_content.replace(f"<{matches[0][0]}", f"\n<{matches[0][0]}")
            file_content = file_content.replace(f"</{matches[0][0]}>", f"</{matches[0][0]}>\n")
            file_content = re.sub(r"(\n\n)+", r"\n", file_content)
        for match in matches:
            if match[10]:
                listlevel = int(match[10]) if int(match[10]) > listlevel else listlevel
        file_content = list_format(mapping_content, file_content, listlevel)
        for match in matches:
            attb1 = match[6]
            attb2 = match[9]
            if r"\[\[seq\]\]" in attb1:
                file_content = attribute_squence(attb1, file_content)
            elif r"\[\[seq\]\]" in attb2:
                file_content = attribute_squence(attb2, file_content)
        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def tag_mapping(inputfiles, mapping_content):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r"<map tagname_to_modyfiy=\"([^\"]*)\" tag_selfcolsed=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" htmltag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" self_close=\"([^\"]*)\" add_parent=\"([^\"]*)\" add_p_attr=\"([^\"]*)\" add_p_attr_val=\"([^\"]*)\" add_child=\"([^\"]*)\" add_c_attr=\"([^\"]*)\" add_c_attr_val=\"([^\"]*)\" child_self_close=\"([^\"]*)\" content_before=\"([^\"]*)\" content_after=\"([^\"]*)\"\/>",
            mapping_content, flags=re.IGNORECASE)
        for match in matches:
            file_content = replace_element(match, file_content)
        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def text_movement(inputfiles, mapping_file):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r"<footnote findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" to_move_under=\"([^\"]*)\" move_before=\"([^\"]*)\" move_after=\"([^\"]*)\"\/>",
            mapping_file, flags=re.IGNORECASE)
        for match in matches:
            file_content = footnote(match, file_content)

        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def tag_groupping(inputfiles, mapping_content):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r"<group_map tagname_to_group=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" grouptag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" nested_type=\"([^\"]*)\" nested_level=\"([^\"]*)\"\/>",
            mapping_content, flags=re.IGNORECASE)
        for match in matches:
            find_tag, find_attrb, find_prefix, find_classname = match[0], match[1], match[2], match[3]
            grouptag, add_attr, attr_val = match[4], match[5], match[6]
            nested_type, nested_level = match[7], match[8],
            find_tag = "p" if find_tag == "" else find_tag
            find_attrb = "class" if find_attrb == "" else find_attrb
            new_attribute = f' {add_attr}="{attr_val}"' if "|" not in add_attr else multiple_attribute(add_attr,
                                                                                                       attr_val)
            new_groputag = grouptag if nested_level == "" else f"{grouptag}{nested_level}"
            new_groputag = new_groputag if attr_val == "" else f"{new_groputag}\n{new_attribute}\n"

            if "|" in find_classname:
                find_elements = find_classname.split("|")
                for element in find_elements:
                    group_elementtag = fr'<{new_groputag}>\n<{find_tag}\1{find_attrb}="{element}"\2>\3</{find_tag}>\n</grouptag>'
                    file_content = re.sub(
                        fr"<{find_tag}([^<]*){find_attrb}=\"{element}\"([^<]*)>((?:(?!<\/{find_tag}>).)*(?=<\/{find_tag}>))<\/{find_tag}>",
                        rf"{group_elementtag}", file_content, flags=re.IGNORECASE)
            else:
                find_element = find_classname if find_prefix == "" else find_prefix
                group_elementtag = fr'<{new_groputag}>\n<{find_tag}\1{find_attrb}="{find_element}\2"\3>\4</{find_tag}>\n</grouptag>'
                file_content = re.sub(
                    fr"<{find_tag}([^<]*){find_attrb}=\"{find_element}([^<\"]*)\"([^<]*)>((?:(?!<\/{find_tag}>).)*(?=<\/{find_tag}>))<\/{find_tag}>",
                    rf"{group_elementtag}", file_content, flags=re.IGNORECASE)
            file_content = file_content.replace(f'\n</grouptag>\n<{new_groputag}>', "")
            file_content = file_content.replace(f'</grouptag>', f"</{grouptag}{nested_level}>")
            if "\[\[seq\]\]" in new_attribute:
                file_content = attribute_squence(new_attribute, file_content)
            new_attribute = new_attribute.replace("\[\[seq\]\]", "")
            file_content = file_content.replace(f'<{grouptag}\n', f'<{grouptag}')
            file_content = file_content.replace(f'<{grouptag}{nested_level}\n', f'<{grouptag}{nested_level}')
            file_content = file_content.replace(f'\"\n', '"')

            file_handler = open(file, "w", encoding="UTF-8")
            file_handler.write(file_content)
            file_handler.close()


def get_all_files_and_dirs(dir_path):
    all_files_and_dirs = os.listdir(dir_path)
    files = []
    for file_or_dir in all_files_and_dirs:
        file_or_dir_path = os.path.join(dir_path, file_or_dir)
        if os.path.isfile(file_or_dir_path):
            files.append(file_or_dir_path)
        else:
            subdirectory_files = get_all_files_and_dirs(file_or_dir_path)
            files += subdirectory_files
    return files


def splitFile_template(body_type, split_content, split_tag, level, epubOptions):
    with open(os.path.join(mapping_content_path, "fileSplit_template.html"), "r", encoding="UTF-8") as template:
        html_template = BeautifulSoup(template, "html.parser")

    input_lang = epubOptions["input_lang"]
    text_lang, lang_code = input_lang.split("-")
    html_element = html_template.find("html")
    html_element.attrs['xml:lang'] = lang_code
    html_element.attrs['lang'] = lang_code
    body_element = html_template.find("body")
    body_element.attrs['epub:type'] = body_type
    body_element.append(split_content)
    headtag = html_template.find("head")
    if epubOptions["input_CSSFilesPath"]:
        if epubOptions['input_HTMLFolderName'] != "No Folder":
            cssfiles = get_all_files_and_dirs(f"../{epubOptions['input_CSSFolderName']}")
        else:
            cssfiles = get_all_files_and_dirs(f"{epubOptions['input_CSSFolderName']}")
        for css in cssfiles:
            if css.endswith(".css"):
                linktag = html_template.new_tag("link")
                linktag["rel"] = "stylesheet"
                linktag["type"] = "text/css"
                linktag["href"] = css.replace("\\", "/")
            headtag.append(linktag)

    if epubOptions["input_JSFilesPath"]:
        if epubOptions['input_HTMLFolderName'] != "No Folder":
            jsfiles = get_all_files_and_dirs("../script")
        else:
            jsfiles = get_all_files_and_dirs("script")
        for js in jsfiles:
            if js.endswith(".js"):
                scripttag = html_template.new_tag("script")
                scripttag["src"] = js.replace("\\", "/")
                headtag.append(scripttag)

    section_tag = body_element.find(f"{split_tag}{level}")

    title_tag = html_template.find("title")
    title_tag.clear()
    math_tags = section_tag.find_all("math")
    svg_tags = section_tag.find_all("svg")
    if math_tags is not None:
        for math_tag in math_tags:
            math_tag.attrs['xmlns'] = "http://www.w3.org/1998/Math/MathML"

    if svg_tags is not None:
        for svg_tag in svg_tags:
            svg_tag.attrs['xmlns'] = "http://www.w3.org/2000/svg"
    try:
        heading_tag = section_tag.find_all([f"h{level + 1}", f"h{level}"])
        if len(heading_tag) > 1:
            tem_text = ""
            for heading in heading_tag:
                if tem_text == "":
                    tem_text = heading.text
                else:
                    tem_text = f"{tem_text}: {heading.text}"
            title_tag.string = tem_text
        else:
            title_tag.string = heading_tag.text
    except:
        try:
            heading_tag = section_tag.find([f"h{level + 1}"])
            title_tag.string = heading_tag.text
        except:
            title_tag.clear()
            title_tag.string = f"{section_tag.get('epub:type')}".title()

    return html_template


def file_fragments(file_text, split_tag, level, new_body_name, epubOptions, start=2):
    file = f"{file_text}.xhtml"
    for sublevel in range(start, level + 1):
        with open(file, "r", encoding="UTF-8") as f:
            htmlObject = BeautifulSoup(f, "html.parser")
        levels = htmlObject.find_all(f"{split_tag}{sublevel}")
        for i, elem in enumerate(levels):
            with open(f"{file_text}_" + f"{i + 1}".zfill(2) + ".xhtml", "w", encoding="UTF-8") as f:
                file_order.append(f"{file_text}_" + f"{i + 1}".zfill(2) + ".xhtml")
                elem = splitFile_template(new_body_name, elem, split_tag, sublevel, epubOptions)
                f.write(str(elem))
                if sublevel + 1 < level + 1:
                    new_file_text = f"{file_text}_" + f"{i + 1}".zfill(2)
                    new_level = sublevel + 1
                    new_start = sublevel + 1
                    file_fragments(new_file_text, split_tag, new_level, new_body_name, epubOptions, new_start)
        for elem in levels:
            elem.extract()
        with open(file, "w", encoding="UTF-8") as f:
            f.write(str(htmlObject))


def epub_type_updation(epubOptions, heading_filename_info, fist_levels):
    epub_type_list = Et.fromstring(heading_filename_info)
    input_lang = epubOptions['input_lang']
    text_language, lang_code = input_lang.split("-")
    text_language = text_language.lower()
    possile_headings = epub_type_list.findall(f".//{text_language}/set")
    for possile_heading_el in possile_headings:
        possile_heading = possile_heading_el.find("text").text

        possile_epubType = possile_heading_el.find("epub_type").text
        for section in fist_levels:
            try:
                headings_in_section = section.find(["h1", "h2"])
                if possile_heading in headings_in_section.text:
                    section['epub:type'] = possile_epubType
            except:
                pass

    return fist_levels


def idGenerationforHeading(level, section_tag_in_mapping, split_files, ePub_options):
    sectiontags = []
    chapId = 0
    appId = 0
    headingId = 1
    for i in range(1, level + 1):
        sectiontags.append(f'{section_tag_in_mapping}{i}')
    for htmlfile in split_files:
        if htmlfile.endswith(".html") or htmlfile.endswith(".xhtml") or htmlfile.endswith(".htm"):
            figcount = 1
            tabcount = 1
            with open(htmlfile, "r", encoding="UTF-8") as html:
                htmlcontent = BeautifulSoup(html, "html.parser")
            chapters = htmlcontent.find(f'{section_tag_in_mapping}1', {'epub:type': 'chapter'})
            appendixs = htmlcontent.find(f'{section_tag_in_mapping}1', {'epub:type': 'appendix'})
            if chapters:
                chapId += 1
            elif appendixs:
                appId += 1
            sectiontags_in_html = htmlcontent.find_all(sectiontags)
            if htmlfile.endswith(".xhtml") or htmlfile.endswith(".html") or htmlfile.endswith(".htm"):
                for sectiontag_in_html in sectiontags_in_html:
                    headertags = sectiontag_in_html.find_all('header', recursive=False)
                    if headertags:
                        for headertag in headertags:
                            headings = headertag.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                            for heading in headings:
                                heading['id'] = 'sec_' + f'{headingId}'.zfill(3)
                                headingId += 1
                    else:
                        headings = sectiontag_in_html.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                        for heading in headings:
                            heading['id'] = 'sec_' + f'{headingId}'.zfill(3)
                            headingId += 1

            figures = htmlcontent.find_all('figure')
            tables = htmlcontent.find_all('table')

            for figure in figures:
                if chapters:
                    figimg = figure.find("img")
                    if figimg:
                        figimg['id'] = f'fig_{chapId}_{figcount}'
                    else:
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            imgtag = htmlcontent.new_tag("img", attrs={"src": f"../Images/fig_{chapId}_{figcount}.jpg", "id": f'fig_{chapId}_{figcount}', "alt": "Figure"})
                        else:
                            imgtag = htmlcontent.new_tag("img", attrs={"src": f"Images/fig_{chapId}_{figcount}.jpg",
                                                                       "id": f'fig_{chapId}_{figcount}',
                                                                       "alt": "Figure"})
                        figure.insert(0, imgtag)

                    figcount += 1
                elif appendixs:
                    figimg = figure.find("img")
                    if figimg:
                        figimg['id'] = f'fig_app{appId}_{figcount}'
                    else:
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            imgtag = htmlcontent.new_tag("img",
                                                         attrs={"src": f"../Images/fig_app{appId}_{figcount}.jpg",
                                                                "id": f'fig_app{appId}_{figcount}',
                                                                "alt": "Figure"})
                        else:
                            imgtag = htmlcontent.new_tag("img",
                                                         attrs={"src": f"Images/fig_app{appId}_{figcount}.jpg",
                                                                "id": f'fig_app{appId}_{figcount}',
                                                                "alt": "Figure"})
                        figure.insert(0, imgtag)
                    figcount += 1
                else:
                    figimg = figure.find("img")
                    if figimg:
                        figimg['id'] = f'fig_{figcount}'
                    else:
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            imgtag = htmlcontent.new_tag("img",
                                                         attrs={"src": f"../Images/fig_{figcount}.jpg",
                                                                "id": f'fig_{figcount}',
                                                                "alt": "Figure"})
                        else:
                            imgtag = htmlcontent.new_tag("img",
                                                         attrs={
                                                             "src": f"Images/fig_{figcount}.jpg",
                                                             "id": f'fig_{figcount}',
                                                             "alt": "Figure"})
                        figure.insert(0, imgtag)

                    figcount += 1
            for table in tables:
                tabcaption = table.find("caption")
                if not tabcaption:
                    pre_element = table.find_previous_sibling()
                    if pre_element and 'class' in pre_element.attrs:
                        clasname = pre_element['class'][0]
                        if clasname.startswith('tab') or 'tab' in clasname or 'caption' in clasname or 'cap' in clasname:
                            captiontag = htmlcontent.new_tag("caption")
                            captiontag.append(pre_element)
                            table.insert(0, captiontag)

                if chapters:
                    table['id'] = f'tab_{chapId}_{tabcount}'
                    tabcount += 1
                elif appendixs:
                    table['id'] = f'tab_app{appId}_{tabcount}'
                    tabcount += 1
                else:
                    table['id'] = f'tab_{tabcount}'
                    tabcount += 1
            with open(htmlfile, "w", encoding="UTF-8") as html:
                html.write(str(htmlcontent))


def file_split(file, epubOptions, mapping_content, entity_file, split_info, heading_filename_info):
    global file_order
    file_order = []
    file_name, ext = os.path.splitext(file)
    bodyStart = False
    if epubOptions["input_EntityType"] == "Decimal":
        entity_choice = 4
    elif epubOptions["input_EntityType"] == "Hexa-Decimal":
        entity_choice = 5
    elif epubOptions["input_EntityType"] == "SGML":
        entity_choice = 6
    elif epubOptions["input_EntityType"] == "UTF-8":
        entity_choice = 0
    if ext == ".html" or ext == ".xhtml" or ext == ".htm":
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        if 'xmlns:epub="http://www.idpf.org/2007/ops"' not in file_content:
            file_content = file_content.replace("<html", "<html xmlns:epub=\"http://www.idpf.org/2007/ops\"")

        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()
    working_path = os.getcwd()
    if epubOptions['input_HTMLFolderName'] == "No Folder":
        epubHTMLpath = os.path.join(os.getcwd(),
                                    f"{file_name}\{epubOptions['input_RootFolderName']}")
    else:
        epubHTMLpath = os.path.join(os.getcwd(),
                                    f"{file_name}\{epubOptions['input_RootFolderName']}\{epubOptions['input_HTMLFolderName']}")
    shutil.copy2(os.path.join(working_path, file), epubHTMLpath)
    os.chdir(epubHTMLpath)
    repated_files = []
    split_info_xml = Et.fromstring(split_info)
    possible_file_names = split_info_xml.findall(f"./split/filename")
    for possible_file_name in possible_file_names:
        temp = [possible_file_name.text, 0]
        repated_files.append(temp)

    if epubOptions["input_FileSplit"] == "Level 1" or epubOptions["input_FileSplit"] == "Level 2" or epubOptions[
        "input_FileSplit"] == "Level 3":
        level = 1
        matches = re.findall(
            r"<nested findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" nested_type=\"([^\"]*)\" nested_level=\"1\" nest_parent=\"([^\"]*)\"\/>",
            mapping_content, flags=re.IGNORECASE)
        for match in matches:
            if {match[4]}:
                split_tag = f"{match[4]}"
                break
        with open(file, "r", encoding="UTF-8") as f:
            htmlObject = BeautifulSoup(f, "html.parser")
        fist_levels = htmlObject.find_all(f"{split_tag}{level}")

        fist_levels = epub_type_updation(epubOptions, heading_filename_info, fist_levels)
        for i, fist_level in enumerate(fist_levels):
            splitfile_epub_type = fist_level['epub:type']
            split_info_xml_epub_type = split_info_xml.find(f".//split[EpubType='{splitfile_epub_type}']")
            new_file_name_el = split_info_xml_epub_type.find('filename')
            new_file_name = new_file_name_el.text
            new_file_body_el = split_info_xml_epub_type.find('bodyType')
            new_body_name = new_file_body_el.text
            if new_body_name == "bodymatter":
                bodyStart = True
            if new_body_name == "frontmatter" and bodyStart == True:
                new_body_name = "backmatter"
            if not new_file_name:
                new_file_name = file_name
            else:
                for repeat_file in repated_files:
                    if new_file_name in repeat_file[0]:
                        repeat_file[1] += 1
                        filename_count = repeat_file[1]
                        break
            fist_level = splitFile_template(new_body_name, fist_level, split_tag, level, epubOptions)
            if epubOptions['input_HTMLFileName'] != "Our Standard":
                serial_number = epubOptions['input_HTMLFileName']
            else:
                serial_number = f"{i + 1}".zfill(2)
            with open(f"{serial_number}_{new_file_name}" + f"{filename_count}".zfill(2) + ".xhtml", "w",
                      encoding="UTF-8") as f:
                f.write(str(fist_level))
            file_order.append(f"{serial_number}_{new_file_name}" + f"{filename_count}".zfill(2) + ".xhtml")
            if epubOptions["input_FileSplit"] == "Level 2" or epubOptions["input_FileSplit"] == "Level 3":
                file_text = f"{serial_number}_{new_file_name}" + f"{filename_count}".zfill(2)
                if epubOptions["input_FileSplit"] == "Level 2":
                    new_level = 2
                    file_fragments(file_text, split_tag, new_level, new_body_name, epubOptions)
                elif epubOptions["input_FileSplit"] == "Level 3":
                    new_level = 3
                    file_fragments(file_text, split_tag, new_level, new_body_name, epubOptions)

        if os.path.exists(file):
            os.remove(file)

        split_files = os.listdir(epubHTMLpath)
        find_section_tag_in_mapping = re.search(
            r'<nested findtag="([^"<]*)" find_attrib="([^"<]*)" find_att_value_prefix="([^"<]*)" find_att_value="([^"<]*)" add_p_tag="([^"<]*)" add_attr="([^"<]*)" attr_val="([^"<]*)" nested_type="([^"<]*)" nested_level="([^"<]*)" nest_parent="([^"<]*)"/>',
            mapping_content)
        section_tag_in_mapping = find_section_tag_in_mapping.group(5)
        level_check = re.findall(
            r'<nested findtag="([^"<]*)" find_attrib="([^"<]*)" find_att_value_prefix="([^"<]*)" find_att_value="([^"<]*)" add_p_tag="([^"<]*)" add_attr="([^"<]*)" attr_val="([^"<]*)" nested_type="([^"<]*)" nested_level="([^"<]*)" nest_parent="([^"<]*)"/>',
            mapping_content)
        level = 0
        if level_check:
            for count in level_check:
                if int(count[8]) > level:
                    level = int(count[8])
        idGenerationforHeading(level, section_tag_in_mapping, split_files, epubOptions)
        file_alllowed = [".html", ".xhtml", ".htm", ".ncx", ".opf"]
        for file in split_files:
            filename, ext_file = os.path.splitext(file)
            for ext in file_alllowed:
                if ext == ext_file:
                    if entity_choice != 0:
                        Entity_Toggle.entity_replace(file, entity_choice, entity_file)
    return file_order
def errorlog(errorlogpath, filename, errormessage):
    try:
        error_log = open(f"{errorlogpath}/{filename}_error.log", "x", encoding="UTF-8")
        error_log.close()
    except:
        pass
    with open(f"{errorlogpath}/{filename}_error.log", "a", encoding="UTF-8") as error_log:
        error_log.write(f"\n{errormessage}")

class TocPage():
    def __init__(self, tochtml, uiWindow, GUI):
        self.tochtml = tochtml
        self.uiWindow = uiWindow
        self.GUI = GUI
        self.toc_gui = None
        self.i = None
        self.close = False
        self.empty = False
        self.paratags = tochtml.find_all("p")
        self.toc_classAndLevels = {}
        self.toc_classes = []
        self.selected_values = {}
        self.box_values = {}
        for para in self.paratags:
            if para['class'] not in self.toc_classes:
                self.toc_classes.append(para['class'])
        for toc_class in self.toc_classes:
            self.toc_classAndLevels[toc_class[0]] = "level 1"
        self.formaui()

    def formaui(self):
        height = 150
        if len(self.toc_classAndLevels) > 3:
            height = height + (len(self.toc_classAndLevels) - 3) * 40
        self.toc_gui = tk.Toplevel(self.uiWindow, bg="#acd9fd")
        self.sub_gui = self.GUI(self.toc_gui, 350, height)

        self.toc_gui.title("Toc Mappaing")
        bold = font.Font(weight='bold')
        name_lable = tk.Label(self.toc_gui, text="Class name:", font=bold, pady=10, bg="#acd9fd")
        name_lable.grid(row=0, column=0)
        self.toc_gui.focus_set()

        name_mapping = tk.Label(self.toc_gui, text="Toc Level:", font=bold, pady=10, bg="#acd9fd")
        name_lable.grid(row=0, column=0, sticky="w")
        name_mapping.grid(row=0, column=1, sticky="w")
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "Skip"]

        for self.i, (self.cls, self.levl) in enumerate(self.toc_classAndLevels.items()):
            class_name = tk.Label(self.toc_gui, text=self.cls, bg="#acd9fd")
            class_name.grid(row=self.i+1, column=0, sticky="w", padx=5)
            level_value = tk.StringVar(self.toc_gui)
            level_value.set(levels[0])
            level_filed = ttk.Combobox(self.toc_gui, values=levels, textvariable=level_value)
            level_filed.grid(row=self.i+1, column=1, sticky="w", pady=5)
            self.box_values[self.cls] = level_filed
        self.name_mapping_button = tk.Button(self.toc_gui, text="Submit",
                                             command=lambda: self.toc_mapping(), padx=3)
        self.name_mapping_button.grid(row=self.i + 2, column=0, columnspan=2, sticky="ne", pady=10)


    def toc_mapping(self):
        self.empty == False
        for key in self.toc_classAndLevels.keys():
            if self.box_values[key].get()== "":
                self.empty = True
            else:
                self.empty == False
                self.selected_values[key] = self.box_values[key].get()
        if self.empty == False:
            self.close = True
            self.toc_gui.destroy()
        else:
            messagebox.showerror("Error", "Please fill all feild")
            self.toc_gui.focus_set()

def check_level(parent, userTocSelection):
    class_name = parent['class']
    level = userTocSelection[class_name[0]]
    ncx_level = 0
    for level in userTocSelection.values():
        if level != 'Skip':
            if ncx_level < int(level):
                ncx_level = int(level)
    return level, ncx_level

def TOCitemGeneration(sections, start_level, start, endposion, htmlpath, sublevel=True):
    ol_template = BeautifulSoup(features="html.parser")
    for i in range(start, endposion):
        if not sublevel:
            ol_tag = ol_template.new_tag("ol", attrs={"class": "navlist"})
            ol_template.append(ol_tag)
            sublevel = True

        if sections[i][1] == start_level and not sections[i][2]:
            sections[i][2] = True
            li_tag = ol_template.new_tag("li")
            a_tag = sections[i][0].find("a")
            a_tag['href'] = f"{htmlpath}{a_tag['href']}"
            li_tag.append(a_tag)
            parent_ol = ol_template.find("ol")
            if parent_ol:
                parent_ol.append(li_tag)
            else:
                ol_template.append(li_tag)
        else:
            if not sublevel:
                ol_tag = ol_template.new_tag("ol", attrs={"class": "navlist"})
                ol_template.append(ol_tag)
                sublevel = True

            if sections[i][1] > start_level:
                start_level = sections[i][1]
                start = i
                sublist = TOCitemGeneration(sections, start_level, start, endposion, htmlpath, sublevel=False)
                if li_tag:
                    li_tag.append(sublist)
                else:
                    ol_template.append(sublist)


    for single_ol in ol_template.find_all("ol"):
        if not single_ol.find('li'):
            single_ol.extract()
    for br in ol_template.find_all("br"):
        br.extract()
    return ol_template

def toclink(tocfile, heading_and_filenames, htmlpath, inputfilename, fileorder, epub_options, navItemfile_info, section_tag_in_mapping):
    with open(f'{htmlpath}{tocfile}', "r", encoding="UTF-8") as f:
        tocContent = f.read()
        tochtml = BeautifulSoup(tocContent, 'html.parser')
    paratags = tochtml.find_all("p")
    for_group = heading_and_filenames
    matched_details = {"filename": list(for_group.keys())[0], "heading_position": 0}
    a_tags = tochtml.find_all("a")
    for a_tag in a_tags:
        a_tag.unwrap()
    for para in paratags:
        match_found = False
        for i, (filename, heads) in enumerate(for_group.items()):
            if matched_details["filename"] == filename:
                if heads:
                    for j in range(matched_details["heading_position"], len(heads)):
                        if para.text == heads[j].text:
                            atag = tochtml.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                            match_found = True

                            atext = ""

                            for text in para.contents:
                                if hasattr(text, 'name'):
                                    atext += str(text)
                                else:
                                    atext += text
                            atag.string = atext
                            para.clear()
                            para.append(atag)
                            if j == len(heads) -1:
                                matched_details["heading_position"] = 0
                                if i < len(for_group.keys()) - 1:
                                    matched_details["filename"] = list(for_group.keys())[i + 1]
                            else:
                                matched_details["heading_position"] = j + 1
                                matched_details["filename"] = filename
                            break
                        else:
                            toc_texts = re.findall(r'\w+', para.text)
                            head_texts = re.findall(r'\w+', heads[j].text)
                            text_length = len(toc_texts)
                            matched_num = 0
                            for text in toc_texts:
                                for head_text in head_texts:
                                    if head_text == text:
                                        matched_num +=1
                            matched_percentag = (matched_num/text_length)*100
                            if len(toc_texts) <= 2 and len(toc_texts) == len(head_texts):
                                if matched_percentag >= 50:
                                    match_found = True
                                    atag = tochtml.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                                    match_found = True
                                    unwanter_atag = para.find("a")
                                    if unwanter_atag:
                                        unwanter_atag.unwrap()
                                    atext = ""
                                    for text in para.contents:
                                        if hasattr(text, 'name'):
                                            atext += str(text)
                                        else:
                                            atext += text
                                    atag.string = atext
                                    para.clear()
                                    para.append(atag)

                                    if htmlpath:
                                        errorlog(f'../..', inputfilename,
                                                 f"Warrning: {tocfile}: \n{para} check the link")
                                    else:
                                        errorlog(f'..', inputfilename, f"Warrning: {tocfile}: \n{para} check the link")
                                    if j == len(heads) - 1:
                                        matched_details["heading_position"] = 0
                                        if i < len(for_group.keys()) - 1:
                                            matched_details["filename"] = list(for_group.keys())[i + 1]
                                    else:
                                        matched_details["heading_position"] = j + 1
                                        matched_details["filename"] = filename
                                    break
                            elif matched_percentag >=70:
                                match_found = True
                                atag = tochtml.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                                match_found = True
                                unwanter_atag = para.find("a")
                                if unwanter_atag:
                                    unwanter_atag.unwrap()
                                atext = ""
                                for text in para.contents:
                                    if hasattr(text, 'name'):
                                        atext += str(text)
                                    else:
                                        atext += text
                                atag.string = atext
                                para.clear()
                                para.append(atag)
                                if htmlpath:
                                    errorlog(f'../..', inputfilename, f"Warrning: {tocfile}: \n{para} check the link")
                                else:
                                    errorlog(f'..', inputfilename, f"Warrning: {tocfile}: \n{para} check the link")
                                if j == len(heads) - 1:
                                    matched_details["heading_position"] = 0
                                    if i < len(for_group.keys()) - 1:
                                        matched_details["filename"] = list(for_group.keys())[i + 1]
                                else:
                                    matched_details["heading_position"] = j + 1
                                    matched_details["filename"] = filename
                                break

                        if j == len(heads)-1:
                            matched_details["heading_position"] = 0
                            if i < len(for_group.keys())-1:
                                matched_details["filename"] = list(for_group.keys())[i + 1]

                    if match_found:
                        buffer_file = filename
                        break
                else:
                    matched_details["heading_position"] = 0
                    if i < len(for_group.keys()) - 1:
                        matched_details["filename"] = list(for_group.keys())[i + 1]
        if not match_found:
           matched_details["heading_position"] = 0
           matched_details["filename"] = buffer_file

    myTocPage = TocPage(tochtml, uiWindow, GUI)

    while myTocPage.close is False:
        pass
    userTocSelection = myTocPage.selected_values
    with open(f'{htmlpath}{tocfile}', "w", encoding="UTF-8") as f:
        content = str(tochtml)
        content = re.sub(r'&lt;([^&]*)&gt;', r"<\1>", content, flags=re.IGNORECASE)
        f.write(content)
    hrefs=[]
    with open(f'{htmlpath}{tocfile}', "r", encoding="UTF-8") as f:
        content = f.read()
    tochtml = BeautifulSoup(content, 'html.parser')
    for p in tochtml.find_all("p"):
        if not p.find("a"):
            if htmlpath:
                errorlog(f'../..', inputfilename, f"Error: {tocfile} :\n{p} Link missing")
            else:
                errorlog(f'..', inputfilename, f"Error: {tocfile}: \n{p} Link missing")
    a_hrefs = tochtml.find_all("a")
    for href in a_hrefs:
        hrefs.append(href['href'])
    frontmatter_navItem_language = Et.fromstring(navItemfile_info)
    input_lang = epub_options['input_lang']
    text_language, lang_code = input_lang.split("-")
    text_language = text_language.lower()
    possile_navItems = frontmatter_navItem_language.findall(f".//{text_language}/set")
    html_template = BeautifulSoup(features="html.parser")
    partcount = 0
    chapcount =0
    for htmlname in fileorder:
        itemfound = False
        for href in hrefs:
            if htmlname in href:
                itemfound = True
                break
            else:
                itemfound = False
        if itemfound:
            file_name_items = []
            for href in a_hrefs:
                if htmlname in href['href']:
                    parent = href.parent
                    parent_level, ncx_level = check_level(parent, userTocSelection)
                    if parent_level != 'Skip':
                        parent_level = int(parent_level)
                        temp = [parent, parent_level, False]
                        file_name_items.append(temp)
            endposion = len(file_name_items)
            tocItem1 = TOCitemGeneration(file_name_items, 1, 0, endposion, htmlpath, sublevel=True)
            html_template.append(tocItem1)
        else:
            with open(f'{htmlpath}{htmlname}', "r", encoding="UTF-8") as f:
                text = f.read()
                TextAsHTML = BeautifulSoup(text, 'html.parser')

            section1 = TextAsHTML.find([f"{section_tag_in_mapping}1", "section"])
            if section1['epub:type'] == 'halftitlepage':
                pass
            elif section1['epub:type'] == "chapter":
                chapcount += 1
                tocItem1 = html_template.new_tag("li")
                html_template.append(tocItem1)
                alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                tocItem1.append(alink)
                for possile_navItem in possile_navItems:
                    findEpub_type = possile_navItem.find('epub_type').text
                    FM_navItem = possile_navItem.find('text').text
                    if findEpub_type == section1['epub:type']:
                        alink.string = f'{FM_navItem} {chapcount}'
                        break
            elif section1['epub:type'] == "part":
                partcount += 1
                tocItem1 = html_template.new_tag("li")
                html_template.append(tocItem1)
                alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                tocItem1.append(alink)
                for possile_navItem in possile_navItems:
                    findEpub_type = possile_navItem.find('epub_type').text
                    FM_navItem = possile_navItem.find('text').text
                    if findEpub_type == section1['epub:type']:
                        alink.string = f'{FM_navItem} {partcount}'
                        break
            elif section1['epub:type']:
                tocItem1 = html_template.new_tag("li")
                html_template.append(tocItem1)
                alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                tocItem1.append(alink)
                for possile_navItem in possile_navItems:
                    findEpub_type = possile_navItem.find('epub_type').text
                    FM_navItem = possile_navItem.find('text').text
                    if findEpub_type == section1['epub:type']:
                        alink.string = f'{FM_navItem}'
                        break


    return html_template, ncx_level

def navitemGeneration(sections, section_tag_in_mapping, htmlname, htmlpath, level=1, start=2, sublevel = False, ncx_level = 0):
    ol_tag = ""
    if start <= level:
        ncx_level +=1
        if not sublevel:
            ol_template = BeautifulSoup(features="html.parser")
            ol_tag = ol_template.new_tag("ol", attrs={"class": "navlist"})
            sublevel = True
        subsections = sections.find_all(f"{section_tag_in_mapping}{start}")
        if subsections:
            for subsection in subsections:
                li_tag = ol_template.new_tag("li")
                header_tag = subsection.find('header', recursive=False)
                if header_tag:
                    subheads = header_tag.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                else:
                    subheads = subsection.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)

                if subheads:
                    atext = ""
                    for i, h1 in enumerate(subheads):
                        if i == 0:
                            atext = h1.text
                            a_tag = ol_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}#{h1["id"]}'})
                            li_tag.append(a_tag)
                        else:
                            atext = f'{atext} {h1.text}'
                    a_tag.string = atext
                for newstart in range(start+1, level+1):
                    subsubsection = subsection.find(f"{section_tag_in_mapping}{newstart}")
                    if subsubsection:
                        sub_ol, ncx_level = navitemGeneration(subsection, section_tag_in_mapping, htmlname, htmlpath, level, newstart,
                                              sublevel=False, ncx_level=ncx_level)
                        li_tag.append(sub_ol)


                ol_tag.append(li_tag)

    return ol_tag, ncx_level
def navfiletemp(epub_options, file_order, mapping_content, html_template, navItemfile_info, filename):
    find_section_tag_in_mapping = re.search(
        r'<nested findtag="([^"<]*)" find_attrib="([^"<]*)" find_att_value_prefix="([^"<]*)" find_att_value="([^"<]*)" add_p_tag="([^"<]*)" add_attr="([^"<]*)" attr_val="([^"<]*)" nested_type="([^"<]*)" nested_level="([^"<]*)" nest_parent="([^"<]*)"/>',
        mapping_content)
    section_tag_in_mapping = find_section_tag_in_mapping.group(5)
    page_tag_in_mapping = re.search(r'<pageList IDprefix="([^"<]*)" chapterRestart="([^"<]*)" chapterPageIDPrefix="([^"<]*)" pattern="([^"<]*)" chap_no_roman="([^"<]*)" targetEpubType="([^"<]*)" frontmatterRoman="([^"<]*)"/>', mapping_content)
    pageIDPrefix = page_tag_in_mapping.group(1)
    level_check = re.findall(
        r'<nested findtag="([^"<]*)" find_attrib="([^"<]*)" find_att_value_prefix="([^"<]*)" find_att_value="([^"<]*)" add_p_tag="([^"<]*)" add_attr="([^"<]*)" attr_val="([^"<]*)" nested_type="([^"<]*)" nested_level="([^"<]*)" nest_parent="([^"<]*)"/>',
        mapping_content)
    level = 0
    nav_body = html_template.find("body")
    frontmatter_navItem_language = Et.fromstring(navItemfile_info)
    input_lang = epub_options['input_lang']
    text_language, lang_code = input_lang.split("-")
    text_language = text_language.lower()
    possile_navItems = frontmatter_navItem_language.findall(f".//{text_language}/set")

    if level_check:
        for count in level_check:
            if int(count[8]) > level:
                level = int(count[8])

    tocpages = []
    tocfileNames = []
    heading_and_filenames = {}
    possible_section_tags = []
    for l in range(1, level+1):
        possible_section_tags.append(f'{section_tag_in_mapping}{l}')
    if epub_options['input_HTMLFolderName'] != "No Folder":
        htmlpath =f"{epub_options['input_HTMLFolderName']}/"
    else:
        htmlpath=""
    for htmlfile in file_order:
        with open(f"{htmlpath}{htmlfile}", "r", encoding="UTF-8") as html:
            htmlcontent = BeautifulSoup(html, "html.parser")
        sectiontags_in_html = htmlcontent.find_all(possible_section_tags)
        if htmlfile.endswith(".xhtml") or htmlfile.endswith(".html") or htmlfile.endswith(".htm"):
            for sectiontag_in_html in sectiontags_in_html:
                headertags = sectiontag_in_html.find_all('header', recursive=False)
                if headertags:
                    for headertag in headertags:
                        headings = headertag.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                        headtext = ""
                        if len(headings)<=1:
                            head_tag = headings
                        else:
                            for head in headings:
                                if head.name == 'h2' or head.name == 'h2':
                                    head_tag = Tag(name='h2')
                                else:
                                    head_tag = Tag(name='new_head')
                            for i, head in enumerate(headings):
                                for att, value in head.attrs.items():
                                    if i == 0:
                                        if att == 'id':
                                            id = value
                                    head_tag[att] = value
                                headtext +=head.text
                            head_tag.string = headtext
                            head_tag['id'] = id
                            head_tag = [head_tag]
                        if htmlfile in heading_and_filenames:
                            heading_and_filenames[htmlfile].extend(head_tag)
                        else:
                            heading_and_filenames[htmlfile] = head_tag
                else:
                    headings = sectiontag_in_html.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                    if htmlfile in heading_and_filenames:
                        heading_and_filenames[htmlfile].extend(headings)
                    else:
                        heading_and_filenames[htmlfile] = headings

        toc = htmlcontent.find_all(f'{section_tag_in_mapping}1', {'epub:type': 'toc'})
        if toc:
            tocpages.append(toc)
            tocfileNames.append(htmlfile)

    nav_tag_toc = html_template.find("nav")
    maintoc_list = html_template.new_tag("ol", attrs={"class": "nav-list"})
    nav_tag_toc.append(maintoc_list)

    body_tag = html_template.find("body")

    nav_tag_land = html_template.new_tag("nav", attrs={'epub:type': 'landmarks', })
    body_tag.append(nav_tag_land)
    land_heading = html_template.new_tag("h1", attrs={"epub:type": "title", "id": "guide"})
    land_heading.string = "Guide"
    nav_tag_land.append(land_heading)
    land_list = html_template.new_tag("ol", attrs={"class": "nav-list"})
    land_section = possible_section_tags
    land_section.append("section")
    landBening = 0

    nav_tag_page = html_template.new_tag("nav", attrs={'epub:type': 'page-list'})
    body_tag.append(nav_tag_page)
    page_heading = html_template.new_tag("h1", attrs={"epub:type": "title", "id": "plist"})
    page_heading.string = "Page List"
    nav_tag_page.append(page_heading)
    page_list = html_template.new_tag("ol", attrs={"class": "nav-list"})
    nav_tag_page.append(page_list)
    for htmlname in file_order:
        with open(f'{htmlpath}{htmlname}', "r", encoding="UTF-8") as f:
            text = f.read()
            TextAsHTML = BeautifulSoup(text, 'html.parser')

        landmarks = TextAsHTML.find_all(possible_section_tags)

        for landmark in landmarks:
            epub_type = landmark['epub:type'] if 'epub:type' in landmark.attrs else None
            if epub_type == 'cover':
                landmarkItem = html_template.new_tag("li")
                landmarkItemAtag =  html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}', "epub:type": "cover"})
                landmarkItemAtag.string = "Cover"
                landmarkItem.append(landmarkItemAtag)
                land_list.append(landmarkItem)
            elif epub_type == 'titlepage':
                landmarkItem = html_template.new_tag("li")
                landmarkItemAtag = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}',
                                                                     "epub:type": "titlepage"})
                landmarkItemAtag.string = "Title Page"
                landmarkItem.append(landmarkItemAtag)
                land_list.append(landmarkItem)
            elif epub_type == 'toc':
                landmarkItem = html_template.new_tag("li")
                landmarkItemAtag = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}',
                                                                     "epub:type": "toc"})
                landmarkItemAtag.string = "Table of Contents"
                landmarkItem.append(landmarkItemAtag)
                land_list.append(landmarkItem)
            elif epub_type == 'chapter' or epub_type == 'part' or epub_type == 'introduction':
                if landBening == 0:
                    landBening +=1
                    landmarkItem = html_template.new_tag("li")
                    landmarkItemAtag = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}',
                                                                         "epub:type": "bodymatter"})
                    landmarkItemAtag.string = "Begin Reading"
                    landmarkItem.append(landmarkItemAtag)
                    land_list.append(landmarkItem)
        pageIDs = TextAsHTML.find_all(
            lambda tag: tag.has_attr('id') and f'{pageIDPrefix}' in tag['id'] and tag.get('epub:type') == 'pagebreak')
        for pageid in pageIDs:
            pageItem = html_template.new_tag("li")
            page_list.append(pageItem)
            alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}#{pageid["id"]}'})
            pageItem.append(alink)
            alink.string = pageid['id'].replace(f"{pageIDPrefix}", "")
    nav_tag_land.append(land_list)
    isPart = False
    chaptercount = 0
    partcount = 0
    if epub_options["input_Navigation"] == "TOC":
        tocpage_length = 0
        if len(tocpages) > 1:
            navcontent = tocpages[0][0]
            tocFile = tocfileNames[0]
            tocpage_length = len(str(tocpages[0][0]).split("\n"))
            for i, tocpage in enumerate(tocpages):
                if len(str(tocpage[0]).split("\n")) >= tocpage_length:
                    navcontent = tocpage[0]
                    tocFile = tocfileNames[i]
        elif len(tocpages) == 1:
            navcontent = tocpages[0][0]
            tocFile = tocfileNames[0]
        else:
            errorlog('..', filename, "Error: Table of Content is missing, Please check 'Navigation Option' or 'Input HTML file'")
            navcontent = ""
            submitButton.config(state="normal")

        try:
            tocItems, ncx_level = toclink(tocFile, heading_and_filenames, htmlpath, filename, file_order, epub_options, navItemfile_info, section_tag_in_mapping)
            maintoc_list.append(tocItems)
        except UnboundLocalError:
            messagebox.showerror("Error", 'Toc file missing, please check file has epub:type="toc"')
            submitButton.config(state="normal")

    else:
        for htmlname in file_order:
            with open(f'{htmlpath}{htmlname}', "r", encoding="UTF-8") as f:
                text = f.read()
                TextAsHTML = BeautifulSoup(text, 'html.parser')
            if epub_options["input_Navigation"] == "Level 1":
                section1 = TextAsHTML.find([f"{section_tag_in_mapping}1", "section"])

                if section1['epub:type'] == 'cover' or section1['epub:type'] == 'copyright-page' or section1[
                    'epub:type'] == 'titlepage':
                    tocItem1 = html_template.new_tag("li")
                    maintoc_list.append(tocItem1)
                    alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                    tocItem1.append(alink)
                    for possile_navItem in possile_navItems:
                        findEpub_type = possile_navItem.find('epub_type').text
                        FM_navItem = possile_navItem.find('text').text
                        if findEpub_type == section1['epub:type']:
                            alink.string = f'{FM_navItem}'
                            break
                elif section1['epub:type'] == 'halftitlepage':
                    pass
                elif section1['epub:type'] == 'part':
                    partcount +=1
                    tocItem1 = html_template.new_tag("li")
                    maintoc_list.append(tocItem1)
                    alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                    tocItem1.append(alink)
                    headertags = section1.find('header', recursive=False)
                    if headertags:
                        headings = headertags.find_all(['h1', 'h2'], recursive=False)
                    else:
                        headings = section1.find_all(['h1', 'h2'], recursive=False)

                    if headings:
                        for i, h1 in enumerate(headings):
                            if i == 0:
                                atext = h1.text
                            else:
                                atext = f'{atext} {h1.text}'
                        alink.string = atext
                    else:
                        for possile_navItem in possile_navItems:
                            findEpub_type = possile_navItem.find('epub_type').text
                            FM_navItem = possile_navItem.find('text').text
                            if findEpub_type == section1['epub:type']:
                                alink.string = f'{FM_navItem} {partcount}'
                                break
                    isPart = True
                    firstLevelOl = True
                elif section1['epub:type'] == 'chapter' and isPart:
                    chaptercount += 1
                    if firstLevelOl:
                        subol = html_template.new_tag("ol")
                        tocItem1.append(subol)
                        tocItem2 = html_template.new_tag("li")
                        subol.append(tocItem2)
                        firstLevelOl = False
                    else:
                        tocItem2 = html_template.new_tag("li")
                        subol.append(tocItem2)
                    alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                    tocItem2.append(alink)
                    headertags = section1.find('header', recursive=False)
                    if headertags:
                        headings = headertags.find_all(['h1', 'h2'], recursive=False)
                    else:
                        headings = section1.find_all(['h1', 'h2'], recursive=False)

                    if headings:
                        for i, h1 in enumerate(headings):
                            if i == 0:
                                atext = h1.text
                            else:
                                atext = f'{atext} {h1.text}'
                        alink.string = atext
                    else:
                        for possile_navItem in possile_navItems:
                            findEpub_type = possile_navItem.find('epub_type').text
                            FM_navItem = possile_navItem.find('text').text
                            if findEpub_type == section1['epub:type']:
                                alink.string = f'{FM_navItem} {chaptercount}'
                                break
                elif section1['epub:type'] == 'chapter':
                    chaptercount += 1
                    tocItem1 = html_template.new_tag("li")
                    maintoc_list.append(tocItem1)
                    alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                    tocItem1.append(alink)
                    headertags = section1.find('header', recursive=False)
                    if headertags:
                        headings = headertags.find_all(['h1', 'h2'], recursive=False)
                    else:
                        headings = section1.find_all(['h1', 'h2'], recursive=False)
                    if headings:
                        for i, h1 in enumerate(headings):
                            if i == 0:
                                atext = h1.text
                            else:
                                atext = f'{atext} {h1.text}'
                        alink.string = atext
                    else:
                        for possile_navItem in possile_navItems:
                            findEpub_type = possile_navItem.find('epub_type').text
                            FM_navItem = possile_navItem.find('text').text
                            if findEpub_type == section1['epub:type']:
                                alink.string = f'{FM_navItem} {chaptercount}'
                                break
                elif section1:
                    tocItem1 = html_template.new_tag("li")
                    maintoc_list.append(tocItem1)
                    alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                    tocItem1.append(alink)
                    headertags = section1.find('header', recursive=False)
                    if headertags:
                        headings = headertags.find_all(['h1', 'h2'], recursive=False)
                    else:
                        headings = section1.find_all(['h1', 'h2'], recursive=False)
                    if headings:
                        for i, h1 in enumerate(headings):
                            if i == 0:
                                atext = h1.text
                            else:
                                atext = f'{atext} {h1.text}'
                        alink.string = atext
                    else:
                        for possile_navItem in possile_navItems:
                            findEpub_type = possile_navItem.find('epub_type').text
                            FM_navItem = possile_navItem.find('text').text
                            if findEpub_type == section1['epub:type']:
                                alink.string = f'{FM_navItem}'
                                break
            elif epub_options["input_Navigation"] == "Level 2" or epub_options["input_Navigation"] == "Level 3" or epub_options["input_Navigation"] == "All Heading":
                sections = TextAsHTML.find_all([f"{section_tag_in_mapping}2", f"{section_tag_in_mapping}1", f"{section_tag_in_mapping}"])
                if sections:
                    for section in sections:
                        epub_type = section['epub:type'] if 'epub:type' in section.attrs else None
                        if epub_type == 'cover' or epub_type == 'copyright-page' or epub_type == 'titlepage':
                            tocItem1 = html_template.new_tag("li")
                            maintoc_list.append(tocItem1)
                            alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                            tocItem1.append(alink)
                            for possile_navItem in possile_navItems:
                                findEpub_type = possile_navItem.find('epub_type').text
                                FM_navItem = possile_navItem.find('text').text
                                if findEpub_type == epub_type:
                                    alink.string = f'{FM_navItem}'
                                    break
                        elif epub_type == 'halftitlepage' or epub_type == 'footnotes' or epub_type == 'case-study':
                            pass
                        elif epub_type == 'part':
                            partcount += 1
                            tocItem1 = html_template.new_tag("li")
                            maintoc_list.append(tocItem1)
                            alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                            tocItem1.append(alink)
                            headertags = section.find('header', recursive=False)
                            if headertags:
                                headings = headertags.find_all(['h1', 'h2'], recursive=False)
                            else:
                                headings = section.find_all(['h1', 'h2'], recursive=False)

                            if headings:
                                for i, h1 in enumerate(headings):
                                    if i == 0:
                                        atext = h1.text
                                    else:
                                        atext = f'{atext} {h1.text}'
                                alink.string = atext
                            else:
                                for possile_navItem in possile_navItems:
                                    findEpub_type = possile_navItem.find('epub_type').text
                                    FM_navItem = possile_navItem.find('text').text
                                    if findEpub_type == epub_type:
                                        alink.string = f'{FM_navItem} {partcount}'
                                        break
                            isPart = True
                            firstLevelOl = True
                            if epub_options["input_Navigation"] == "Level 2":
                                sublevels, ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level=2,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level=3,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level,
                                                              start=2, sublevel=False, ncx_level=1)
                            if sublevels:
                                appendTrue = sublevels.find("li")
                                if appendTrue:
                                    tocItem1.append(sublevels)

                        elif epub_type == 'chapter' and isPart:
                            chaptercount += 1
                            if firstLevelOl:
                                subol = html_template.new_tag("ol")
                                tocItem1.append(subol)
                                tocItem2 = html_template.new_tag("li")
                                subol.append(tocItem2)
                                firstLevelOl = False
                            else:
                                tocItem2 = html_template.new_tag("li")
                                subol.append(tocItem2)
                            alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                            tocItem2.append(alink)
                            headertags = section.find('header', recursive=False)
                            if headertags:
                                headings = headertags.find_all(['h1', 'h2'], recursive=False)
                            else:
                                headings = section.find_all(['h1', 'h2'], recursive=False)

                            if headings:
                                for i, h1 in enumerate(headings):
                                    if i == 0:
                                        atext = h1.text
                                    else:
                                        atext = f'{atext} {h1.text}'
                                alink.string = atext
                            else:
                                for possile_navItem in possile_navItems:
                                    findEpub_type = possile_navItem.find('epub_type').text
                                    FM_navItem = possile_navItem.find('text').text
                                    if findEpub_type == epub_type:
                                        alink.string = f'{FM_navItem} {chaptercount}'
                                        break
                            if epub_options["input_Navigation"] == "Level 2":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level=2,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level=3,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level,
                                                              start=2, sublevel=False, ncx_level=1)
                            if sublevels:
                                appendTrue = sublevels.find("li")
                                if appendTrue:
                                    tocItem2.append(sublevels)

                        elif epub_type == 'chapter':
                            chaptercount += 1
                            tocItem1 = html_template.new_tag("li")
                            maintoc_list.append(tocItem1)
                            alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                            tocItem1.append(alink)
                            headertags = section.find('header', recursive=False)
                            if headertags:
                                headings = headertags.find_all(['h1', 'h2'], recursive=False)
                            else:
                                headings = section.find_all(['h1', 'h2'], recursive=False)
                            if headings:
                                for i, h1 in enumerate(headings):
                                    if i == 0:
                                        atext = h1.text
                                    else:
                                        atext = f'{atext} {h1.text}'
                                alink.string = atext
                            else:
                                for possile_navItem in possile_navItems:
                                    findEpub_type = possile_navItem.find('epub_type').text
                                    FM_navItem = possile_navItem.find('text').text
                                    if findEpub_type == epub_type:
                                        alink.string = f'{FM_navItem} {chaptercount}'
                                        break
                            if epub_options["input_Navigation"] == "Level 2":
                                sublevels, ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level=2,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level=3,
                                                              start=2, sublevel=False,ncx_level=1)
                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level,
                                                              start=2, sublevel=False,ncx_level=1)
                            if sublevels:
                                appendTrue = sublevels.find("li")
                                if appendTrue:
                                    tocItem1.append(sublevels)

                        elif epub_type:
                            tocItem1 = html_template.new_tag("li")
                            maintoc_list.append(tocItem1)
                            alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                            tocItem1.append(alink)
                            headertags = section.find('header', recursive=False)
                            if headertags:
                                headings = headertags.find_all(['h1', 'h2'], recursive=False)
                            else:
                                headings = section.find_all(['h1', 'h2'], recursive=False)
                            if headings:
                                for i, h1 in enumerate(headings):
                                    if i == 0:
                                        atext = h1.text
                                    else:
                                        atext = f'{atext} {h1.text}'
                                alink.string = atext
                            else:
                                for possile_navItem in possile_navItems:
                                    findEpub_type = possile_navItem.find('epub_type').text
                                    FM_navItem = possile_navItem.find('text').text
                                    if findEpub_type == epub_type:
                                        alink.string = f'{FM_navItem}'
                                        break
                            if epub_options["input_Navigation"] == "Level 2":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, 2,
                                                              start=2, sublevel=False)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, 3,
                                                              start=2, sublevel=False)

                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, level,
                                                              start=2, sublevel=False)
                            if sublevels:
                                appendTrue = sublevels.find("li")
                                if appendTrue:
                                    tocItem1.append(sublevels)

    if epub_options["input_includeTable"]:
        nav_tag_table = html_template.new_tag("nav", attrs={'epub:type': 'lot'})
        body_tag.append(nav_tag_table)
        tbl_heading = html_template.new_tag("h1", attrs={"epub:type": "title", "id": "table-list"})
        tbl_heading.string = "List of Tables"
        nav_tag_table.append(tbl_heading)
        lot = html_template.new_tag("ol", attrs={"class": "nav-list"})
        for htmlfile in file_order:
            with open(f"{htmlpath}{htmlfile}", "r", encoding="UTF-8") as html:
                htmlcontent = BeautifulSoup(html, "html.parser")
            tables = htmlcontent.find_all("table")
            if tables:
                for table in tables:
                    tabcaption = table.find("caption")
                    if tabcaption:
                        tableItem = html_template.new_tag("li")
                        tableItem_ahref = html_template.new_tag("a",
                                                                 attrs={"href": f'{htmlpath}{htmlfile}#{table["id"]}'})
                        tableItem.append(tableItem_ahref)
                        tableItem_ahref.string = tabcaption.text
                        lot.append(tableItem)


        nav_tag_table.append(lot)
    if epub_options["input_includeFigure"]:
        nav_tag_figure = html_template.new_tag("nav", attrs={'epub:type': 'loi'})
        body_tag.append(nav_tag_figure)
        fig_heading = html_template.new_tag("h1", attrs={"epub:type": "title", "id": "figure-list"})
        fig_heading.string = "List of Figures"
        nav_tag_figure.append(fig_heading)
        loi = html_template.new_tag("ol", attrs={"class": "nav-list"})
        for htmlfile in file_order:
            with open(f"{htmlpath}{htmlfile}", "r", encoding="UTF-8") as html:
                htmlcontent = BeautifulSoup(html, "html.parser")
            figures = htmlcontent.find_all("figure")
            if figures:
                for figure in figures:
                    figcaption = figure.find("figcaption")

                    imgtag = figure.find("img")

                    if figcaption:
                        figcaptionpara = figcaption.find("p")
                        figureItem = html_template.new_tag("li")
                        figureItem_ahref = html_template.new_tag("a", attrs={"href": f'{htmlpath}{htmlfile}#{imgtag["id"]}'})
                        figureItem.append(figureItem_ahref)
                        if figcaptionpara:
                            figureItem_ahref.string = figcaptionpara.text
                        else:
                            if figcaption:
                                figureItem_ahref.string = figcaption.text
                        loi.append(figureItem)
        nav_tag_figure.append(loi)
    if epub_options["input_Navigation"] == "Level 1":
        ncx_level = 1
    elif epub_options["input_Navigation"] == "Level 2":
        ncx_level = 2
    return html_template, ncx_level


def navFileCreation(ePub_options, metadetails, file_order, mapping_content, navItemfile_info, filename):
    with open(os.path.join(mapping_content_path, "fileSplit_template.html"), "r", encoding="UTF-8") as template:
        html_template = BeautifulSoup(template, "html.parser")
    input_lang = ePub_options["input_lang"]
    text_lang, lang_code = input_lang.split("-")
    html_element = html_template.find("html")
    html_element.attrs['xml:lang'] = lang_code
    html_element.attrs['lang'] = lang_code
    body_element = html_template.find("body")
    nav_tag = html_template.new_tag("nav")
    nav_tag.attrs['epub:type'] = "toc"
    body_element.append(nav_tag)
    head_tag = html_template.new_tag("h1")
    head_tag.attrs['epub:type'] = "title"
    head_tag.string = "Table of Contents"
    nav_tag.append(head_tag)
    title_tag = html_template.find("title")
    title_tag.string = metadetails[0]['Title']
    headtag = html_template.find("head")
    if ePub_options["input_CSSFilesPath"]:
        cssfiles = get_all_files_and_dirs(f"{ePub_options['input_CSSFolderName']}")
        for css in cssfiles:
            if css.endswith(".css"):
                linktag = html_template.new_tag("link")
                linktag["rel"] = "stylesheet"
                linktag["type"] = "text/css"
                linktag["href"] = css.replace("\\", "/")
            headtag.append(linktag)
    html_template, ncx_level = navfiletemp(ePub_options, file_order, mapping_content, html_template, navItemfile_info, filename)
    ncx_content = html_template
    navfile = str(html_template)
    navfile = navfile.replace("><nav", '>\n<nav')
    navfile = navfile.replace("><ol", '>\n<ol')
    navfile = navfile.replace("><h1", '>\n<h1')
    navfile = navfile.replace("><li", '>\n<li')
    navfile = navfile.replace("></nav", '>\n</nav')
    navfile = navfile.replace("></body", '>\n</body')
    navfile = navfile.replace("></ol", '>\n</ol')
    navfile = navfile.replace('">\n', '">')
    with open(f"{ePub_options['input_NCXName']}.xhtml", "w", encoding="utf-8") as nav:
        nav.write(navfile)

    ncx_items = ncx_content.find("nav", attrs={"epub:type": "toc"})
    ncx_pageItems = ncx_content.find("nav", attrs={"epub:type": "page-list"})

    NCX_File = BeautifulSoup(features='xml')
    NCX_root = NCX_File.new_tag('ncx', attrs={'version': '2005-1', 'xmlns': 'http://www.daisy.org/z3986/2005/ncx/', 'xmlns:xlink': 'http://www.w3.org/1999/xlink', 'xml:lang': f"{lang_code}"})
    NCX_File.append(NCX_root)
    NCX_head = NCX_File.new_tag('head')
    NCX_root.append(NCX_head)
    NCX_meta1 = NCX_File.new_tag('meta', attrs={'name': 'dtb:uid', 'content': f"{metadetails[0]['e-ISBN']}"})
    NCX_meta2 = NCX_File.new_tag('meta', attrs={'name': 'dtb:depth', 'content': f"{ncx_level}"})
    NCX_meta3 = NCX_File.new_tag('meta', attrs={'name': 'dtb:totalPageCount', 'content': f"{metadetails[0]['Pages']}"})
    NCX_meta4 = NCX_File.new_tag('meta', attrs={'name': 'dtb:maxPageNumber', 'content': f"{metadetails[0]['Pages']}"})
    NCX_head.append(NCX_meta1)
    NCX_head.append(NCX_meta2)
    NCX_head.append(NCX_meta3)
    NCX_head.append(NCX_meta4)
    NCX_Title = NCX_File.new_tag('docTitle')
    NCX_root.append(NCX_Title)
    NCX_text = NCX_File.new_tag('text')
    NCX_text.string = metadetails[0]['Title']
    NCX_Title.append(NCX_text)
    NCX_NavMap = NCX_File.new_tag('navMap')
    NCX_root.append(NCX_NavMap)
    NCX_Page = NCX_File.new_tag('pageList')
    NCX_root.append(NCX_Page)

    unwantedh1 = ncx_items.find('h1')
    if unwantedh1:
        unwantedh1.extract()
    unwantedh1 = ncx_pageItems.find('h1')
    if unwantedh1:
        unwantedh1.extract()
    for ol in ncx_items.find_all('ol'):
        ol.unwrap()
    for ol in ncx_pageItems.find_all('ol'):
        ol.unwrap()
    ncx_items = str(ncx_items)
    ncx_items = ncx_items.replace("><li", '>\n<li')
    ncx_items = re.sub(r'<li><a href="([^<"]*)">((?:(?!<\/a>).)*(?=<\/a>))</a>', r'<navPoint id="nav-1" playOrder="1"><navLabel><text>\2</text></navLabel><content src="\1"/>', ncx_items)
    ncx_items = ncx_items.replace("</li>", '</navPoint>')
    ncx_items = BeautifulSoup(ncx_items, "html.parser")
    NCX_NavMap.append(ncx_items)
    ncx_pageItems = str(ncx_pageItems)
    ncx_pageItems = ncx_pageItems.replace("><li", '>\n<li')

    ncx_pageItems = re.sub(r'<li><a href="([^<"]*)">((?:(?!<\/a>).)*(?=<\/a>))</a></li>',
                       r'<pageTarget id="nav-1" playOrder="1" type="front" value="1"><navLabel><text>\2</text></navLabel><content src="\1"/></pageTarget>',
                       ncx_pageItems)

    ncx_pageItems = BeautifulSoup(ncx_pageItems, "html.parser")
    NCX_Page.append(ncx_pageItems)
    navcount = 1

    for navItem in NCX_NavMap.find_all('navpoint'):
        navItem['id'] = f'nav-{navcount}'
        navItem['playorder'] = navcount
        navcount += 1
        navitem_text_el = navItem.find('text')
        navtext = navitem_text_el.text
        navitem_text_el.string = navtext
    value = 1
    for navPage in NCX_Page.find_all('pagetarget'):
        navPage['id'] = f'nav-{navcount}'
        navPage['playorder'] = navcount
        navPage['value'] = value
        value += 1
        navcount += 1
        if "-" in navPage.find('text').text:
            navPage['type'] = 'special'
        elif re.search(r"\d+", navPage.find('text').text):
            navPage['type'] = 'normal'
        elif re.search(r"\w+", navPage.find('text').text):
            navPage['type'] = 'front'
        else:
            navPage['type'] = 'special'

    for unwanted in NCX_root.find_all('nav'):
        unwanted.unwrap()
    NCX_File_cotent = str(NCX_File)
    NCX_File_cotent = NCX_File_cotent.replace('><head', '>\n<head')
    NCX_File_cotent = NCX_File_cotent.replace('><meta', '>\n<meta')
    NCX_File_cotent = NCX_File_cotent.replace('><docTitle', '>\n<docTitle')
    NCX_File_cotent = NCX_File_cotent.replace('><navMap', '>\n<navMap')
    NCX_File_cotent = NCX_File_cotent.replace('><pageList', '>\n<pageList')
    NCX_File_cotent = NCX_File_cotent.replace('></navMap>', '>\n</navMap>')
    NCX_File_cotent = NCX_File_cotent.replace('></head>', '>\n</head>')
    NCX_File_cotent = NCX_File_cotent.replace('></ncx>', '>\n</ncx>')
    NCX_File_cotent = NCX_File_cotent.replace('></pageList>', '>\n</pageList>')
    NCX_File_cotent = NCX_File_cotent.replace('<pagetarget', '<pageTarget')
    NCX_File_cotent = NCX_File_cotent.replace('</pagetarget', '</pageTarget')
    NCX_File_cotent = NCX_File_cotent.replace('<navpoint', '<navPoint')
    NCX_File_cotent = NCX_File_cotent.replace('</navpoint', '</navPoint')
    NCX_File_cotent = NCX_File_cotent.replace('<navlabel', '<navLabel')
    NCX_File_cotent = NCX_File_cotent.replace('</navlabel', '</navLabel')
    NCX_File_cotent = NCX_File_cotent.replace('playorder=', 'playOrder=')
    with open(f"{ePub_options['input_NCXName']}.ncx", "w", encoding="utf-8") as nav:
        nav.write(NCX_File_cotent)
    file_alllowed = [".html", ".xhtml", ".htm", ".ncx", ".opf"]
    if ePub_options["input_EntityType"] == "Decimal":
        entity_choice = 4
    elif ePub_options["input_EntityType"] == "Hexa-Decimal":
        entity_choice = 5
    elif ePub_options["input_EntityType"] == "SGML":
        entity_choice = 6
    elif ePub_options["input_EntityType"] == "UTF-8":
        entity_choice = 0

    Entity_Toggle.entity_replace(f"{ePub_options['input_NCXName']}.ncx", entity_choice, entity_file)
    Entity_Toggle.entity_replace(f"{ePub_options['input_NCXName']}.xhtml", entity_choice, entity_file)
    if ePub_options['input_epub_version'] == 'ePub 2':
        os.remove(f"{ePub_options['input_NCXName']}.xhtml")
def opfFileCreation(ePub_options, metadetails, filename, file_order):
    if ePub_options['input_HTMLFolderName'] != "No Folder":
        os.chdir("..")
    opf = BeautifulSoup(features='xml')
    # Create the <package> element and add it to the BeautifulSoup object
    lang, lang_code = ePub_options['input_lang'].split("-")
    package = opf.new_tag('package')
    package.attrs = {'xmlns': 'http://www.idpf.org/2007/opf', 'xmlns:m': 'http://www.w3.org/1998/Math/MathML',
                     'prefix': "rendition: http://www.idpf.org/vocab/rendition/# rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns# a11y: http://www.idpf.org/epub/vocab/package/a11y/#",
                     'xml:lang': lang_code, 'unique-identifier': f"isbn{metadetails[0]['e-ISBN']}"}
    if ePub_options['input_epub_version'] == "ePub 3":
        package['version'] = '3.0'
    elif ePub_options['input_epub_version'] == "ePub 2":
        package['version'] = '2.0'
    opf.append(package)

    # Create the <metadata> element and add it to the <package> element
    metadata = opf.new_tag('metadata', attrs={'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                                              'xmlns:opf': 'http://www.idpf.org/2007/opf'})
    package.append(metadata)

    # Create the <dc:title> element and add it to the <metadata> element
    title = opf.new_tag('dc:title')
    title.string = metadetails[0]['Title']
    metadata.append(title)

    # Create the <dc:creator> element and add it to the <metadata> element
    if not pandas.isna(metadetails[0]['Author']):
        author_details = metadetails[0]['Author'].replace(", ", ",")
        authors = author_details.split(",")
        for i, author in enumerate(authors):
            creator = opf.new_tag('dc:creator')
            creator.string = author
            creator['id'] = f"creater{i}"
            metadata.append(creator)
            if ePub_options['input_epub_version'] == "ePub 3":
                creator_meta = opf.new_tag('meta', attrs={"refines": f"#creater{i}", "property": "role"})
                creator_meta.string = "aut"
                metadata.append(creator_meta)

    # Create the <dc:contributor> element and add it to the <metadata> element

    if not pandas.isna(metadetails[0]['Editors']):
        editors_details = metadetails[0]['Editors'].replace(", ", ",")
        editors = editors_details.split(",")
        for i, editor in enumerate(editors):
            ed_contributor = opf.new_tag('dc:contributor')
            ed_contributor.string = editor
            ed_contributor['id'] = f"editor{i}"
            metadata.append(ed_contributor)
    if not pandas.isna(metadetails[0]['Translators']):
        translator_details = metadetails[0]['Translators'].replace(", ", ",")
        translators = translator_details.split(",")
        for i, translator in enumerate(translators):
            tr_contributor = opf.new_tag('dc:contributor')
            tr_contributor.string = translator
            tr_contributor['id'] = f"translator{i}"
            metadata.append(tr_contributor)

    # Create the <dc:identifier> and <dc:source> element and add it to the <metadata> element
    identifier = opf.new_tag("dc:identifier", attrs={'id': f"isbn{metadetails[0]['e-ISBN']}"})
    identifier.string = f"{metadetails[0]['e-ISBN']}"
    metadata.append(identifier)
    if ePub_options['input_epub_structure'] == "Accessible":
        meta_identifier = opf.new_tag('meta', attrs={'refines': f"isbn{metadetails[0]['e-ISBN']}",
                                                     'property': 'identifier-type', 'scheme': 'onix:codelist5'})
        meta_identifier.string = "15"
        metadata.append(meta_identifier)
    if not pandas.isna(metadetails[0]['P-ISBN']):
        print_source = opf.new_tag("dc:source", attrs={'id': f"isbn{metadetails[0]['P-ISBN']}"})
        print_source.string = f"{metadetails[0]['P-ISBN']}"
        metadata.append(print_source)
        if ePub_options['input_epub_structure'] == "Accessible":
            meta_identifier = opf.new_tag('meta',
                                          attrs={'refines': f"isbn{metadetails[0]['P-ISBN']}", 'property': 'source-of'})
            meta_identifier.string = "pagination"
            metadata.append(meta_identifier)
    # Create the <dc:format> and <dc:source> element and add it to the <metadata> element
    dcformat = opf.new_tag("dc:format")
    dcformat.string = 'application/ePub'
    metadata.append(dcformat)

    # Create the <dc:date> and <dc:source> element and add it to the <metadata> element
    get_now = datetime.now()
    dcdate = opf.new_tag("dc:date")
    metadata.append(dcdate)
    if ePub_options['input_epub_version'] == "ePub 3":
        current_date = get_now.strftime('%Y-%m-%dT00:00:00Z')
        dcdate.string = current_date
        dcdate_meta = opf.new_tag("meta", attrs={"property": "dcterms:modified"})
        dcdate_meta.string = current_date
        metadata.append(dcdate_meta)
    else:
        current_date = get_now.strftime('%Y')
        dcdate.string = current_date

    # Create the <dc:type> element and add it to the <metadata> element
    dctype = opf.new_tag("dc:type")
    dctype.string = 'Text'
    metadata.append(dctype)

    # Create the <dc:rights> element and add it to the <metadata> element
    if not pandas.isna(metadetails[0]['Copyrights']):
        dcrights = opf.new_tag("dc:rights")
        dcrights.string = f"{metadetails[0]['Copyrights']}"
        metadata.append(dcrights)
    # Create the <dc:language> element and add it to the <metadata> element
    dclanguage = opf.new_tag("dc:language")
    dclanguage.string = lang_code
    metadata.append(dclanguage)

    # Create the <dc:publisher> element and add it to the <metadata> element
    if not pandas.isna(metadetails[0]['Publisher']):
        dcpublisher = opf.new_tag("dc:publisher")
        dcpublisher.string = f"{metadetails[0]['Publisher']}"
        metadata.append(dcpublisher)

    # Create the <dc:subject> element and add it to the <metadata> element
    if not pandas.isna(metadetails[0]['Subject']):
        dcsubject = opf.new_tag("dc:subject")
        dcsubject.string = f"{metadetails[0]['Subject']}"
        metadata.append(dcsubject)

    # Create the <dc:description> element and add it to the <metadata> element
    if not pandas.isna(metadetails[0]['dc:description']):
        dcdescription = opf.new_tag("dc:description")
        dcdescription.string = f"{metadetails[0]['dc:description']}"
        metadata.append(dcdescription)

    # Create the <Cover> element and add it to the <package> element
    dccover = opf.new_tag("meta", attrs={"name": "cover", "content": "cover-image"})
    metadata.append(dccover)

    if ePub_options['input_epub_structure'] == "Accessible":
        access_modes = ["textual", "visual"]
        access_modes_sufficient = ["textual,visual", "textual"]
        accessibility_features = ["structuralNavigation", "readingOrder", "printPageNumbers", "tableOfContents",
                                  "displayTransformability", "alternativeText", "longDescription", "index"]
        accessibility_hazards = ["noFlashingHazard", "noSoundHazard", "noMotionSimulationHazard"]
        for access_mode in access_modes:
            meta = opf.new_tag("meta", property="schema:accessMode")
            meta.string = access_mode
            metadata.append(meta)
        for access_mode_sufficient in access_modes_sufficient:
            meta = opf.new_tag("meta", property="schema:accessModeSufficient")
            meta.string = access_mode_sufficient
            metadata.append(meta)

        for accessibility_feature in accessibility_features:
            meta = opf.new_tag("meta", property="schema:accessibilityFeature")
            meta.string = accessibility_feature
            metadata.append(meta)

        for accessibility_hazard in accessibility_hazards:
            meta = opf.new_tag("meta", property="schema:accessibilityHazard")
            meta.string = accessibility_hazard
            metadata.append(meta)

        if not pandas.isna(metadetails[0]['Accessibility Summary']):
            dssummary = opf.new_tag("meta", attrs={"property": "schema:accessibilitySummary"})
            dssummary.string = f"{metadetails[0]['Accessibility Summary']}"
            metadata.append(dssummary)

    # Create the <manifest> element and add it to the <package> element
    manifest = opf.new_tag('manifest')
    package.append(manifest)
    allfiles = get_all_files_and_dirs(".")
    spin_order = []
    # Create the <item> elements for cover html and add them to the <manifest> element
    if ePub_options['input_epub_version'] == "ePub 3":
        nav = opf.new_tag('item')
        nav['id'] = 'Nav001'
        nav['media-type'] = 'application/xhtml+xml'
        if ePub_options["input_NCXName"] == "ISBN":
            nav['href'] = f"{metadetails[0]['e-ISBN']}.xhtml"
        else:
            nav['href'] = f'{ePub_options["input_NCXName"]}.xhtml'
        nav['properties'] = 'nav'
        manifest.append(nav)
    ncxitem = opf.new_tag('item')
    ncxitem['id'] = 'ncx'
    ncxitem['media-type'] = 'application/x-dtbncx+xml'
    if ePub_options["input_NCXName"] == "ISBN":
        ncxitem['href'] = f"{metadetails[0]['e-ISBN']}.ncx"
    else:
        ncxitem['href'] = f'{ePub_options["input_NCXName"]}.ncx'
    manifest.append(ncxitem)
    file_order.insert(0, "00_Cover.xhtml")
    # Create the <item> element for html files and add it to the <package> element
    properties_list = ["svg", "mathml", "remote-resources", "scripted"]
    for i, manifest_item in enumerate(allfiles):
        manifest_item = manifest_item.replace(".\\", "")
        if manifest_item.endswith(".xhtml") or manifest_item.endswith(".html") or manifest_item.endswith(".htm"):
            properties = ""
            item1 = opf.new_tag('item')
            item1['href'] = manifest_item.replace("\\", "/")
            item1['media-type'] = 'application/xhtml+xml'
            if ePub_options['input_HTMLFolderName'] != "No Folder":
                manifest_html = manifest_item.replace(f"{ePub_options['input_HTMLFolderName']}\\", "")
            else:
                manifest_html = manifest_item
            if manifest_html in file_order:
                item1['id'] = 'HTML' + f'{file_order.index(manifest_html) + 1}'.zfill(3)
            else:
                item1['id'] = 'OHTML' + f'{i + 1}'.zfill(3)
            with open(manifest_item, "r", encoding="UTF-8") as f:
                htmlcontent = f.read()
                if "<svg" in htmlcontent:
                    properties += " svg"
                if ("<math" or "<mml:" or "<m:") in htmlcontent:
                    properties += " mathml"
                if 'src="http' in htmlcontent:
                    properties += " remote-resources"
                if '<script' in htmlcontent:
                    properties += " scripted"
            if properties:
                item1['properties'] = properties
            manifest.append(item1)
        # Create the <item> element for CSS files and add it to the <package> element
        elif manifest_item.endswith(".css"):
            item1 = opf.new_tag('item')
            item1['id'] = 'CSS' + f'{i + 1}'.zfill(3)
            item1['media-type'] = 'text/css'
            item1['href'] = manifest_item.replace("\\", "/")
            manifest.append(item1)
        # Create the <item> element for Fonst files and add it to the <package> element
        elif manifest_item.endswith(".otf") or manifest_item.endswith(".ttf") or manifest_item.endswith(".woff"):
            item1 = opf.new_tag('item')
            item1['id'] = 'font' + f'{i + 1}'.zfill(3)
            item1['href'] = manifest_item.replace("\\", "/")
            item1['media-type'] = 'application/vnd.ms-opentype'
            manifest.append(item1)
        # Create the <item> element for JS files and add it to the <package> element
        elif manifest_item.endswith(".js") or manifest_item.endswith(".swf"):
            item1 = opf.new_tag('item')
            item1['id'] = f'JS' + f'{i + 1}'.zfill(3)
            item1['href'] = manifest_item.replace("\\", "/")
            if manifest_item.endswith(".js"):
                item1['media-type'] = 'text/javascript'
            else:
                item1['media-type'] = 'application/swf'
            manifest.append(item1)
        # Create the <item> element for Media files and add it to the <package> element
        elif manifest_item.endswith(".mp3") or manifest_item.endswith(".mp4"):
            item1 = opf.new_tag('item')
            item1['id'] = f'media' + f'{i + 1}'.zfill(3)
            item1['href'] = manifest_item.replace("\\", "/")
            if manifest_item.endswith(".mp3"):
                item1['media-type'] = 'audio/mpeg'
            else:
                item1['media-type'] = 'audio/mp4'
            manifest.append(item1)
        # Create the <item> element for Smil files and add it to the <package> element
        elif manifest_item.endswith(".smil"):
            item1 = opf.new_tag('item')
            item1['id'] = f'smil' + f'{i + 1}'.zfill(3)
            item1['href'] = manifest_item.replace("\\", "/")
            item1['media-type'] = 'application/smil+xml'
            manifest.append(item1)
        elif manifest_item == f'Images\{os.path.basename(ePub_options["input_CoverImagePath"])}':
            item1 = opf.new_tag('item')
            item1['id'] = 'cover-image'
            item1['href'] = manifest_item.replace("\\", "/")
            image_name, img_ext = os.path.splitext(os.path.basename(ePub_options['input_CoverImagePath']))
            if img_ext.upper() == ".gif".upper():
                item1['media-type'] = 'image/gif'
            elif img_ext.upper() == ".jpg".upper() or img_ext.upper() == ".jpeg".upper():
                item1['media-type'] = 'image/jpeg'
            elif img_ext.upper() == ".png".upper():
                item1['media-type'] = 'image/png'
            elif img_ext.upper() == ".svg".upper():
                item1['media-type'] = 'image/svg+xml'
            item1['properties'] = 'cover-image'
            manifest.append(item1)
        # Create the <item> element for Images  and add it to the <package> element
        elif manifest_item.endswith(".gif") or manifest_item.endswith(".png") or manifest_item.endswith(
                ".jpg") or manifest_item.endswith(".jpeg") or manifest_item.endswith(".svg"):
            item1 = opf.new_tag('item')
            item1['id'] = 'image' + f'{i}'.zfill(3)
            item1['href'] = manifest_item.replace("\\", "/")
            image_name, img_ext = os.path.splitext(manifest_item)
            if img_ext.upper() == ".gif".upper():
                item1['media-type'] = 'image/gif'
            elif img_ext.upper() == ".jpg".upper() or img_ext.upper() == ".jpeg".upper():
                item1['media-type'] = 'image/jpeg'
            elif img_ext.upper() == ".png".upper():
                item1['media-type'] = 'image/png'
            elif img_ext.upper() == ".svg".upper():
                item1['media-type'] = 'image/svg+xml'
            manifest.append(item1)
        else:
            try:
                error_log = open(f"../../{filename}_error.log" "x", encoding="UTF-8")
                error_log.close()
            except:
                pass
            with open(f"../../{filename}_error.log", "a", encoding="UTF-8") as error_log:
                error_log.write(f'Error: unknown file "{manifest_item}" in ePub\n')
    # Create the <spine> element and add it to the <package> element
    spine = opf.new_tag('spine')
    spine['toc'] = 'ncx'
    package.append(spine)

    # Create the <itemref> elements and add them to the <spine> element
    for i, spin in enumerate(file_order):
        itemref1 = opf.new_tag('itemref')
        itemref1['idref'] = 'HTML' + f"{i + 1}".zfill(3)
        spine.append(itemref1)

    # Write the BeautifulSoup object to a file with the .opf extension
    with open(f'{ePub_options["input_opfName"]}.opf', 'w', encoding='utf-8') as file:
        file.write(str(opf).replace("><", ">\n<"))
    return file_order


def pageIDgenration(file, mapping_content, ePub_options, filename, split_info):
    pageIDpatterns = re.findall(
        r'<pageList IDprefix="([^"<]*)" chapterRestart="([^"<]*)" chapterPageIDPrefix="([^"<]*)" pattern="([^"<]*)" chap_no_roman="([^"<]*)" targetEpubType="([^"<]*)" frontmatterRoman="([^"<]*)"/>',
        mapping_content)
    pageformat_check = re.search(
        r'<pageList IDprefix="([^"<]*)" chapterRestart="([^"<]*)" chapterPageIDPrefix="([^"<]*)" pattern="([^"<]*)" chap_no_roman="([^"<]*)" targetEpubType="([^"<]*)" frontmatterRoman="([^"<]*)"/>',
        mapping_content)
    try:
        pageformat = pageformat_check.group(2)
    except:
        errorlog('..', filename, "Error: pagelist is missing in config xml file")

    prefix = pageformat_check.group(1)
    frontmatterRoman = pageformat_check.group(7)
    find_section_tag_in_mapping = re.search(
        r'<nested findtag="([^"<]*)" find_attrib="([^"<]*)" find_att_value_prefix="([^"<]*)" find_att_value="([^"<]*)" add_p_tag="([^"<]*)" add_attr="([^"<]*)" attr_val="([^"<]*)" nested_type="([^"<]*)" nested_level="([^"<]*)" nest_parent="([^"<]*)"/>',
        mapping_content)
    section_tag_in_mapping = find_section_tag_in_mapping.group(5)
    with open(file, "r", encoding="UTF-8") as f:
        htmlObject = BeautifulSoup(f, "html.parser")
    level = 1
    fist_levels = htmlObject.find_all(f"{section_tag_in_mapping}{level}")
    fist_levels = epub_type_updation(ePub_options, heading_filename_info, fist_levels)

    frontmatters = []
    backmatters = []
    bodymatters = []
    split_info_xml = Et.fromstring(split_info)
    bodytypes = split_info_xml.findall(f"split")
    for bodytype in bodytypes:
        splitepubtype = bodytype.find("bodyType")
        if splitepubtype.text == "frontmatter":
            fm_epub_type_el = bodytype.find("EpubType")
            fm_epub_type = fm_epub_type_el.text
            frontmatters.append(fm_epub_type)
        elif splitepubtype.text == "backmatter":
            bm_epub_type_el = bodytype.find("EpubType")
            bm_epub_type = bm_epub_type_el.text
            backmatters.append(bm_epub_type)
        else:
            body_epub_type_el = bodytype.find("EpubType")
            body_epub_type = body_epub_type_el.text
            bodymatters.append(body_epub_type)

    pagenumber = 0
    if pageformat.upper() == 'NO' or pageformat.upper() == 'N' or pageformat.upper() == 'FALSE':
        if frontmatterRoman.upper() == 'NO' or frontmatterRoman.upper() == 'N' or frontmatterRoman.upper() == 'FALSE':
            pagenumber = 0 if int(ePub_options['input_pageOffset']) == 0 else pagenumber + int(
                ePub_options['input_pageOffset'])
    romanpage = 0
    romanpage = 0 if int(ePub_options['input_pageOffset']) == 0 else romanpage + int(ePub_options['input_pageOffset'])

    frontmatter = True
    alphapetes = list(string.ascii_lowercase)
    alphapetesindex = 0
    if pageformat.upper() == 'NO' or pageformat.upper() == 'N' or pageformat.upper() == 'FALSE':
        for htmlname in fist_levels:
            pageIDs = htmlname.find_all(lambda tag: tag.get('epub:type') == 'pagebreak')
            if frontmatterRoman.upper() == 'NO' or frontmatterRoman.upper() == 'N' or frontmatterRoman.upper() == 'FALSE':
                for pageid in pageIDs:
                    pagenumber += 1
                    pagevalue = pagenumber
                    pageid['id'] = f'{prefix}{pagevalue}'
            else:
                for pageid in pageIDs:
                    if htmlname['epub:type'] in frontmatters and frontmatter:
                        if romanpage >= 0:
                            romanpage += 1
                            pagevalue = romanNumberGenartion(romanpage)
                            pageid['id'] = f'{prefix}{pagevalue}'
                        else:
                            pagevalue = alphapetes[alphapetesindex]
                            pageid['id'] = f'{prefix}{pagevalue}'
                            alphapetesindex +=1
                            romanpage += 1
                    else:
                        frontmatter = False
                        pagenumber += 1
                        pagevalue = pagenumber
                        pageid['id'] = f'{prefix}{pagevalue}'

            with open(file, "w", encoding="UTF-8") as f:
                f.write(str(htmlObject))
    else:
        FMvisited = False
        BMvistied = False
        visitedfiles = []
        for j, pagePattern in enumerate(pageIDpatterns):
            chapno = 0
            if not FMvisited:
                pagenumber = 0
            if not BMvistied:
                bmpagenumber = 0
            prefix = pagePattern[0]
            chapterRestart = pagePattern[1]
            chapprefix = pagePattern[2]

            pattern = pagePattern[3]
            chap_no_roman = pagePattern[4]
            targetEpubType = pagePattern[5]
            frontmatterRoman = pagePattern[6]
            pagenumber = 0 if int(ePub_options['input_pageOffset']) == 0 else pagenumber + int(
                ePub_options['input_pageOffset'])
            romanpage = 0 if int(ePub_options['input_pageOffset']) == 0 else pagenumber + int(
                ePub_options['input_pageOffset'])
            for i, htmlname in enumerate(fist_levels):
                pageIDs = htmlname.find_all(lambda tag: tag.get('epub:type') == 'pagebreak')
                mainsection_epubtype = htmlname['epub:type'] if 'epub:type' in htmlname.attrs else None
                if mainsection_epubtype in bodymatters:
                    if mainsection_epubtype == targetEpubType and i not in visitedfiles:
                        visitedfiles.append(i)
                        pagenumber = 0
                        chapno += 1
                        for pageid in pageIDs:
                            pagenumber += 1
                            if chap_no_roman.upper() == "YES" or chap_no_roman.upper() == "Y" or chap_no_roman.upper() == "TRUE":
                                temp = chapno
                                chapno = romanNumberGenartion(chapno).upper()
                                try:
                                    newpattern = pattern.format(chapprefix=chapprefix, prefix=prefix,
                                                             chapno=chapno)
                                except:
                                    errorlog('..', filename,
                                             "Error: incorrect systax in pagelist in config xml file")
                                pagevalue = newpattern
                                pageid['id'] = f'{prefix}{pagevalue}{pagenumber}'
                                chapno = temp
                            else:
                                try:
                                    newpattern = pattern.format(chapprefix=chapprefix, prefix=prefix,
                                                                chapno=chapno)
                                except:
                                    errorlog('..', filename,
                                             "Error: incorrect systax in pagelist in config xml file")
                                pagevalue = newpattern
                                pageid['id'] = f'{prefix}{pagevalue}{pagenumber}'
                elif mainsection_epubtype in frontmatters and targetEpubType == 'frontmatter':
                    FMvisited = True
                    if i not in visitedfiles:
                        visitedfiles.append(i)
                        for pageid in pageIDs:
                            pagenumber += 1
                            romanpage +=1
                            if frontmatterRoman.upper() == "YES" or frontmatterRoman.upper() == "Y" or frontmatterRoman.upper() == "TRUE":
                                temp = chapno
                                chapno = romanNumberGenartion(chapno).upper()
                                try:
                                    newpattern = pattern.format(chapprefix=chapprefix, prefix=prefix,
                                                                chapno=chapno)
                                except:
                                    errorlog('..', filename,
                                             "Error: incorrect systax in pagelist in config xml file")
                                if romanpage >= 0:
                                    pagevalue = f'{newpattern}{romanNumberGenartion(romanpage)}'
                                    pageid['id'] = f'{prefix}{pagevalue}'
                                    chapno = temp
                                else:
                                    pagevalue = f'{newpattern}{alphapetes[alphapetesindex]}'
                                    pageid['id'] = f'{prefix}{pagevalue}'
                                    alphapetesindex += 1
                                    romanpage += 1
                                    chapno = temp
                            else:
                                temp = chapno
                                chapno = romanNumberGenartion(chapno)
                                chapno = chapno.upper()
                                try:
                                    newpattern = pattern.format(chapprefix=chapprefix, prefix=prefix,
                                                                chapno=chapno)
                                except:
                                    errorlog('..', filename,
                                             "Error: incorrect systax in pagelist in config xml file")
                                if romanpage >= 0:
                                    pagevalue = f'{newpattern}{pagenumber}'
                                    pageid['id'] = f'{prefix}{pagevalue}'
                                    chapno = temp
                                else:
                                    pagevalue = f'{newpattern}{alphapetes[alphapetesindex]}'
                                    pageid['id'] = f'{prefix}{pagevalue}'
                                    alphapetesindex += 1
                                    romanpage += 1
                                    chapno = temp
                elif mainsection_epubtype in backmatters and i not in visitedfiles:
                    if targetEpubType == mainsection_epubtype:
                        visitedfiles.append(i)
                        BMvistied = True
                        pagenumber = 0
                        chapno += 1
                        for pageid in pageIDs:
                            pagenumber += 1
                            try:
                                newpattern = pattern.format(chapprefix=chapprefix, prefix=prefix,
                                                            chapno=chapno)
                            except:
                                errorlog('..', filename,
                                         "Error: incorrect systax in pagelist in config xml file")

                            pagevalue = f'{newpattern}{pagenumber}'
                            pageid['id'] = f'{prefix}{pagevalue}'
                    if targetEpubType == 'backmatter':
                        visitedfiles.append(i)
                        BMvistied = True
                        pagenumber = 0
                        chapno += 1
                        for pageid in pageIDs:
                            pagenumber += 1
                            try:
                                newpattern = pattern.format(chapprefix=chapprefix, prefix=prefix,
                                                            chapno=chapno)
                            except:
                                errorlog('..', filename,
                                         "Error: incorrect systax in pagelist in config xml file")

                            pagevalue = f'{newpattern}{pagenumber}'
                            pageid['id'] = f'{prefix}{pagevalue}'
                with open(file, "w", encoding="UTF-8") as f:
                    f.write(str(htmlObject))

def epubFileformation(metadetails, filename, ePub_options):
    if ePub_options['input_HTMLFolderName'] == "No Folder":
        os.chdir('..')
    else:
        os.chdir('../..')
    shutil.make_archive(os.getcwd(), "zip", os.getcwd())
    os.chdir('..')
    os.rename(f'{filename}.zip', f"{metadetails[0]['e-ISBN']}_EPUB.epub")
    epubfile = f"{metadetails[0]['e-ISBN']}_EPUB.epub"
    try:
        validate = EpubCheck(epubfile)
    except:
        messagebox.showerror("Error", "Error in ePub Checker")

    try:
        with open(f"{epubfile}_epubchecker.log", "x", encoding="UTF-8") as epublog:
            pass
    except:
        messagebox.showerror("Error", "Problem in creating ePub checker")
    try:
        with open(f"{epubfile}_epubchecker.log", "w", encoding="UTF-8") as epublog:
            if validate.valid:
                epublog.write(f"{epubfile} is valid!")
            else:
                for mess in validate.messages:
                    epublog.write(f"{mess.id}: {mess.level}: {mess.location} - {mess.message}\n")
    except:
        messagebox.showerror("Error", "Problem in creating ePub checker")

def lableCreation(lableContent, link_lable_info, ePub_options, lang):
    lableHTML = BeautifulSoup(lableContent, "html.parser")
    possible_fig_lables_sigular = link_lable_info.find(f"{lang}").find("Figure").find("sigular").text.split("|")
    possible_fig_lables_plural = link_lable_info.find(f"{lang}").find("Figure").find("plural").text.split("|")


def linkProcess(linksOptions, ePub_options, file_order, link_lable_file_info):
    link_lable_info = BeautifulSoup(link_lable_file_info, "xml")
    lang, lang_code = ePub_options['input_lang'].split("-")
    for file in file_order:
        with open(file, "r", encoding="UTF-8") as forlink:
            lableContent = forlink.read()
            lableContent = lableCreation(lableContent, link_lable_info, ePub_options, lang)


def ePub_Creation(inputfiles, ePub_options, mapping_content, entity_file, split_info, heading_filename_info,
                  metadetails, navItemfile_info, linksOptions, link_lable_file_info):
    global outputPath
    language, langCode = ePub_options['input_lang'].split("-")
    ISBN = metadetails[0]['e-ISBN']
    if ePub_options['input_HTMLFileName'] == "ISBN":
        ePub_options['input_HTMLFileName'] = ISBN
    for file in inputfiles:
        os.chdir(outputPath)
        filename, file_ext = os.path.splitext(file)
        try:
            os.mkdir(f"{filename}")
        except:
            pass
        os.mkdir(f"{filename}/META-INF")
        if ePub_options['input_RootFolderName'] == "ISBN":
            ePub_options['input_RootFolderName'] = ISBN
        os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}")
        shutil.copy2(os.path.join(mapping_content_path, "container.xml"), f"{filename}/META-INF")
        with open(os.path.join(mapping_content_path, "container.xml"), "r", encoding="UTF-8") as xml_file:
            container_xml_content = xml_file.read()
            container_xml = BeautifulSoup(container_xml_content, "xml")

        container_rootfile = container_xml.find("rootfile")
        container_rootfile['full-path'] = f"{ePub_options['input_RootFolderName']}/{ePub_options['input_opfName']}.opf"
        with open(os.path.join(f"{filename}/META-INF", "container.xml"), "w", encoding="UTF-8") as xml_file:
            xml_file.write(str(container_xml))

        with open(os.path.join(mapping_content_path, "00_Cover.xhtml"), "r", encoding="UTF-8") as cover_file:
            coverhtml_contnet = cover_file.read()
            coverhtml = BeautifulSoup(coverhtml_contnet, "html.parser")

        headtag = coverhtml.find("head")
        htmltag = coverhtml.find("html")
        htmltag['lang'] = langCode
        htmltag['xml:lang'] = langCode
        if ePub_options['input_CSSFilesPath']:
            for cssfile in ePub_options['input_CSSFilesPath']:
                linktag = coverhtml.new_tag("link")
                linktag["rel"] = "stylesheet"
                linktag["type"] = "text/css"
                css = os.path.basename(cssfile)
                if ePub_options['input_CSSFolderName'] != "No Folder" or ePub_options[
                    'input_HTMLFolderName'] != "No Folder":
                    if ePub_options['input_CSSFolderName'] != "No Folder" and ePub_options[
                        'input_HTMLFolderName'] != "No Folder":
                        linktag["href"] = f"../{ePub_options['input_CSSFolderName']}/{css}"
                    elif ePub_options['input_CSSFolderName'] != "No Folder":
                        linktag["href"] = f"{ePub_options['input_CSSFolderName']}/{css}"
                    elif ePub_options['input_HTMLFolderName'] != "No Folder":
                        linktag["href"] = f"../{css}"
                headtag.append(linktag)
        coverimage = coverhtml.find("img")
        if ePub_options['input_HTMLFolderName'] != "No Folder":
            coverfilename = os.path.basename(ePub_options['input_CoverImagePath'])
            coverimage['src'] = f"../Images/{coverfilename}"
            coverimage['id'] = "cover"

        try:
            mimetype = open(f"{filename}/mimetype", "x", encoding="UTF-8")
            mimetype.close()
        except:
            pass
        mimetype = open(f"{filename}/mimetype", "w", encoding="UTF-8")
        mimetype.write("application/epub+zip")
        mimetype.close()

        if ePub_options['input_HTMLFolderName'] != "No Folder":
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_HTMLFolderName']}")
            shutil.copy2(os.path.join(mapping_content_path, "00_Cover.xhtml"),
                         f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_HTMLFolderName']}")
            with open(os.path.join(
                    f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_HTMLFolderName']}",
                    "00_Cover.xhtml"), "w", encoding="UTF-8") as cover_file:
                cover_file.write(str(coverhtml))
        else:
            shutil.copy2(os.path.join(mapping_content_path, "00_Cover.xhtml"),
                         f"{filename}/{ePub_options['input_RootFolderName']}/")
            with open(os.path.join(f"{filename}/{ePub_options['input_RootFolderName']}", "00_Cover.xhtml"),
                      "w", encoding="UTF-8") as cover_file:
                cover_file.write(str(coverhtml))
        if ePub_options["input_CSSFilesPath"]:
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_CSSFolderName']}")
            shutil.copytree(ePub_options['input_CSSFilesPath'],
                            f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_CSSFolderName']}",
                            dirs_exist_ok=True)

        os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/Images")

        shutil.copy2(ePub_options['input_CoverImagePath'], f"{filename}/{ePub_options['input_RootFolderName']}/Images")
        if ePub_options['input_ImageFilesPath']:
            shutil.copytree(ePub_options['input_ImageFilesPath'],
                            f"{filename}/{ePub_options['input_RootFolderName']}/Images", dirs_exist_ok=True)

        if ePub_options['input_FontFilesPath']:
            allowed_fonts = [".ttf", ".otf", ".WOFF", ".WOFF2"]
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/Fonts")
            shutil.copytree(ePub_options['input_FontFilesPath'],
                            f"{filename}/{ePub_options['input_RootFolderName']}/Fonts", dirs_exist_ok=True)

        if ePub_options['input_JSFilesPath']:
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/script")
            shutil.copytree(ePub_options['input_JSFilesPath'],
                            f"{filename}/{ePub_options['input_RootFolderName']}/script", dirs_exist_ok=True)

        if ePub_options['input_AudioFilesPath']:
            allowed_audios = [".mp3", ".mp4"]
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/Media")
            shutil.copytree(ePub_options['input_AudioFilesPath'],
                            f"{filename}/{ePub_options['input_RootFolderName']}/Media", dirs_exist_ok=True)

        if ePub_options['input_AudioScriptFilesPath']:
            allowed_audioscripts = [".smil"]
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/Transcript")
            shutil.copytree(ePub_options['input_AudioScriptFilesPath'],
                            f"{filename}/{ePub_options['input_RootFolderName']}/Transcript", dirs_exist_ok=True)

        pageIDgenration(file, mapping_content, ePub_options, filename, split_info)
        file_order = file_split(file, ePub_options, mapping_content, entity_file, split_info, heading_filename_info)

        file_order = opfFileCreation(ePub_options, metadetails, filename, file_order)
        navFileCreation(ePub_options, metadetails, file_order, mapping_content, navItemfile_info, filename)
        if ePub_options['input_HTMLFolderName'] == "No Folder":
            listfiles = os.listdir(os.getcwd())
            inputfiles = []
            for listfile in listfiles:
                if listfile.endswith('.html') or listfile.endswith('.xhtml') or listfile.endswith('.htm'):
                    inputfiles.append(listfile)
        else:
            inputfiles = os.listdir(os.path.join(os.getcwd(), f"{ePub_options['input_HTMLFolderName']}"))
            os.chdir(os.path.join(os.getcwd(), f"{ePub_options['input_HTMLFolderName']}"))
        tag_nested_cleanup(inputfiles, mapping_content, ePub_options["input_FileSplit"])
        linkProcess(linksOptions, ePub_options, file_order, link_lable_file_info)
        epubFileformation(metadetails,filename, ePub_options)

def call_backfiles(field):
    global cssfiles_path
    cssfiles_path = select_files(field)


def select_Path(field):
    selectPath = tk.filedialog.askdirectory()
    field.delete(0, "end")
    field.insert(0, selectPath)
    field.focus_set()
    return selectPath


def select_files(field):
    selectPath = tk.filedialog.askopenfilenames(filetypes=[("All files", "*.*")])
    field.delete(0, "end")
    field.insert(0, selectPath)
    field.focus_set()
    return selectPath


def select_file(field, file_type):
    selectPath = tk.filedialog.askopenfilename(filetypes=[*file_type, ("All files", "*.*")])
    field.delete(0, "end")
    field.insert(0, selectPath)
    field.focus_set()
    return selectPath


def xhtml_validation(file):
    file_name, ext = os.path.splitext(file)
    try:
        parcer = etree.XMLParser(dtd_validation=False, encoding="UTF-8")
        etree.parse(file, parcer)
        return True
    except etree.XMLSyntaxError as e:
        try:
            error_log = open(f"{file_name}_error.log", "x", encoding="UTF-8")
            error_log.close()
            error_log = open(f"{file_name}_error.log", "a", encoding="UTF-8")
        except:
            error_log = open(f"{file_name}_error.log", "a", encoding="UTF-8")
        for error in e.error_log:
            error_log.write(f'{error.filename}, line {error.line}, column {error.column}: {error.message}\n')
        error_log.close()
        return False
    except Exception as e:
        try:
            error_log = open(f"{file_name}_error.log", "x", encoding="UTF-8")
            error_log.close()
            error_log = open(f"{file_name}_error.log", "a", encoding="UTF-8")
        except:
            error_log = open(f"{file_name}_error.log", "a", encoding="UTF-8")
        error_log.write(f'Error occurred while parsing the file: {e}')
        error_log.close()
        return False


# Prgram Start Here
# __________________
path = os.getcwd()
gui_data_file = Et.parse("gui_confi.xml")
gui_data_root = gui_data_file.getroot()
PublisherName_list = gui_data_root.find("PublisherName").text.split(",")
PublisherName_list.sort()
Language_list = gui_data_root.find("Language").text.split(",")
epubVersion_list = gui_data_root.find("epubVersion").text.split(",")
ePubStructure_list = gui_data_root.find("ePubStructure").text.split(",")
OpfName_list = gui_data_root.find("OpfName").text.split(",")
NCXName_list = gui_data_root.find("NCXName").text.split(",")
HTMLFileName_list = gui_data_root.find("HTMLFileName").text.split(",")
EntityType_list = gui_data_root.find("EntityType").text.split(",")
fileSplit_list = gui_data_root.find("fileSplit").text.split(",")
footnoteMovement_list = gui_data_root.find("footnoteMovement").text.split(",")
Navigation_list = gui_data_root.find("Navigation").text.split(",")
RootFolderName_list = gui_data_root.find("RootFolderName").text.split(",")
HTMLFolderName_list = gui_data_root.find("HTMLFolderName").text.split(",")
CSSFolderName_list = gui_data_root.find("CSSFolderName").text.split(",")
project_confi_file = Et.parse("project_confi.xml")
project_confi_root = project_confi_file.getroot()
project_list = project_confi_root.findall("publisher")


mapping_content_path = os.path.join(path, "Support")
os.chdir(mapping_content_path)
split_info_file = open("Split.xml", "r", encoding="UTF-8")
split_info = split_info_file.read()
split_info_file.close()

heading_filename_file = open("heading_filename.xml", "r", encoding="UTF-8")
heading_filename_info = heading_filename_file.read()
heading_filename_file.close()

link_lable_file = open("link_lable.xml", "r", encoding="UTF-8")
link_lable_file_info = link_lable_file.read()
link_lable_file.close()

navItemfile = open("lang_nav.xml", "r", encoding="UTF-8")
navItemfile_info = navItemfile.read()
navItemfile.close()


def conversion():
    warning_label.config(text="")
    global mappping_doc_name
    global entity_file
    global mapping_content
    global split_info
    global outputPath
    global heading_filename_info
    global navItemfile_info
    global link_lable_file_info
    user_inputfile = inputPath.get()
    path, input_htmlfile = os.path.split(user_inputfile)
    epubOptions = {
        "input_publisher": publisher_info.get(),
        "input_jobno": job_no_filed.get(),
        "input_lang": lang_info.get(),
        "input_epub_version": ePub_version_info.get(),
        "input_epub_structure": ePub_type_info.get(),
        "input_HTMLFileName": HTML_file_info.get(),
        "input_EntityType": entity_type_info.get(),
        "input_FileSplit": fileSplit_info.get(),
        "input_footnoteMovement": footnoteMovement_info.get(),
        "input_Navigation": Navigation_info.get(),
        "input_RootFolderName": root_folder_info.get(),
        "input_HTMLFolderName": HTML_folder_info.get(),
        "input_CSSFolderName": CSS_folder_info.get(),
        "input_opfName": OpfName_info.get(),
        "input_NCXName": ncx_file_info.get(),
        "input_CSSFilesPath": css_path_filed.get(),
        "input_CoverImagePath": cover_path_filed.get(),
        "input_ImageFilesPath": image_path_filed.get(),
        "input_FontFilesPath": font_path_filed.get(),
        "input_JSFilesPath": js_path_filed.get(),
        "input_AudioFilesPath": audio_path_filed.get(),
        "input_AudioScriptFilesPath": audioScript_filed.get(),
        "input_MetaExcel": meta_exel_filed.get(),
        "input_pageOffset": int(pageOffset_filed.get()),
        "input_includeTable": tableInclude.get(),
        "input_includeFigure": figureInclude.get(),
        "input_checkHyphen": hyphen.get()
    }
    linksOptions = {"Figure": figurelink.get(), "Table": tablelink.get(), "Chapter": chapterlink.get(),
                    "Section": sectionlink.get(), "Chap/Part TOC": ChapTOClink.get(),
                    "Footnotes/Endnotes": footnotelink.get(),
                    "Web/eMail": weblink.get(), "Reference": referencelink.get(), "Index": indexlink.get(),
                    "See/See also": seelink.get(), "Glossary/Keywords": Keywordslink.get()}
    if publisher_info.get() == "Common":
        mappping_doc_name = "Tagmapping_config.xml"
    else:
        for child in project_list:
            for subchild in child:
                if publisher_info.get() == subchild.text:
                    mappping_doc_name = child.find('mappingDoc').text
    try:
        entity_file = open(os.path.join(mapping_content_path, "entity.ini"), "r", encoding="UTF-8")
    except FileNotFoundError:
        submitButton.config(state="normal")
        messagebox.showerror("Error","\"entity.ini\" is not found  in support folder")
    if epubOptions['input_checkHyphen']:

        try:
            language, language_code = epubOptions['input_lang'].split("-")
            exception_filename = f"{language.lower()}.ini"
            exception_file = open(os.path.join(mapping_content_path, exception_filename), "r", encoding="utf8")
        except:
            messagebox.showerror("Error", f"\"{exception_filename}\" is not found in support folder")
    try:
        mapping_file = open(os.path.join(mapping_content_path, f"{mappping_doc_name}"), "r", encoding="UTF-8")
    except:
        submitButton.config(state="normal")
        messagebox.showerror("Error",
                             f"{mappping_doc_name} is missing!, \n Check Support folders and Project Confic XML file")
    mapping_content = mapping_file.read()
    mapping_content = mapping_content.replace("[", "\[")
    mapping_content = mapping_content.replace("]", "\]")
    mapping_file.close()

    try:
        os.chdir(path)
    except:
        warning_label["text"] = "Invalid Path"
        submitButton.config(state="normal")
        path = ""
        inputPath.delete(0, 'end')

    def jobnoChecking(epubOptions, metadata_exel):
        if "," in epubOptions['input_jobno']:
            epubOptions['input_jobno'].replace(", ", ",")
            multijobs = epubOptions['input_jobno'].split(",")
            for job in metadata_exel['Job No']:
                for job1 in multijobs:
                    if job == job1:
                        pass
                    else:

                        return False
            return True
        else:
            for job in metadata_exel['Job No']:
                if job == epubOptions['input_jobno']:
                    return True
        return False

    if not job_no_filed.get():
        warning_label["text"] = "Enter Job no."
        submitButton.config(state="normal")
    elif not epubOptions['input_CoverImagePath']:
        warning_label["text"] = "Please choose cover image!"
        submitButton.config(state="normal")
    elif not epubOptions['input_MetaExcel']:
        warning_label["text"] = "Meta Excel Missing! Please upload Meta Info"
        submitButton.config(state="normal")
    else:
        metadata_exel = pandas.read_excel(epubOptions['input_MetaExcel'], header=0,
                                          sheet_name=f'{epubOptions["input_publisher"]}')
        isJobPresent = jobnoChecking(epubOptions, metadata_exel)
        if not isJobPresent:
            messagebox.showerror("Jobno Missing", "Job no. is missing Metadata excel")
            submitButton.config(state="normal")
        else:
            metadetails = metadata_exel.loc[metadata_exel['Job No'] == epubOptions['input_jobno']]
            metadetails = metadetails.to_dict('records')
            files = os.listdir(path)
            try:
                os.mkdir("Output")
            except FileExistsError:
                try:
                    shutil.rmtree("Output")
                    os.mkdir("Output")
                except:
                    warning_label["text"] = "Problem with creating Output folder"
            file_alllowed = [".html", ".xhtml", ".htm"]

            try:
                if xhtml_validation(input_htmlfile):
                    outputPath = os.path.join(path, "Output")
                    shutil.copy2(user_inputfile, outputPath)
                else:
                    try:
                        os.mkdir("Invalid_file")
                    except:
                        messagebox.showerror("Error", "Invalid HTML File, Please check the error Report")
                    errorfile_path = os.path.join(path, "Invalid_file")
                    shutil.copy2(user_inputfile, errorfile_path)

            except:
                warning_label["text"] = f"{input_htmlfile} is already exit!"
            progress_bar['value'] = 10
            os.chdir(outputPath)
            if epubOptions["input_footnoteMovement"] == "Level 1":
                mapping_content = re.sub(r'to_move_under="([^"<]*)"', 'to_move_under="section1"', mapping_content,
                                         flags=re.IGNORECASE)
            elif epubOptions["input_footnoteMovement"] == "Level 2":
                mapping_content = re.sub(r'to_move_under="([^"<]*)"', 'to_move_under="section1|section2"',
                                         mapping_content,
                                         flags=re.IGNORECASE)
            elif epubOptions["input_footnoteMovement"] == "Level 3":
                mapping_content = re.sub(r'to_move_under="([^"<]*)"', 'to_move_under="section1|section2|section3"',
                                         mapping_content,
                                         flags=re.IGNORECASE)

            inputfiles = os.listdir(outputPath)
            if inputfiles:
                pre_replace(inputfiles, mapping_content)
                progress_bar['value'] = 20
                tag_nested(inputfiles, mapping_content)
                progress_bar['value'] = 30
                listing(inputfiles, mapping_content)
                progress_bar['value'] = 40
                text_movement(inputfiles, mapping_content)
                progress_bar['value'] = 50
                tag_groupping(inputfiles, mapping_content)
                progress_bar['value'] = 60
                tag_mapping(inputfiles, mapping_content)
                progress_bar['value'] = 70
                if epubOptions['input_checkHyphen']:
                    lang_choice = 2 if language == "German".lower() else 1
                    input_content=""
                    for file in inputfiles:
                        file_handler = open(file, "r", encoding="utf8")
                        file_content = file_handler.read()
                        input_content += file_content
                    try:
                        Hyphen_Space.hyphen_replace(exception_file, input_content, inputfiles, lang_choice)
                    except UnboundLocalError:
                        pass
                progress_bar['value'] = 80

                list_tagcleaup(inputfiles, mapping_content)
                progress_bar['value'] = 90
                post_replace(inputfiles, mapping_content)
                ePub_Creation(inputfiles, epubOptions, mapping_content, entity_file, split_info, heading_filename_info,
                              metadetails, navItemfile_info, linksOptions, link_lable_file_info)
                progress_bar['value'] = 100
            messagebox.showinfo("Info", "ePub Converted Sucessfully!")
            submitButton.config(state="normal")
            progress_bar.grid_forget()
            warning_label.grid(row=0, column=0)


class GUI:
    def __init__(self, master, width, height):
        self.master = master
        self.width = width
        self.height = height
        self.master.geometry(f"{width}x{height}")
        self.center_window()

    def center_window(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width / 2) - (self.width / 2)
        y = (screen_height / 2) - (self.height / 2)

        # set the window geometry
        self.master.geometry(f"{self.width}x{self.height}+{int(x)}+{int(y)}")


uiWindow = tk.Tk()
gui = GUI(uiWindow, 850, 680)
uiWindow.title("Epub Conversion Tool - Version 1.0.0")
icon = PhotoImage(file=f"{path}/LD_icon.png")
excel_icon = PhotoImage(file=f"{path}/excel-download-icon.gif")
uiWindow.iconphoto(True, icon)
frame1 = tk.Frame(uiWindow)
frame2 = tk.Frame(uiWindow)
frame3 = tk.LabelFrame(uiWindow, text="ePub Information", font=10)
frame3_1 = tk.LabelFrame(frame3, text="Meta Info")
frame3_2 = tk.LabelFrame(frame3, text="Folder Option")
frame3_3 = tk.LabelFrame(frame3, text="Links")
frame3_4 = tk.LabelFrame(frame3, text="Others", pady=10, padx=10)
frame4 = tk.LabelFrame(uiWindow, text="Media Files and Paths", font=10)
frame5 = tk.Frame(uiWindow)
frame6 = tk.Frame(uiWindow)

frame1.grid(row=0, column=0, columnspan=2, sticky="we")
frame2.grid(row=1, column=0, columnspan=2)
frame3.grid(row=2, column=0)
frame3_1.grid(row=0, column=0, padx=5, pady=5, sticky="ns")
frame3_2.grid(row=0, column=1, padx=5, pady=5, sticky="ns")
frame3_3.grid(row=1, column=0, padx=5, pady=5, sticky="ns")
frame3_4.grid(row=1, column=1, padx=5, pady=5, sticky="w")
frame4.grid(row=3, column=0, columnspan=2, pady=5, ipady=5)
frame5.grid(row=4, column=0, columnspan=2, pady=5)
frame6.grid(row=5, column=0, columnspan=2)
# Frame 1
heading = tk.Label(frame1, text="HTML to ePub", fg="white", bg="#c5161d", font=("Arial Black", 20), width=45,
                   relief="raised")
heading.grid(row=0, column=0)
# Frame 2
inputLable = tk.Label(frame2, text="Enter path: ", font="sans-serif", pady=10)
inputPath = tk.Entry(frame2, width=30, text=path)
input_selectPath = tk.Button(frame2, text="...", command=lambda: select_file(inputPath, [("HTML files", "*.html"),("XHTML files","*.xhtml")]), padx=3, border=1,
                             relief="solid")
inputLable.grid(row=0, column=0)
inputPath.grid(row=0, column=1)
input_selectPath.grid(row=0, column=2, padx=3)

# Frame3
# Frame 3_1, Meta Info, 1st Column
publisher_lable = tk.Label(frame3_1, text="Publisher:")
publisher_info = tk.StringVar(frame3_1)
publisher_info.set("Common")
publisher_filed = ttk.Combobox(frame3_1, values=PublisherName_list, textvariable=publisher_info)

job_no = tk.Label(frame3_1, text="Job No*:", fg="red")
job_no_filed = tk.Entry(frame3_1, width=23)
lang = tk.Label(frame3_1, text="Language:")
lang_info = tk.StringVar(frame3_1)
lang_info.set(Language_list[0])
lang_filed = ttk.Combobox(frame3_1, values=Language_list, textvariable=lang_info)

ePub_version = tk.Label(frame3_1, text="ePub Version:")
ePub_version_info = tk.StringVar(frame3_1)
ePub_version_info.set(epubVersion_list[0])
ePub_version_filed = ttk.Combobox(frame3_1, values=epubVersion_list, textvariable=ePub_version_info)

ePub_type = tk.Label(frame3_1, text="ePub Structure:")
ePub_type_info = tk.StringVar(frame3_1)
ePub_type_info.set(ePubStructure_list[0])
ePub_type_filed = ttk.Combobox(frame3_1, values=ePubStructure_list, textvariable=ePub_type_info)

publisher_lable.grid(row=0, column=0, pady=3, padx=3, sticky="e")
publisher_filed.grid(row=0, column=1, pady=3, padx=8, sticky="w")
job_no.grid(row=1, column=0, pady=3, padx=3, sticky="e")
job_no_filed.grid(row=1, column=1, pady=3, padx=8, sticky="w")
lang.grid(row=2, column=0, pady=3, padx=3, sticky="e")
lang_filed.grid(row=2, column=1, pady=3, padx=8, sticky="w")
ePub_version.grid(row=3, column=0, pady=3, padx=3, sticky="e")
ePub_version_filed.grid(row=3, column=1, pady=3, padx=8, sticky="w")
ePub_type.grid(row=4, column=0, pady=3, padx=3, sticky="e")
ePub_type_filed.grid(row=4, column=1, pady=3, padx=8, sticky="w")

# Frame 3_1, Meta Info, 2nd Column


HTML_file = tk.Label(frame3_1, text="HTML File Name:")
HTML_file_info = tk.StringVar(frame3_1)
HTML_file_info.set(HTMLFileName_list[0])
HTML_file_filed = ttk.Combobox(frame3_1, values=HTMLFileName_list, textvariable=HTML_file_info)
entity_type = tk.Label(frame3_1, text="Entity Type:")
entity_type_info = tk.StringVar(frame3_1)
entity_type_info.set(EntityType_list[0])
entity_type_filed = ttk.Combobox(frame3_1, values=EntityType_list, textvariable=entity_type_info)
fileSplit = tk.Label(frame3_1, text="File Split:")
fileSplit_info = tk.StringVar(frame3_1)
fileSplit_info.set(fileSplit_list[0])
fileSplit_filed = ttk.Combobox(frame3_1, values=fileSplit_list, textvariable=fileSplit_info)

footnoteMovement = tk.Label(frame3_1, text="Footnote Movement:")
footnoteMovement_info = tk.StringVar(frame3_1)
footnoteMovement_info.set(footnoteMovement_list[0])
footnoteMovement_filed = ttk.Combobox(frame3_1, values=footnoteMovement_list, textvariable=footnoteMovement_info)

Navigation = tk.Label(frame3_1, text="Navigation:")
Navigation_info = tk.StringVar(frame3_1)
Navigation_info.set(Navigation_list[0])
Navigation_filed = ttk.Combobox(frame3_1, values=Navigation_list, textvariable=Navigation_info)

HTML_file.grid(row=0, column=2, pady=3, padx=3, sticky="e")
HTML_file_filed.grid(row=0, column=3, pady=3, padx=8)
entity_type.grid(row=1, column=2, pady=3, padx=3, sticky="e")
entity_type_filed.grid(row=1, column=3, pady=3, padx=8)
fileSplit.grid(row=2, column=2, pady=3, padx=3, sticky="e")
fileSplit_filed.grid(row=2, column=3, pady=3, padx=8)
footnoteMovement.grid(row=3, column=2, pady=3, padx=3, sticky="e")
footnoteMovement_filed.grid(row=3, column=3, pady=3, padx=8)
Navigation.grid(row=4, column=2, pady=3, padx=3, sticky="e")
Navigation_filed.grid(row=4, column=3, pady=3, padx=8)

# Frame 3_2, Folder Info, 1nd Column

root_folder = tk.Label(frame3_2, text="Root Folder Name:")
root_folder_info = tk.StringVar(frame3_2)
root_folder_info.set(RootFolderName_list[0])
root_folder_filed = ttk.Combobox(frame3_2, values=RootFolderName_list, textvariable=root_folder_info)
HTML_folder = tk.Label(frame3_2, text="HTML Folder Name:")
HTML_folder_info = tk.StringVar(frame3_2)
HTML_folder_info.set(HTMLFolderName_list[0])
HTML_folder_filed = ttk.Combobox(frame3_2, values=HTMLFolderName_list, textvariable=HTML_folder_info)
CSS_folder = tk.Label(frame3_2, text="CSS Folder Name:")
CSS_folder_info = tk.StringVar(frame3_2)
CSS_folder_info.set(CSSFolderName_list[0])
CSS_folder_filed = ttk.Combobox(frame3_2, values=CSSFolderName_list, textvariable=CSS_folder_info)

opf_file = tk.Label(frame3_2, text="OPF File Name:")
OpfName_info = tk.StringVar(frame3_2)
OpfName_info.set(OpfName_list[0])
opf_file_filed = ttk.Combobox(frame3_2, values=OpfName_list, textvariable=OpfName_info)
ncx_file = tk.Label(frame3_2, text="NCX File Name:")
ncx_file_info = tk.StringVar(frame3_2)
ncx_file_info.set(NCXName_list[0])
ncx_file_filed = ttk.Combobox(frame3_2, values=NCXName_list, textvariable=ncx_file_info, )

root_folder.grid(row=0, column=0, pady=3, padx=3, sticky="e")
root_folder_filed.grid(row=0, column=1, pady=3, padx=8)
HTML_folder.grid(row=1, column=0, pady=3, padx=3, sticky="e")
HTML_folder_filed.grid(row=1, column=1, pady=3, padx=8)
CSS_folder.grid(row=2, column=0, pady=3, padx=3, sticky="e")
CSS_folder_filed.grid(row=2, column=1, pady=3, padx=8)
opf_file.grid(row=3, column=0, pady=3, padx=3, sticky="e")
opf_file_filed.grid(row=3, column=1, pady=3, padx=8)
ncx_file.grid(row=4, column=0, pady=3, padx=3, sticky="e")
ncx_file_filed.grid(row=4, column=1, pady=3, padx=8)

# Frame 3_3, Links, 1nd Column
figurelink = tk.BooleanVar()
figlink_checkbox = tk.Checkbutton(frame3_3, text="Figure", variable=figurelink, width=15, anchor="w")
tablelink = tk.BooleanVar()
tablink_checkbox = tk.Checkbutton(frame3_3, text="Table", variable=tablelink)
footnotelink = tk.BooleanVar()
fnlink_checkbox = tk.Checkbutton(frame3_3, text="Footnotes/Endnotes", variable=footnotelink)
chapterlink = tk.BooleanVar()
chaplink_checkbox = tk.Checkbutton(frame3_3, text="Chapter/Part", variable=chapterlink)
sectionlink = tk.BooleanVar()
seclink_checkbox = tk.Checkbutton(frame3_3, text="Section", variable=sectionlink, width=15, anchor="w")
ChapTOClink = tk.BooleanVar()
ChapTOClink_checkbox = tk.Checkbutton(frame3_3, text="Chapter/Part TOC", variable=ChapTOClink)
weblink = tk.BooleanVar()
weblink_checkbox = tk.Checkbutton(frame3_3, text="Web/eMail", variable=weblink, width=15, anchor="w")
referencelink = tk.BooleanVar()
reflink_checkbox = tk.Checkbutton(frame3_3, text="Reference", variable=referencelink)
indexlink = tk.BooleanVar()
indexlink_checkbox = tk.Checkbutton(frame3_3, text="Index", variable=indexlink)
seelink = tk.BooleanVar()
seelink_checkbox = tk.Checkbutton(frame3_3, text="See/See also", variable=seelink, width=14, anchor="w")
Keywordslink = tk.BooleanVar()
Keywordslink_checkbox = tk.Checkbutton(frame3_3, text="Glossary/Keywords", variable=Keywordslink, width=14, anchor="w")

figlink_checkbox.grid(row=0, column=0, sticky="w")
tablink_checkbox.grid(row=1, column=0, sticky="w")
fnlink_checkbox.grid(row=2, column=0, sticky="w")
chaplink_checkbox.grid(row=0, column=1, sticky="w")
seclink_checkbox.grid(row=1, column=1, sticky="w")
ChapTOClink_checkbox.grid(row=2, column=1, sticky="w")
weblink_checkbox.grid(row=0, column=2, sticky="w")
reflink_checkbox.grid(row=1, column=2, sticky="w")
indexlink_checkbox.grid(row=2, column=2, sticky="w")
seelink_checkbox.grid(row=0, column=3, sticky="w")
Keywordslink_checkbox.grid(row=1, column=3, sticky="w")


# Frame 3_4, Others, 1nd Column
hyphen = tk.BooleanVar()
hyphen_checkbox = tk.Checkbutton(frame3_4, text="Hyphen Check", variable=hyphen, width=15, anchor="w")
tableInclude = tk.BooleanVar()
tableInclude_checkbox = tk.Checkbutton(frame3_4, text="Include Tables in Nav", variable=tableInclude)
figureInclude = tk.BooleanVar()
figureInclude_checkbox = tk.Checkbutton(frame3_4, text="Include Figures in Nav", variable=figureInclude)
pageOffset = tk.Label(frame3_4, text="Page offset:")
pageOffset_filed = tk.Entry(frame3_4, width=10)
pageOffset_filed.insert(0, "0")

hyphen_checkbox.grid(row=0, column=0, sticky="w", columnspan=2)
tableInclude_checkbox.grid(row=1, column=0, sticky="w", columnspan=2)
figureInclude_checkbox.grid(row=2, column=0, sticky="w", columnspan=2)
pageOffset.grid(row=3, column=0, sticky="w")
pageOffset_filed.grid(row=3, column=1, sticky="w")



# Frame 4, Media Files,
# 1st Column
css_path = tk.Label(frame4, text="CSS Path:")
css_path_filed = tk.Entry(frame4)
css_selectPath = tk.Button(frame4, text="...", command=lambda: select_Path(css_path_filed), padx=3)

cover_path = tk.Label(frame4, text="Cover Image*:", fg="red")
cover_path_filed = tk.Entry(frame4)
cover_selectPath = tk.Button(frame4, text="...", command=lambda: select_file(cover_path_filed, [("PNG files", "*.png"),
                                                                                                ("jpeg files",
                                                                                                 "*.jpg")]), padx=3)
image_path = tk.Label(frame4, text="Images Path:")
image_path_filed = tk.Entry(frame4)
image_selectPath = tk.Button(frame4, text="...", command=lambda: select_Path(image_path_filed), padx=3)

font_path = tk.Label(frame4, text="Fonts Path:")
font_path_filed = tk.Entry(frame4)
font_selectPath = tk.Button(frame4, text="...", command=lambda: select_Path(font_path_filed), padx=3)

css_path.grid(row=0, column=0, pady=3, padx=3, sticky="e")
css_path_filed.grid(row=0, column=1, pady=3, padx=8)
css_selectPath.grid(row=0, column=2, padx=8)

cover_path.grid(row=1, column=0, pady=3, padx=3, sticky="e")
cover_path_filed.grid(row=1, column=1, pady=3, padx=8)
cover_selectPath.grid(row=1, column=2, padx=8)

image_path.grid(row=2, column=0, pady=3, padx=3, sticky="e")
image_path_filed.grid(row=2, column=1, pady=3, padx=8)
image_selectPath.grid(row=2, column=2, padx=8)
font_path.grid(row=3, column=0, pady=3, padx=3, sticky="e")
font_path_filed.grid(row=3, column=1, pady=3, padx=8)
font_selectPath.grid(row=3, column=2, padx=8)


# Frame 4, 2nd Column

def dowload_excel():
    excel_loc = f"{path}/Support/Meta_Template.xlsx"
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="Meta_Template.xlsx",
                                             filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
    shutil.copyfile(excel_loc, file_path)
    tk.messagebox.showinfo("Download Complete", "The template file has been downloaded.")


js_path = tk.Label(frame4, text="JS Path:")
js_path_filed = tk.Entry(frame4)
js_selectPath = tk.Button(frame4, text="...", command=lambda: select_Path(js_path_filed), padx=3)

audio_path = tk.Label(frame4, text="Audios and Vidoes Path:")
audio_path_filed = tk.Entry(frame4)
audio_selectPath = tk.Button(frame4, text="...", command=lambda: select_Path(audio_path_filed), padx=3)

audioScript_path = tk.Label(frame4, text="Audio Script Path:")
audioScript_filed = tk.Entry(frame4)
audioScript_selectpath = tk.Button(frame4, text="...", command=lambda: select_Path(audioScript_filed), padx=3)

meta_exel = tk.Label(frame4, text="Meta Excel Path*:", fg="red")
meta_exel_filed = tk.Entry(frame4)
meta_exel_selectPath = tk.Button(frame4, text="...",
                                 command=lambda: select_file(meta_exel_filed, [("Excel file", "*.xlsx")]), padx=3)

excel_temlate = tk.Button(frame4, image=excel_icon, command=dowload_excel)
js_path.grid(row=0, column=3, pady=3, padx=3, sticky="e")
js_path_filed.grid(row=0, column=4, pady=3, padx=8)
js_selectPath.grid(row=0, column=5, padx=8)

audio_path.grid(row=1, column=3, pady=3, padx=3, sticky="e")
audio_path_filed.grid(row=1, column=4, pady=3, padx=8)
audio_selectPath.grid(row=1, column=5, padx=8, columnspan=2, sticky="w")
audioScript_path.grid(row=2, column=3, pady=3, padx=3, sticky="e")
audioScript_filed.grid(row=2, column=4, pady=3, padx=8)
audioScript_selectpath.grid(row=2, column=5, padx=8, columnspan=2, sticky="w")

meta_exel.grid(row=3, column=3, pady=3, padx=3, sticky="e")
meta_exel_filed.grid(row=3, column=4, pady=3, padx=8)
meta_exel_selectPath.grid(row=3, column=5, padx=8)
excel_temlate.grid(row=3, column=6, padx=8)


def newProject():
    input_lang, input_epub_version, input_epub_structure = lang_info.get(), ePub_version_info.get(), ePub_type_info.get()
    input_opfName, input_NCXName, input_HTMLFileName, input_EntityType, input_FileSplit, input_footnoteMovement, input_Navigation = OpfName_info.get(), ncx_file_info.get(), HTML_file_info.get(), entity_type_info.get(), fileSplit_info.get(), footnoteMovement_info.get(), Navigation_info.get()
    input_RootFolderName, input_HTMLFolderName, input_CSSFolderName = root_folder_info.get(), HTML_folder_info.get(), CSS_folder_info.get()

    def createProject():
        global new_projectname
        new_projectname = name_field.get()
        if new_projectname == "":
            subwarning_label["text"] = "Please enter project name!"
        else:
            if os.path.exists(name_mapping_field.get()):
                if os.path.exists(os.path.join(mapping_content_path, os.path.basename(name_mapping_field.get()))):
                    messagebox.showerror("Error", "This mapping document already exit!")
                    new_gui.focus_set()
                elif name_mapping_field.get().endswith(".xml"):
                    shutil.copy2(name_mapping_field.get(), mapping_content_path)
                    new_gui.focus_set()
                    New_PublisherName_Element = gui_data_root.find("PublisherName")
                    New_PublisherName_list = New_PublisherName_Element.text + f",{new_projectname}"
                    New_PublisherName_Element.text = New_PublisherName_list
                    new_element = Et.Element("publisher")
                    new_prjectname = Et.SubElement(new_element, "name")
                    new_prjectname.text = name_field.get()
                    new_language = Et.SubElement(new_element, "Language")
                    new_language.text = input_lang
                    new_epubVersion = Et.SubElement(new_element, "epubVersion")
                    new_epubVersion.text = input_epub_version
                    new_ePubStructure = Et.SubElement(new_element, "ePubStructure")
                    new_ePubStructure.text = input_epub_structure
                    new_OpfName = Et.SubElement(new_element, "OpfName")
                    new_OpfName.text = input_opfName
                    new_NCXName = Et.SubElement(new_element, "NCXName")
                    new_NCXName.text = input_NCXName
                    new_HTMLFileName = Et.SubElement(new_element, "HTMLFileName")
                    new_HTMLFileName.text = input_HTMLFileName
                    new_EntityType = Et.SubElement(new_element, "EntityType")
                    new_EntityType.text = input_EntityType
                    new_fileSplit = Et.SubElement(new_element, "fileSplit")
                    new_fileSplit.text = input_FileSplit
                    new_footnoteMovement = Et.SubElement(new_element, "footnoteMovement")
                    new_footnoteMovement.text = input_footnoteMovement
                    new_Navigation = Et.SubElement(new_element, "Navigation")
                    new_Navigation.text = input_Navigation
                    new_RootFolderName = Et.SubElement(new_element, "RootFolderName")
                    new_RootFolderName.text = input_RootFolderName
                    new_HTMLFolderName = Et.SubElement(new_element, "HTMLFolderName")
                    new_HTMLFolderName.text = input_HTMLFolderName
                    new_CSSFolderName = Et.SubElement(new_element, "CSSFolderName")
                    new_CSSFolderName.text = input_CSSFolderName
                    new_mappingDoc = Et.SubElement(new_element, "mappingDoc")
                    new_mappingDoc.text = os.path.basename(name_mapping_field.get())
                    project_confi_root.append(new_element)
                    os.chdir(path)
                    project_confi_file.write("project_confi.xml")
                    gui_data_file.write("gui_confi.xml")
                    messagebox.showinfo("Info", "New project created Sucessfully!")
                    new_gui.destroy()
                else:
                    messagebox.showerror(title="Error", message="Please choose valid xml file!")
                    new_gui.focus_set()
            else:
                messagebox.showerror(title="Error", message="Please choose valid mapping document!")
                new_gui.focus_set()

    new_gui = tk.Toplevel(uiWindow)
    sub_gui = GUI(new_gui, 350, 150)
    new_gui.title("Project Name")
    name_lable = tk.Label(new_gui, text="New Project Name:", pady=10)
    name_field = tk.Entry(new_gui)
    new_gui.focus_set()
    name_mapping = tk.Label(new_gui, text="Mapping Document:", pady=10)
    name_mapping_field = tk.Entry(new_gui)
    name_mapping_button = tk.Button(new_gui, text="...",
                                    command=lambda: select_file(name_mapping_field, [("xml file", "*.xml")]), padx=3)

    name_lable.grid(row=0, column=0, padx=10)
    name_field.grid(row=0, column=1, columnspan=2, padx=10, sticky="w")
    name_mapping.grid(row=1, column=0, padx=10)
    name_mapping_field.grid(row=1, column=1, padx=10, sticky="w")
    name_mapping_button.grid(row=1, column=2, sticky="w")

    submitButton = tk.Button(new_gui, text="Create", padx=10, font=("Arial Black", 10), bg="#c5161d", fg="#ffffff",
                             command=createProject)
    CancelButton = tk.Button(new_gui, text="Cancel", padx=10, font=("Arial Black", 10), bg="#c5161d", fg="#ffffff",
                             command=new_gui.destroy)
    submitButton.grid(row=2, column=0, padx=3)
    CancelButton.grid(row=2, column=1)
    subwarning_label = tk.Label(new_gui, fg="red", padx=10)
    subwarning_label.grid(row=3, column=0, columnspan=3, padx=3)


def progress_update():
    if job_no_filed.get() and meta_exel_filed.get():
        progress_bar.grid(row=1, column=0)
    thread1 = threading.Thread(target=conversion)
    thread1.start()

    def update():
        if thread1.is_alive():
            submitButton.config(state="disabled")
        else:
            submitButton.config(state="normal")
            progress_bar.grid_forget()


    update()


# Frame 5
submitButton = tk.Button(frame5, text="Process", padx=20, font=("Arial Black", 10), bg="#c5161d", fg="#ffffff",
                         command=progress_update)
copyofProjectButton = tk.Button(frame5, text="Copy/New Project", padx=20, font=("Arial Black", 10), bg="#c5161d",
                                fg="#ffffff", command=newProject)
CancelButton = tk.Button(frame5, text="Cancel", padx=20, font=("Arial Black", 10), bg="#c5161d", fg="#ffffff",
                         command=uiWindow.quit)
submitButton.grid(row=0, column=0, padx=3)
copyofProjectButton.grid(row=0, column=1, padx=3)
CancelButton.grid(row=0, column=2)

# Frame 6
warning_label = tk.Label(frame6, fg="red", font=10, padx=10)
warning_label.grid(row=0, column=0)
progress_bar = ttk.Progressbar(frame6, orient="horizontal", mode="determinate", length=300, maximum=100)
progress_bar.grid_forget()


def on_select(event):
    for child in project_list:
        for subchild in child:
            if event.widget.get() == subchild.text:
                for item in child:
                    if item.tag == "Language":
                        lang_info.set(item.text)
                        lang_filed.config(state="disabled")
                    elif item.tag == "epubVersion":
                        ePub_version_info.set(item.text)
                        ePub_version_filed.config(state="disabled")
                    elif item.tag == "ePubStructure":
                        ePub_type_info.set(item.text)
                        ePub_type_filed.config(state="disabled")
                    elif item.tag == "OpfName":
                        OpfName_info.set(item.text)
                        opf_file_filed.config(state="disabled")
                    elif item.tag == "HTMLFileName":
                        HTML_file_info.set(item.text)
                        HTML_file_filed.config(state="disabled")
                    elif item.tag == "NCXName":
                        ncx_file_info.set(item.text)
                        ncx_file_filed.config(state="disabled")
                    elif item.tag == "EntityType":
                        entity_type_info.set(item.text)
                        entity_type_filed.config(state="disabled")
                    elif item.tag == "fileSplit":
                        fileSplit_info.set(item.text)
                        fileSplit_filed.config(state="disabled")
                    elif item.tag == "RootFolderName":
                        root_folder_info.set(item.text)
                        root_folder_filed.config(state="disabled")
                    elif item.tag == "HTMLFolderName":
                        HTML_folder_info.set(item.text)
                        HTML_folder_filed.config(state="disabled")
                    elif item.tag == "CSSFolderName":
                        CSS_folder_info.set(item.text)
                        CSS_folder_filed.config(state="disabled")
                    elif item.tag == "footnoteMovement":
                        footnoteMovement_info.set(item.text)
                        footnoteMovement_filed.config(state="disabled")
                    elif item.tag == "Navigation":
                        Navigation_info.set(item.text)
                        Navigation_filed.config(state="disabled")


            elif event.widget.get() == "Common":
                lang_filed.config(state="normal")
                ePub_version_filed.config(state="normal")
                ePub_type_filed.config(state="normal")
                opf_file_filed.config(state="normal")
                HTML_file_filed.config(state="normal")
                ncx_file_filed.config(state="normal")
                entity_type_filed.config(state="normal")
                fileSplit_filed.config(state="normal")
                root_folder_filed.config(state="normal")
                HTML_folder_filed.config(state="normal")
                CSS_folder_filed.config(state="normal")
                footnoteMovement_filed.config(state="normal")
                Navigation_filed.config(state="normal")


def on_version(event):
    if event.widget.get() == "ePub 2":
        ePub_type_filed.config(state="disabled")
        ePub_type_info.set("")
    elif event.widget.get() == "ePub 3":
        ePub_type_filed.config(state="normal")
        ePub_type_info.set("Semantic")


publisher_filed.bind("<<ComboboxSelected>>", on_select)
ePub_version_filed.bind("<<ComboboxSelected>>", on_version)
uiWindow.mainloop()
