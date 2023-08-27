import customtkinter as ct
import string
import subprocess
import cssutils
# from epubcheck import EpubCheck
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
from tkinter import font
from PIL import Image
from CTkMessagebox import CTkMessagebox




# Tag mapping subfunction

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
        self.master.maxsize(self.width, self.height)

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

    open_nest_tag = f"{nest_tag}1" if nested_level == "" else f"{nest_tag}{nested_level}"
    new_tag = open_nest_tag if nest_attr_val == "" else f"{open_nest_tag}\n{new_attribute}"
    file_content = re.sub(rf"<{find_tag}", f"\n<{find_tag}", file_content, flags=re.IGNORECASE)
    file_content = re.sub(rf"([\n\n]+)", f"\n", file_content, flags=re.IGNORECASE)
    file_array = file_content.split("\n")
    for x in range(len(file_array)):
        open_tag = re.findall(rf'<{find_tag}([^<]*){find_attrib}="({fint_att})"([^<]*)>', file_array[x],
                              flags=re.IGNORECASE)
        if open_tag:
            if find_classname:
                file_array[x] = re.sub(rf'<{find_tag}([^<]*){find_attrib}="({fint_att})"([^<]*)>',
                                   rf'<{new_tag}>\n<{find_tag}\1{find_attrib}="\2"\3>', file_array[x],
                                   flags=re.IGNORECASE)
            elif prefix:
                file_array[x] = re.sub(rf'<{find_tag}([^<]*){find_attrib}="({fint_att})"([^<]*)>',
                                       rf'<{new_tag}>\n<{find_tag}\1{find_attrib}="\2"\4>', file_array[x],
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
                new_file_array[line] = re.sub(rf"(<{open_nest_tag}\b|{nest_parent})", rf"{close_tag}\n\1",
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
    completed_levels = []
    for match in matches:
        nest_tag = match[4]
        nested_level = match[8]
        open_nest_tag = f"{nest_tag}1" if nested_level == "" else f"{nest_tag}{nested_level}"
        new_open_nest_tag = True
        for completed_level in completed_levels:
            if open_nest_tag == completed_level:
                new_open_nest_tag = False
                break
        if new_open_nest_tag:
            file_content = nested_closetag(match, file_content)
            completed_levels.append(open_nest_tag)
    return file_content


def footnote(match, file_content, link_lable_info, linksOptions):
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
    if linksOptions['Footnotes/Endnotes']:
        link_lable  = BeautifulSoup(link_lable_info, 'xml')
        footnote_class = link_lable.find("footnote").text
        p_tag, p_attrib, p_value_prefix, p_value = match[0], match[1], match[2], match[3]
        p_tag = "p" if p_tag == "" else p_tag
        p_attrib = "class" if p_attrib == "" else find_attrib

        new_tag =  rf'{p_tag}([^<]*){p_attrib}="{footnote_class}"'

        new_replace_tag = rf'<{p_tag}\1{p_attrib}="{footnote_class}"\2 id="rfn_">\3<a href="#fn_" epub:type="footnotelink">\4</a>\5\6'
        file_content = re.sub(rf'<{new_tag}([^<]*)>(<[^<>]+>)*(\d+|\*+)(<[^<>]+>)*(\.)*', rf'{new_replace_tag}', file_content, flags=re.IGNORECASE)

    return file_content


def clean_up(match, file_content, input_FileSplit):
    nest_tag, nest_attrib, nest_attr_val, = match[4], match[5], match[6]
    
    file_content = re.sub(rf"<{nest_tag}\d+", rf"<{nest_tag}", file_content, flags=re.IGNORECASE)
    file_content = re.sub(rf"</{nest_tag}\d+>", rf"</{nest_tag}>", file_content, flags=re.IGNORECASE)
    file_content = re.sub(r"(\n\n+)", r"\n", file_content, flags=re.IGNORECASE)
    file_content = file_content.replace("><link", ">\n<link")
    file_content = file_content.replace("><script", ">\n<script")
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
        file_content = re.sub("(\n\n)+", "\n", file_content)
        file_content = file_content.replace(f"\n</{list_findtag}>\n{list_tag}", "")
        file_content = file_content.replace(f"</{list_findtag}>\n{list_tag}", "")

    find_att_value = match[3]
    listItem_attrib = "" if match[5] == "" else f'{match[5]}="{match[6]}"'
    listItem_attrib = listItem_attrib if "|" not in listItem_attrib else multiple_attribute(match[5], match[6])
    listItem_findtag = f'{match[4]}{x}'
    listItem_tag = f'<{listItem_findtag}>' if listItem_attrib == "" else f'<{match[4]}{x} {listItem_attrib}>'
    find_element = rf'<{find_tag}([^<"]*){find_attrib}="{find_att_value}"([^<"]*)>'
    repl_element = rf'{listItem_tag}<{find_tag}\1{find_attrib}="{find_att_value}"\2>'
    file_content = re.sub(find_element, repl_element, file_content, flags=re.IGNORECASE)

    return file_content

def list_nested_tagging(file_content, listlevel, li_tag):
    HTML_content = BeautifulSoup(file_content, 'html.parser')
    for x in range(1, listlevel + 1):
        x_find = True
        while x_find:
            x_vistited = False
            elements = HTML_content.find_all(lambda tag_name: tag_name.name.startswith(f'list{x}-'))
            if elements:
                for ol_tag in elements:
                    next_element = ol_tag.find_next_sibling(True)
                    if next_element:
                        next_number = x + 1
                        for y in range(next_number, listlevel + 1):
                            if next_element.name.startswith(f"list{y}-"):
                                x_vistited = True
                                last_li_tag = ol_tag.find_all(li_tag, recursive=False)[-1]
                                last_li_tag.append(next_element)
                        if next_element.name == ol_tag.name:
                            ol_tag_siblings = next_element.find_all(True, recursive=False)
                            for ol_tag_sibling in ol_tag_siblings:
                                ol_tag.append(ol_tag_sibling)
                            next_element.decompose()
            if x_vistited:
                x_find = True
            else:
                x_find = False
    for x in range(1, listlevel + 1):
        elements = HTML_content.find_all(lambda tag_name: tag_name.name.startswith(f'list{x}-'))
        if elements:
            for ol_tag in elements:
                next_element = ol_tag.find_next_sibling(True)
                if next_element:
                    if next_element.name == ol_tag.name:
                        ol_tag_siblings = next_element.find_all(True, recursive=False)
                        for ol_tag_sibling in ol_tag_siblings:
                            ol_tag.append(ol_tag_sibling)
                        next_element.decompose()
    file_content = str(HTML_content)
    file_content = file_content.replace("><li", ">\n<li")
    file_content = file_content.replace("\n</li", "</li")
    file_content = file_content.replace("></list", ">\n</list")
    file_content = re.sub(f"<list(\d+)*\-", f"<", file_content, flags=re.IGNORECASE)
    file_content = re.sub(f"<\/list(\d+)*\-", f"</", file_content, flags=re.IGNORECASE)
    return file_content

def listgroup_open1(file_content, maxlevel, li_tag):
    listing = True
    visited = False
    while listing:
        file_content = re.sub(r"(\n\n)+", r"\n", file_content)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<{li_tag}(\d+)\b', rf'</list\1-\2><{li_tag}\3', file_content,
                              re.IGNORECASE)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2><list\3-', file_content, re.IGNORECASE)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)><\/list(\d+)\-(\w+)>\n<list(\d+)\-', rf'</list\1-\2>\n</list\3-\4><list\5-', file_content, re.IGNORECASE)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)><\/list(\d+)\-(\w+)>\n<list(\d+)\-',
                              rf'</list\1-\2>\n</list\3-\4><list\5-', file_content, re.IGNORECASE)
        file_content = re.sub(rf'<\/list(\d+)\-(\w+)><\/list(\d+)\-(\w+)>\n<list(\d+)\-',
                              rf'</list\1-\2>\n</list\3-\4><list\5-', file_content, re.IGNORECASE)
        file_array = file_content.split("\n")
        file_len = len(file_array)
        nestClose = False
        parCheck = False
        list_Type = ""
        parentList = ""
        for x in range(maxlevel, 0, -1):
            for y in range(x - 1, 0, -1):
                seacrhes = re.findall(rf'</list{y}\-(\w+)><list{x}\-', file_content, re.IGNORECASE)
                if seacrhes:
                    visited = True

        if not visited:
            listing = False
        for x in range(maxlevel, 0, -1):
            if x - 1 > 0:
                for y in range(x - 1, 0, -1):
                    for n, line in enumerate(file_array):
                        seacrhes = re.findall(rf'</list{y}\-(\w+)><list{x}\-', line, re.IGNORECASE)
                        li_seacrhes = re.findall(rf'</list{y}\-(\w+)><{li_tag}{x}\b', line, re.IGNORECASE)
                        if seacrhes or li_seacrhes:
                            for sr in seacrhes:
                                list_Type = sr
                                file_array[n] = re.sub(rf'</list{y}\-(\w+)><list{x}\-', rf'<list{x}-', file_array[n],
                                                       flags=re.IGNORECASE)

                            for li_ser in li_seacrhes:

                                list_Type = li_ser
                                file_array[n] = re.sub(rf'</list{y}\-(\w+)><{li_tag}{x}\b', rf'<{li_tag}{x}',
                                                       file_array[n],
                                                       flags=re.IGNORECASE)
                            nestClose = True
                        if nestClose and f"</list{x}-" in file_array[n]:
                            nestClose = False
                            file_array[n] = re.sub(rf'<\/list{x}\-(\w+)>', rf'</list{x}-\1>\n</list{y}-{list_Type}>', file_array[n],
                                                   flags=re.IGNORECASE)
                            parCheck = True
                            file_array[n] = f"{file_array[n]}{file_array[n + 1]}"
                            file_array.pop(n + 1)
                            for reLine in range(n - 1, 0, -1):
                                if parCheck and f"<list{y}-{list_Type}" in file_array[reLine]:
                                    find_parent_element = re.findall(rf"(<list{y}-{list_Type}[^<]*>)", file_array[reLine],
                                                                     flags=re.IGNORECASE)
                                    for find in find_parent_element:
                                        parentList = find
                                    parCheck = False
                                    break
                        if parentList:
                            file_array[n] = file_array[n].replace(f"</list{y}-{list_Type}>{parentList}", "")
                            file_array[n] = file_array[n].replace(f"</list{y}-{list_Type}>\n{parentList}", "")
                            parentList = ""
        file_content = ""

        for line in file_array:
            file_content += f"{line}\n"
        visited = False

    list_types = re.findall(f'</list{x}-(\w+)>', file_content)
    list_typein_file = []
    for types in list_types:
        if types not in list_typein_file:
            list_typein_file.append(types)
    for x in range(1, maxlevel + 1):
        for type in list_typein_file:
            file_content = re.sub(f'</list{x}-{type}><list{x}-{type}([^<>]*)>', "", file_content)
            file_content = re.sub(f'</list{x}-{type}>\n<list{x}-{type}([^<>]*)>', "", file_content)
    file_content = re.sub(r"(\n\n)+", r"\n", file_content)



    return file_content


def listgroup_close(file_content, match, x):
    file_array = file_content.split("\n")
    n = 0
    close = 0
    find_tag = f"<{match[4]}{x}"
    file_array_length = len(file_array)
    for line in range(0, file_array_length):
        if n < file_array_length:
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

    file_content = re.sub(r"(\n\n)+", r"\n", file_content)
    file_content = file_content.replace(f"</{match[4]}{x}>", f"</{match[4]}>")
    file_content = file_content.replace(f"<{match[4]}{x}", f"<{match[4]}")

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
    parent_tag = re.search(
        rf"<listing findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" list_type=\"([^\"]*)\" list_attr=\"([^\"]*)\" list_attr_val=\"([^\"]*)\" list_level=\"{x}\"\/>",
        mapping_content, flags=re.IGNORECASE)
    for x in range(1, listlevel + 1):
        matches = re.findall(
            rf"<listing findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" list_type=\"([^\"]*)\" list_attr=\"([^\"]*)\" list_attr_val=\"([^\"]*)\" list_level=\"{x}\"\/>",
            mapping_content, flags=re.IGNORECASE)
        if matches:
            try:
                for match in matches:

                    file_content = listgroup_close(file_content, match, x)
            except:
               meesage_error = CTkMessagebox(title="Error", message="List tag not defined properly in Mapping document", options=["OK"], justify="center", width=50, height=30, icon="cancel")
               message_info = meesage_error.get()
    # file_content = listgroup_open1(file_content, listlevel, parent_tag[5])
    file_content = list_nested_tagging(file_content, listlevel, parent_tag[5])

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
            if r"\[\[seq\]\]" in attb2:
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


def text_movement(inputfiles, mapping_file, link_lable_info, linksOptions):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        matches = re.findall(
            r"<footnote findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" to_move_under=\"([^\"]*)\" move_before=\"([^\"]*)\" move_after=\"([^\"]*)\"\/>",
            mapping_file, flags=re.IGNORECASE)
        for match in matches:
            file_content = footnote(match, file_content, link_lable_info, linksOptions)

        file_handler = open(file, "w", encoding="UTF-8")
        file_handler.write(file_content)
        file_handler.close()


def tag_groupping(inputfiles, mapping_content, nesting=False):
    for file in inputfiles:
        file_handler = open(file, "r", encoding="UTF-8")
        file_content = file_handler.read()
        file_handler.close()
        if nesting:
            matches = re.findall(
                r"<group_map tagname_to_group=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" grouptag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" nested_type=\"([^\"]+)\" nested_level=\"([^\"]+)\" group_start=\"([^\"]*)\"\/>",
                mapping_content, flags=re.IGNORECASE)
        else:
            matches = re.findall(
                r"<group_map tagname_to_group=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" grouptag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" nested_type=\"\" nested_level=\"\" group_start=\"([^\"]*)\"\/>",
                mapping_content, flags=re.IGNORECASE)
        for match in matches:
            find_tag, find_attrb, find_prefix, find_classname = match[0], match[1], match[2], match[3]
            grouptag, add_attr, attr_val = match[4], match[5], match[6]
            group_start_point = ""

            if nesting:
                nested_type, nested_level = match[7], match[8]
                group_start_point = match[9]
            else:
                group_start_point = match[7]

            find_tag = "p" if find_tag == "" else find_tag
            find_attrb = "class" if find_attrb == "" else find_attrb
            new_attribute = f' {add_attr}="{attr_val}"' if "|" not in add_attr else multiple_attribute(add_attr,
                                                                                                       attr_val)
            if nesting:
                new_groputag = f"{grouptag}{nested_level}"
            else:
                new_groputag = grouptag
                nested_level = ""
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
            if group_start_point:
                if "|" in group_start_point:
                    group_start_points = group_start_point.split("|")
                    for group_start_point in group_start_points:
                        file_content = re.sub(
                            fr"<{new_groputag}>\n<{find_tag}([^<]*){find_attrb}=\"{group_start_point}\"([^<]*)>",
                            fr'<1{new_groputag}>\n<{find_tag}\1{find_attrb}="{group_start_point}"\2>', file_content, flags=re.IGNORECASE)
                else:
                    file_content = re.sub(
                        fr"<{new_groputag}>\n<{find_tag}([^<]*){find_attrb}=\"{group_start_point}\"([^<]*)>",
                        fr'<1{new_groputag}>\n<{find_tag}\1{find_attrb}="{group_start_point}"\2>', file_content,
                        flags=re.IGNORECASE)

            file_content = file_content.replace(f'\n</grouptag>\n<{new_groputag}>', "")
            file_content = file_content.replace(f'</grouptag>', f"</{grouptag}{nested_level}>")
            file_content = file_content.replace(f'<1{new_groputag}>', f"<{new_groputag}>")
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
        cssfiles = get_all_files_and_dirs(epubOptions["input_CSSFilesPath"])
        if cssfiles:
            if epubOptions['input_HTMLFolderName'] != "No Folder":
                if epubOptions['input_CSSFolderName'] != "No Folder":
                    cssfiles = get_all_files_and_dirs(f"../{epubOptions['input_CSSFolderName']}")
                else:
                    cssfiles = get_all_files_and_dirs(f"..")
            else:
                if epubOptions['input_CSSFolderName'] != "No Folder":
                    cssfiles = get_all_files_and_dirs(f"{epubOptions['input_CSSFolderName']}")
                else:
                    cssfiles = get_all_files_and_dirs(".")
            for css in cssfiles:
                if css.endswith(".css"):
                    linktag = html_template.new_tag("link")
                    linktag["rel"] = "stylesheet"
                    linktag["type"] = "text/css"
                    linktag["href"] = css.replace("\\", "/")
                    headtag.append(linktag)

    if epubOptions["input_JSFilesPath"]:
        jsfiles = get_all_files_and_dirs(epubOptions["input_JSFilesPath"])
        if jsfiles:
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
                if possile_heading.upper() in headings_in_section.text.upper():
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
    other_possiple_group_tags = ["aside", "article", "div"]
    sectiontags.extend(other_possiple_group_tags)
    for htmlfile in split_files:

        if htmlfile.endswith(".html") or htmlfile.endswith(".xhtml") or htmlfile.endswith(".htm"):

            figcount = 1
            tabcount = 1
            asidecount = 1
            with open(htmlfile, "r", encoding="UTF-8") as html:
                htmlcontent = BeautifulSoup(html, "html.parser")
            figimgs = htmlcontent.find_all("img")
            for figimg in figimgs:
                if figimg and 'src' in figimg.attrs:
                    old_image = figimg['src']
                    image_name = os.path.basename(old_image)
                    if ePub_options['input_HTMLFolderName'] != "No Folder":
                        if ePub_options['input_ImageFolderName'] != "No Folder":
                            figimg['src'] = f"../{ePub_options['input_ImageFolderName']}/{image_name}"
                        else:
                            figimg['src'] = f"../{image_name}"
                    else:
                        if ePub_options['input_ImageFolderName'] != "No Folder":
                            figimg['src'] = f"{ePub_options['input_ImageFolderName']}/{image_name}"
                        else:
                            figimg['src'] = image_name
            chapters = htmlcontent.find(f'{section_tag_in_mapping}1', {'epub:type': 'chapter'})
            appendixs = htmlcontent.find(f'{section_tag_in_mapping}1', {'epub:type': 'appendix'})
            if chapters:
                chapId += 1
            elif appendixs:
                appId += 1
            sectiontags_in_html = htmlcontent.find_all(sectiontags)

            if htmlfile.endswith(".xhtml") or htmlfile.endswith(".html") or htmlfile.endswith(".htm"):
                for sectiontag_in_html in sectiontags_in_html:
                    headertags = sectiontag_in_html.find_all(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header'] or tag.get('data-for') == 'toclink')

                    if headertags:
                        for headertag in headertags:
                            if headertag.name.startswith("h"):
                                if headertag.name == 'header':
                                    headings = headertag.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                                    for heading in headings:
                                        heading['id'] = 'sec_' + f'{headingId}'.zfill(3)
                                        headingId += 1
                                else:
                                    no_header_headings = sectiontag_in_html.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                                    for head in no_header_headings:
                                        head['id'] = 'sec_' + f'{headingId}'.zfill(3)
                                        headingId += 1
                            else:
                                headertag['id'] = 'sec_' + f'{headingId}'.zfill(3)
                                headingId += 1
            figures = htmlcontent.find_all('figure')
            tables = htmlcontent.find_all('table')
            asides = htmlcontent.find_all('aside')

            for figure in figures:
                figimg = figure.find("img")
                if chapters:
                    if figimg and 'src' in figimg.attrs:
                        figimg['id'] = f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3)
                    elif figimg and not 'src' in figimg.attrs:
                        figimg['id'] = f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3)
                        figimg['alt'] = f"Figure {chapId}-{figcount}"
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                figimg['src'] = f"../{ePub_options['input_ImageFolderName']}/fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg"
                            else:
                                figimg['src'] = f"../fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg"
                        else:
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                figimg['src'] = f"{ePub_options['input_ImageFolderName']}/fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg"
                            else:
                                figimg['src'] = f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg"
                    else:
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                imgtag = htmlcontent.new_tag("img", attrs={"src": f"../{ePub_options['input_ImageFolderName']}/fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg", "id": f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3), "alt": f"Figure {chapId}-{figcount}"})
                            else:
                                imgtag = htmlcontent.new_tag("img", attrs={
                                    "src": f"../fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg",
                                    "id": f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3), "alt": f"Figure {chapId}-{figcount}"})
                        else:
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                imgtag = htmlcontent.new_tag("img", attrs={"src": f"{ePub_options['input_ImageFolderName']}/fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg",
                                                                       "id": f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3),
                                                                       "alt": f"Figure {chapId}-{figcount}"})
                            else:
                                imgtag = htmlcontent.new_tag("img", attrs={
                                    "src": f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3) +".jpg",
                                    "id": f"fig" + f"{chapId}".zfill(3) + "_" + f"{figcount}".zfill(3),
                                    "alt": f"Figure {chapId}-{figcount}"})
                        figure.insert(0, imgtag)

                    figcount += 1
                elif appendixs:
                    if figimg and 'src' in figimg.attrs:
                        figimg['id'] = f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3)
                        figimg['alt'] = f"Figure {appId}-{figcount}"
                    elif figimg and not 'src' in figimg.attrs:
                        figimg['id'] = f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3)
                        figimg['alt'] = f"Figure {appId}-{figcount}"
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                figimg['src'] = f"../{ePub_options['input_ImageFolderName']}/fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg"
                            else:
                                figimg['src'] = f"../fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg"
                        else:
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                figimg['src'] = f"{ePub_options['input_ImageFolderName']}/fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg"
                            else:
                                figimg['src'] = f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg"
                    else:
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                imgtag = htmlcontent.new_tag("img",
                                                         attrs={"src": f"../{ePub_options['input_ImageFolderName']}/fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg",
                                                                "id": f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3),
                                                                "alt": f"Figure {appId}-{figcount}"})
                            else:
                                imgtag = htmlcontent.new_tag("img",
                                                             attrs={"src": f"../fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg",
                                                                    "id": f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3),
                                                                    "alt": f"Figure {appId}-{figcount}"})
                        else:
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                imgtag = htmlcontent.new_tag("img",
                                                         attrs={"src": f"{ePub_options['input_ImageFolderName']}/fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg",
                                                                "id": f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3),
                                                                "alt": f"Figure {appId}-{figcount}"})
                            else:
                                imgtag = htmlcontent.new_tag("img",
                                                             attrs={
                                                                 "src": f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3) + ".jpg",
                                                                 "id": f"fig_app" + f"{appId}".zfill(3) + "_" + f"{figcount}".zfill(3),
                                                                 "alt": f"Figure {appId}-{figcount}"})
                        figure.insert(0, imgtag)
                    figcount += 1
                else:
                    if figimg  and 'src' in figimg.attrs:
                        figimg['id'] = f"fig_" +f"{figcount}".zfill(3)
                        figimg['alt'] = f"Figure {figcount}"
                    elif figimg and not 'src' in figimg.attrs:
                        figimg['id'] = f"fig_" +f"{figcount}".zfill(3)
                        figimg['alt'] = f"Figure {figcount}"
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                figimg['src'] = f"../{ePub_options['input_ImageFolderName']}/fig_" +f"{figcount}".zfill(3) +".jpg"
                            else:
                                figimg['src'] = f"../fig_" +f"{figcount}".zfill(3) +".jpg"
                        else:
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                figimg['src'] = f"{ePub_options['input_ImageFolderName']}/fig_" +f"{figcount}".zfill(3) +".jpg"
                            else:
                                figimg['src'] = f"fig_" +f"{figcount}".zfill(3) +".jpg"
                    else:
                        if ePub_options['input_HTMLFolderName'] != "No Folder":
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                imgtag = htmlcontent.new_tag("img",
                                                         attrs={"src": f"../{ePub_options['input_ImageFolderName']}/fig_" +f"{figcount}".zfill(3) +".jpg",
                                                                "id": f"fig_" +f"{figcount}".zfill(3),
                                                                "alt": f"Figure {figcount}"})
                            else:
                                imgtag = htmlcontent.new_tag("img",
                                                             attrs={
                                                                 "src": f"../fig_" +f"{figcount}".zfill(3) +".jpg",
                                                                 "id": f"fig_" +f"{figcount}".zfill(3),
                                                                 "alt": f"Figure {figcount}"})
                        else:
                            if ePub_options['input_ImageFolderName'] != "No Folder":
                                imgtag = htmlcontent.new_tag("img",
                                                         attrs={
                                                             "src": f"{ePub_options['input_ImageFolderName']}/fig_" +f"{figcount}".zfill(3) +".jpg",
                                                             "id": f"fig_" +f"{figcount}".zfill(3),
                                                             "alt": f"Figure {figcount}"})
                            else:
                                imgtag = htmlcontent.new_tag("img",
                                                             attrs={
                                                                 "src": f"fig_" +f"{figcount}".zfill(3) +".jpg",
                                                                 "id": f"fig_" +f"{figcount}".zfill(3),
                                                                 "alt": f"Figure {figcount}"})
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
                    if not table.has_attr('id'):
                        table['id'] = f'tab_{chapId}_{tabcount}'
                        tabcount += 1
                elif appendixs:
                    if not table.has_attr('id'):
                        table['id'] = f'tab_app{appId}_{tabcount}'
                        tabcount += 1
                else:
                    if not table.has_attr('id'):
                        table['id'] = f'tab_{tabcount}'
                        tabcount += 1
            for aside in asides:
                if chapters:
                    aside['id'] = f'aside_{chapId}_{asidecount}'
                    asidecount += 1
                elif appendixs:
                    aside['id'] = f'aside_app{appId}_{asidecount}'
                    asidecount += 1
                else:
                    aside['id'] = f'aside_{asidecount}'
                    asidecount += 1

            with open(htmlfile, "w", encoding="UTF-8") as html:
                html.write(str(htmlcontent))


def file_split(file, epubOptions, mapping_content, split_info, heading_filename_info):
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
        if not epubOptions['input_xml']:
            section_tag_in_mapping = find_section_tag_in_mapping.group(5)
        else:
            section_tag_in_mapping = "section"
        level_check = re.findall(
            r'<nested findtag="([^"<]*)" find_attrib="([^"<]*)" find_att_value_prefix="([^"<]*)" find_att_value="([^"<]*)" add_p_tag="([^"<]*)" add_attr="([^"<]*)" attr_val="([^"<]*)" nested_type="([^"<]*)" nested_level="([^"<]*)" nest_parent="([^"<]*)"/>',
            mapping_content)
        level = 0
        if not epubOptions['input_xml']:
            if level_check:
                for count in level_check:
                    if int(count[8]) > level:
                        level = int(count[8])
        else:
            level = 15
        idGenerationforHeading(level, section_tag_in_mapping, split_files, epubOptions)

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
        height = 160
        if len(self.toc_classAndLevels) > 3:
            height = height + (len(self.toc_classAndLevels) - 3) * 50
        self.toc_gui = ct.CTkToplevel(self.uiWindow)
        self.sub_gui = self.GUI(self.toc_gui, 350, height)

        self.toc_gui.title("Toc Mappaing")
        bold = font.Font(weight='bold')
        name_lable = ct.CTkLabel(self.toc_gui, text="Class name:")
        name_lable.grid(row=0, column=0)
        self.toc_gui.focus()

        name_mapping = ct.CTkLabel(self.toc_gui, text="Toc Level:", pady=10)
        name_lable.grid(row=0, column=0, sticky="w")
        name_mapping.grid(row=0, column=1, sticky="w")
        levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "Skip"]

        for self.i, (self.cls, self.levl) in enumerate(self.toc_classAndLevels.items()):
            class_name = ct.CTkLabel(self.toc_gui, text=self.cls)
            class_name.grid(row=self.i+1, column=0, sticky="w", padx=5)
            level_value = ct.StringVar()
            level_value.set(levels[0])
            level_filed = ct.CTkComboBox(self.toc_gui, values=levels, variable=level_value)
            level_filed.grid(row=self.i+1, column=1, sticky="w", pady=5)
            self.box_values[self.cls] = level_filed.get()
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
            meesage_error = CTkMessagebox(title="Error", message="Please fill all feild", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            message_info = meesage_error.get()
            self.toc_gui.focus()

def check_level(parent, userTocSelection):
    class_name = parent['class']
    level = userTocSelection[class_name[0]]

    ncx_level = 0
    for lev in userTocSelection.values():
        if lev != 'Skip':
            if ncx_level < int(lev):
                ncx_level = int(lev)
    return level, ncx_level

def TOCitemGeneration(sections, start_level, start, endposion, htmlpath, sublevel=True):
    ol_template = BeautifulSoup(features="html.parser")
    li_tag = None
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

def selected_values(tochtml, mapping_content):
    matches = re.findall(
        rf"<listing findtag=\"([^\"]*)\" find_attrib=\"([^\"]*)\" find_att_value_prefix=\"([^\"]*)\" find_att_value=\"([^\"]*)\" add_p_tag=\"([^\"]*)\" add_attr=\"([^\"]*)\" attr_val=\"([^\"]*)\" list_type=\"([^\"]*)\" list_attr=\"([^\"]*)\" list_attr_val=\"([^\"]*)\" list_level=\"(\d+)\"\/>",
        mapping_content, flags=re.IGNORECASE)
    toc_levels = {}
    for p in tochtml.find_all("p"):
        if p["class"][0] not in toc_levels.keys():
            for match in matches:
                if p["class"][0] == match[3]:
                    toc_levels[p["class"][0]] = int(match[10])
    return toc_levels


def toclinking_with_heading(tocfileNames, htmlpath, tocpages, heading_and_filenames, inputfilename, epub_options, filename, data_for_toc_link, mapping_content):

    tocpage_length = 0
    Final_TOC = None
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
        errorlog('..', filename,
                 "Error: Table of Content is missing, Please check 'Navigation Option' or 'Input HTML file'\n")
        navcontent = ""
        submitButton.configure(state="normal")
    if tocpages:
        for tocfile, tocfilename in zip(tocfileNames, tocpages):
            with open(f'{htmlpath}{tocfile}', "r", encoding="UTF-8") as f:
                tocContent = f.read()
                tochtml = BeautifulSoup(tocContent, 'html.parser')
            userTocSelection = selected_values(tochtml, mapping_content)
            paratags = [p for p in tochtml.find_all('p') if p['class'][0] in userTocSelection.keys()]

            for_group = heading_and_filenames
            a_tags = tochtml.find_all("a")
            if epub_options['input_xml']:
                meesage_error = CTkMessagebox(title="Clelan-up", message="Do want put link TOC page?", icon="warning", option_1="Yes", option_2="No")
                xml_toc = meesage_error.get()
            if (not epub_options['input_xml'] or xml_toc == "Yes") and tocFile == tocfile:
                if len(paratags) == len(data_for_toc_link):
                    if data_for_toc_link:
                        for a_tag in a_tags:
                            a_tag.unwrap()
                        for value, para in enumerate(paratags):
                            if para["class"][0] in userTocSelection.keys():
                                atag = tochtml.new_tag("a", attrs={"href": f"{data_for_toc_link[value][0]}#{data_for_toc_link[value][1]['id']}"})
                                atext = ""
                                for text in para.contents:
                                    if hasattr(text, 'name'):
                                        atext += str(text)
                                    else:
                                        atext += text
                                atag.string = atext
                                para.clear()
                                para.append(atag)
                else:
                    meesage_error = CTkMessagebox(title="Error", message="Data attriubte count is not matching with TOC entry count", justify="center", width=50, height=30, icon="cancel")
                    message_info = meesage_error.get()
                    for a_tag in a_tags:
                        a_tag.unwrap()
                    for para in paratags:
                        match_found = False
                        full_match_found = False
                        for i, (filename, heads) in enumerate(for_group.items()):
                            if heads:
                                for j in range(0, len(heads)):
                                    if para.text.upper().replace("  ", " ").strip() == heads[j].text.upper().replace("  ", " ").strip():
                                        heads[j].string = "matched"
                                        atag = tochtml.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                                        full_match_found = True
                                        atext = ""
                                        for text in para.contents:
                                            if hasattr(text, 'name'):
                                                atext += str(text)
                                            else:
                                                atext += text
                                        atag.string = atext
                                        para.clear()
                                        para.append(atag)
                                        break

                            if full_match_found:
                                break
                        if not full_match_found:
                            for i, (filename, heads) in enumerate(for_group.items()):
                                if heads:
                                    for j in range(0, len(heads)):
                                        toc_texts = re.findall(r'\w+', para.text)
                                        head_texts = re.findall(r'\w+', heads[j].text)
                                        text_length = len(toc_texts)
                                        matched_num = 0
                                        head_start = 0
                                        head_length = len(head_texts)
                                        for text in toc_texts:
                                            for num in range(head_start, head_length-1):
                                                if head_texts[num].upper() == text.upper():
                                                    matched_num +=1
                                                    head_start = num
                                                    break

                                        if matched_num > 0:
                                            matched_percentag = (matched_num/text_length)*100
                                        else:
                                            matched_percentag = 0
                                        if len(toc_texts) <= 2 and len(toc_texts) == len(head_texts) and matched_percentag >= 50:
                                            atag = tochtml.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                                            heads[j].string = "matched"
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


                                            break
                                        elif matched_percentag >=70:
                                            atag = tochtml.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                                            match_found = True
                                            heads[j].string = "matched"
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

                                            break
                                if match_found:
                                    break
                        if not match_found and not full_match_found:
                            atag = tochtml.new_tag("a", attrs={"href": "#dummy_link"})
                            atext = ""
                            for text in para.contents:
                                if hasattr(text, 'name'):
                                    atext += str(text)
                                else:
                                    atext += text
                            atag.string = atext
                            para.clear()
                            para.append(atag)


            with open(f'{htmlpath}{tocfile}', "w", encoding="UTF-8") as f:
                content = str(tochtml)
                content = re.sub(r'&lt;([^&]*)&gt;', r"<\1>", content, flags=re.IGNORECASE)
                f.write(content)
            if tocfile == tocFile:
                Final_TOC = tochtml

    return Final_TOC


def collect_heading_for_toc_link(htmlpath, fileorder):
    data_for_toc_link = []
    for file in fileorder:
        with open(f'{htmlpath}{file}', "r", encoding="UTF-8") as f:
            file_string = f.read()
        tochtml = BeautifulSoup(file_string, 'html.parser')
        data_for_toc = tochtml.find_all(attrs={'data-for': "toclink"})
        if data_for_toc:
            for data in data_for_toc:
                temp_data = [file, data]
                data_for_toc_link.append(temp_data)



    return data_for_toc_link

def toclink(tocfileNames, tocpages, heading_and_filenames, htmlpath, inputfilename, fileorder, epub_options, navItemfile_info, section_tag_in_mapping, mapping_content, filename):

    data_for_toc_link = collect_heading_for_toc_link(htmlpath, fileorder)

    tochtml = toclinking_with_heading(tocfileNames, htmlpath, tocpages, heading_and_filenames, inputfilename, epub_options, filename, data_for_toc_link, mapping_content)
    ncx_level = 1
    hrefs=[]
    # with open(f'{htmlpath}{tocfile}', "r", encoding="UTF-8") as f:
    #     content = f.read()
    # tochtml = BeautifulSoup(content, 'html.parser')
    userTocSelection = selected_values(tochtml, mapping_content)
    for p in tochtml.find_all("p"):
        if not p.find("a"):
            if htmlpath:
                errorlog(f'../..', inputfilename, f"Error - Link is missing in TOC HTML: '{p.text}'\n")
            else:
                errorlog(f'..', inputfilename, f"Error - Link is missing in TOC HTML: '{p.text}'\n")
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

    def getting_headings(headertags):
        heading_text = ""

        for headertag in headertags:
            if headertag.name == 'header':
                headings = headertag.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                for heading in headings:
                    if not heading_text:
                        heading_text = heading.text
                    else:
                        heading_text = heading_text + " " + heading.text
            else:
                no_header_headings = headertag.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                                                                 recursive=False)
                for head in no_header_headings:
                    if not heading_text:
                        heading_text = head.text
                    else:
                        heading_text = heading_text + " " + head.text
        return heading_text

    for htmlname in fileorder:
        itemfound = False
        for href in hrefs:
            if htmlname in href:
                itemfound = True
                break
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
            elif section1['epub:type'] == 'titlepage':
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
            elif section1['epub:type'] == "chapter":
                chapcount += 1
                tocItem1 = html_template.new_tag("li")
                html_template.append(tocItem1)
                alink = html_template.new_tag("a", attrs={'href': f'{htmlpath}{htmlname}'})
                tocItem1.append(alink)
                headertags = section1.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header'],
                                               recursive=False)

                if headertags:
                    alink.string = getting_headings(headertags)
                else:
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
                headertags = section1.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header'],
                                               recursive=False)

                if headertags:
                    alink.string = getting_headings(headertags)
                else:
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
                headertags = section1.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header'],
                                               recursive=False)

                if headertags:
                    alink.string = getting_headings(headertags)
                else:
                    for possile_navItem in possile_navItems:
                        findEpub_type = possile_navItem.find('epub_type').text
                        FM_navItem = possile_navItem.find('text').text
                        if findEpub_type == section1['epub:type']:
                            alink.string = f'{FM_navItem}'
                            break

    return html_template, ncx_level

def navitemGeneration(sections, section_tag_in_mapping, htmlname, htmlpath, epub_options, level=1, start=2, sublevel = False, ncx_level = 0):
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
                subsubsection = subsection.find(f"{section_tag_in_mapping}{start+1}")
                if subsubsection:
                    sub_ol, ncx_level = navitemGeneration(subsection, section_tag_in_mapping, htmlname, htmlpath, epub_options, level, start+1,
                                          sublevel=False, ncx_level=ncx_level)
                    li_tag.append(sub_ol)


                ol_tag.append(li_tag)
    return ol_tag, ncx_level
def navfiletemp(epub_options, file_order, mapping_content, html_template, navItemfile_info, filename):
    find_section_tag_in_mapping = re.search(
        r'<nested findtag="([^"<]*)" find_attrib="([^"<]*)" find_att_value_prefix="([^"<]*)" find_att_value="([^"<]*)" add_p_tag="([^"<]*)" add_attr="([^"<]*)" attr_val="([^"<]*)" nested_type="([^"<]*)" nested_level="([^"<]*)" nest_parent="([^"<]*)"/>',
        mapping_content)
    if not epub_options['input_xml']:
        section_tag_in_mapping = find_section_tag_in_mapping.group(5)
    else:
        section_tag_in_mapping = "section"
    page_tag_in_mapping = re.search(r'<pageList IDprefix="([^"<]*)" chapterRestart="([^"<]*)" chapterPageIDPrefix="([^"<]*)" pattern="([^"<]*)" chap_no_roman="([^"<]*)" targetEpubType="([^"<]*)" frontmatterRoman="([^"<]*)" pageIdSequenc="([^"<]*)"/>', mapping_content)
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

    if not epub_options['input_xml']:
        if level_check:
            for count in level_check:
                if int(count[8]) > level:
                    level = int(count[8])
    else:
        level = 15
    tocpages = []
    tocfileNames = []
    heading_and_filenames = {}
    possible_section_tags = []
    tocFile = None
    for l in range(1, level+1):
        possible_section_tags.append(f'{section_tag_in_mapping}{l}')
    other_possiple_group_tags = ["aside", "article", "div"]
    possible_section_tags.extend(other_possiple_group_tags)
    if epub_options['input_HTMLFolderName'] != "No Folder":
        htmlpath =f"{epub_options['input_HTMLFolderName']}/"
    else:
        htmlpath=""

    def getting_headings():
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
                                    if head.name == 'h2' or head.name == 'h1':
                                        head_tag = Tag(name='h2')
                                    else:
                                        head_tag = Tag(name='new_head')
                                for i, head in enumerate(headings):
                                    for att, value in head.attrs.items():
                                        if i == 0:
                                            if att == 'id':
                                                id = value
                                        head_tag[att] = value
                                    if headtext:
                                        headtext = headtext + " " + head.text
                                    else:
                                        headtext += head.text
                                head_tag.string = headtext
                                head_tag['id'] = id
                                head_tag = [head_tag]
                            if htmlfile in heading_and_filenames:
                                heading_and_filenames[htmlfile].extend(head_tag)
                            else:
                                heading_and_filenames[htmlfile] = head_tag
                    else:
                        headings = sectiontag_in_html.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                        if headings:
                            if htmlfile in heading_and_filenames:
                                heading_and_filenames[htmlfile].extend(headings)
                            else:
                                heading_and_filenames[htmlfile] = headings

            toc = htmlcontent.find_all(f'{section_tag_in_mapping}1', {'epub:type': 'toc'})
            if toc:
                tocpages.append(toc)
                tocfileNames.append(htmlfile)
        return heading_and_filenames, tocpages, tocfileNames

    heading_and_filenames, tocpages, tocfileNames = getting_headings()

    if not tocpages:
        for htmlfile in file_order:
            with open(f"{htmlpath}{htmlfile}", "r", encoding="UTF-8") as html:
                check_htmlcontent = BeautifulSoup(html, "html.parser")
            bref = check_htmlcontent.find_all(f'{section_tag_in_mapping}1', {'epub:type': 'brief-toc'})
            if bref:
                tocpages.append(bref)
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


        try:
            tocItems, ncx_level = toclink(tocfileNames, tocpages, heading_and_filenames, htmlpath, filename, file_order, epub_options, navItemfile_info, section_tag_in_mapping, mapping_content, filename)

            tocItems = str(tocItems)
            tocItems = re.sub(f'(\n\n)+', "\n", tocItems)
            tocItems = tocItems.replace(f'</ol>\n<ol class="navlist">', "")
            tocItems = tocItems.replace(f'</ol><ol class="navlist">', "")
            tocItems = tocItems.replace(f'><li', ">\n<li")
            tocItems = tocItems.replace(f'&lt;', "<")
            tocItems = tocItems.replace(f'&gt;', ">")
            tocItems = BeautifulSoup(tocItems, "html.parser")
            for li_tag in tocItems.find_all("li"):
                next_element = li_tag.find_next_sibling(True)
                if next_element:
                    if next_element.name == "ol":
                        li_tag.append(next_element)
            maintoc_list.append(tocItems)
        except:
            meesage_error = CTkMessagebox(title="Error", message='Toc file missing, please check file has epub:type="toc"', options=["OK"],
                          justify="center",  width=50, height=30,  icon="cancel")
            message_info = meesage_error.get()
            submitButton.configure(state="normal")

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
                sections = TextAsHTML.find_all([f"{section_tag_in_mapping}1"])
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
                                sublevels, ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level=2,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level=3,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level,
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
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level=2,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level=3,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level,
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
                                sublevels, ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level=2,
                                                              start=2, sublevel=False, ncx_level=1)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level=3,
                                                              start=2, sublevel=False,ncx_level=1)
                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level,
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
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, 2,
                                                              start=2, sublevel=False)
                            elif epub_options["input_Navigation"] == "Level 3":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, 3,
                                                              start=2, sublevel=False)

                            elif epub_options["input_Navigation"] == "All Heading":
                                sublevels,ncx_level = navitemGeneration(section, section_tag_in_mapping, htmlname, htmlpath, epub_options, level,
                                                              start=2, sublevel=False)
                            if sublevels:
                                appendTrue = sublevels.find("li")
                                if appendTrue:
                                    tocItem1.append(sublevels)


    if epub_options["input_Navigation"] == "Level 1":
        ncx_level = 1
    elif epub_options["input_Navigation"] == "Level 2":
        ncx_level = 2
    new_heading_and_filenames = {}
    new_tocpages = []
    new_tocfileNames = []
    new_heading_and_filenames, new_tocpages, new_tocfileNames = getting_headings()
    for htmlfile in file_order:
        temp_dict = {}
        temp_dict.update(new_heading_and_filenames)
        with open(f"{htmlpath}{htmlfile}", "r", encoding="UTF-8") as html:
            check_htmlcontent = BeautifulSoup(html, "html.parser")
        bref = check_htmlcontent.find_all(f'{section_tag_in_mapping}1', {'epub:type': 'brief-toc'})
        tableOfContent = check_htmlcontent.find_all(f'{section_tag_in_mapping}1', {'epub:type': 'brief-toc'})
        if bref or tableOfContent:
            if htmlfile != tocFile:
                toclinking_with_heading(htmlpath, htmlfile, temp_dict, filename)
    all_tags = html_template.find_all(True)
    for tags in all_tags:
        if tags.name and not tags.get_text(strip=True):
            tags.extract()
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
        cssfiles = get_all_files_and_dirs(ePub_options["input_CSSFilesPath"])
        if cssfiles:
            if ePub_options["input_CSSFolderName"] != "No Folder":
                cssfiles = get_all_files_and_dirs(f"{ePub_options['input_CSSFolderName']}")
            else:
                cssfiles = get_all_files_and_dirs(".")
            for css in cssfiles:
                if css.endswith(".css"):
                    linktag = html_template.new_tag("link")
                    linktag["rel"] = "stylesheet"
                    linktag["type"] = "text/css"
                    linktag["href"] = css.replace("\\", "/")
                    headtag.append(linktag)
    html_template, ncx_level = navfiletemp(ePub_options, file_order, mapping_content, html_template, navItemfile_info, filename)
    pagebreakInNav = html_template.find_all(attrs={"epub:type": "pagebreak"})
    if pagebreakInNav:
        for pagebreak in pagebreakInNav:
            pagebreak.extract()
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

    if ePub_options["input_EntityType"] == "Decimal":
        entity_choice = 4
    elif ePub_options["input_EntityType"] == "Hexa-Decimal":
        entity_choice = 5
    elif ePub_options["input_EntityType"] == "SGML":
        entity_choice = 6
    elif ePub_options["input_EntityType"] == "UTF-8":
        entity_choice = 0
    error_log_path = f'../../'
    Entity_Toggle.entity_replace(f"{ePub_options['input_NCXName']}.ncx", entity_choice, entity_file, error_log_path, filename)
    Entity_Toggle.entity_replace(f"{ePub_options['input_NCXName']}.xhtml", entity_choice, entity_file, error_log_path, filename)
    if ePub_options['input_epub_version'] == 'ePub 2':
        os.remove(f"{ePub_options['input_NCXName']}.xhtml")
def opfFileCreation(ePub_options, metadetails, filename, file_order, entity_file, navItemfile_info):
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
        if ePub_options['input_epub_structure'] == "Accessible":
            author_details = metadetails[0]['Author'].replace(", ", ",")
            authors = author_details.split(",")
            for i, author in enumerate(authors):
                creator = opf.new_tag('dc:creator')
                creator.string = author
                creator['id'] = f"creater{i}"
                metadata.append(creator)
                creator_meta = opf.new_tag('meta', attrs={"refines": f"#creater{i}", "property": "role"})
                creator_meta.string = "aut"
                metadata.append(creator_meta)
        else:
            creator = opf.new_tag('dc:creator')
            creator.string = metadetails[0]['Author']
            metadata.append(creator)

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
            if properties and ePub_options['input_epub_version'] == "ePub 3":
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
        elif manifest_item == f'{ePub_options["input_ImageFolderName"]}\{os.path.basename(ePub_options["input_CoverImagePath"])}' or manifest_item == f'{os.path.basename(ePub_options["input_CoverImagePath"])}':
            item1 = opf.new_tag('item')
            item1['id'] = 'cover-image'
            if ePub_options["input_ImageFolderName"] != "No Folder":
                item1['href'] = manifest_item.replace("\\", "/")
            else:
                item1['href'] = manifest_item
            image_name, img_ext = os.path.splitext(os.path.basename(ePub_options['input_CoverImagePath']))
            if img_ext.upper() == ".gif".upper():
                item1['media-type'] = 'image/gif'
            elif img_ext.upper() == ".jpg".upper() or img_ext.upper() == ".jpeg".upper():
                item1['media-type'] = 'image/jpeg'
            elif img_ext.upper() == ".png".upper():
                item1['media-type'] = 'image/png'
            elif img_ext.upper() == ".svg".upper():
                item1['media-type'] = 'image/svg+xml'
            if ePub_options["input_epub_version"] == 'ePub 3':
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
    if ePub_options["input_epub_version"] == 'ePub 2':
        guide_text_info = Et.fromstring(navItemfile_info)

        input_lang = ePub_options['input_lang']
        text_language, lang_code = input_lang.split("-")
        text_language = text_language.lower()
        possile_navItems = guide_text_info.findall(f".//{text_language}/set")

        guide = opf.new_tag('guide')
        package.append(guide)
        for guidefile in file_order:
            if ePub_options['input_HTMLFolderName'] != "No Folder":
                with open(f"{ePub_options['input_HTMLFolderName']}/{guidefile}", 'r', encoding='UTF-8') as file:
                    file_content = file.read()

            else:
                with open(guidefile, 'r', encoding='UTF-8') as file:
                    file_content = file.read()
            if 'epub:type="cover"' in file_content:
                itemref1 = opf.new_tag('reference')
                itemref1['type'] = 'cover'
                for possile_navItem in possile_navItems:
                    possile_heading = possile_navItem.find("text").text
                    possile_epubType = possile_navItem.find("epub_type").text
                    if possile_epubType == 'cover':
                        itemref1['title'] = possile_heading
                        break
                if ePub_options['input_HTMLFolderName'] != "No Folder":
                    itemref1['href'] = f"{ePub_options['input_HTMLFolderName']}/{guidefile}"
                else:
                    itemref1['href'] = f"{guidefile}"
                guide.append(itemref1)
            elif 'epub:type="titlepage"' in file_content:
                itemref1 = opf.new_tag('reference')
                itemref1['type'] = 'text'
                for possile_navItem in possile_navItems:
                    possile_heading = possile_navItem.find("text").text

                    possile_epubType = possile_navItem.find("epub_type").text
                    if possile_epubType == 'titlepage':
                        itemref1['title'] = possile_heading
                        break
                if ePub_options['input_HTMLFolderName'] != "No Folder":
                    itemref1['href'] = f"{ePub_options['input_HTMLFolderName']}/{guidefile}"
                else:
                    itemref1['href'] = f"{guidefile}"
                guide.append(itemref1)
            elif 'epub:type="toc"' in file_content:
                itemref1 = opf.new_tag('reference')
                itemref1['type'] = 'toc'
                for possile_navItem in possile_navItems:
                    possile_heading = possile_navItem.find("text").text

                    possile_epubType = possile_navItem.find("epub_type").text
                    if possile_epubType == 'toc':
                        itemref1['title'] = possile_heading
                        break
                if ePub_options['input_HTMLFolderName'] != "No Folder":
                    itemref1['href'] = f"{ePub_options['input_HTMLFolderName']}/{guidefile}"
                else:
                    itemref1['href'] = f"{guidefile}"
                guide.append(itemref1)
            elif 'epub:type="introduction"' in file_content or 'epub:type="part"' in file_content or 'epub:type="chapter"' in file_content:
                itemref1 = opf.new_tag('reference')
                for possile_navItem in possile_navItems:
                    possile_epubType = possile_navItem.find("epub_type").text
                    if 'epub:type="introduction"' in file_content and 'epub:type="introduction"' == f'epub:type="{possile_epubType}"':
                        itemref1['type'] = possile_epubType
                        break
                    elif 'epub:type="part"' in file_content and 'epub:type="part"' == f'epub:type="{possile_epubType}"':
                        itemref1['type'] = possile_epubType
                        break
                    elif 'epub:type="chapter"' in file_content and 'epub:type="chapter"' == f'epub:type="{possile_epubType}"':
                        itemref1['type'] = possile_epubType
                        break
                itemref1['title'] = 'Start Reading'
                if ePub_options['input_HTMLFolderName'] != "No Folder":
                    itemref1['href'] = f"{ePub_options['input_HTMLFolderName']}/{guidefile}"
                else:
                    itemref1['href'] = f"{guidefile}"
                guide.append(itemref1)
                break
    # Write the BeautifulSoup object to a file with the .opf extension
    with open(f'{ePub_options["input_opfName"]}.opf', 'w', encoding='utf-8') as file:
        file.write(str(opf).replace("><", ">\n<"))
    if ePub_options["input_EntityType"] == "Decimal":
        entity_choice = 4
    elif ePub_options["input_EntityType"] == "Hexa-Decimal":
        entity_choice = 5
    elif ePub_options["input_EntityType"] == "SGML":
        entity_choice = 6
    elif ePub_options["input_EntityType"] == "UTF-8":
        entity_choice = 0
    error_log_path = f'../../'

    Entity_Toggle.entity_replace(f"{ePub_options['input_opfName']}.opf", entity_choice, entity_file, error_log_path, filename)
    return file_order


def pageIDgenration(file, mapping_content, ePub_options, filename, split_info):
    pageIDpatterns = re.findall(
        r'<pageList IDprefix="([^"<]*)" chapterRestart="([^"<]*)" chapterPageIDPrefix="([^"<]*)" pattern="([^"<]*)" chap_no_roman="([^"<]*)" targetEpubType="([^"<]*)" frontmatterRoman="([^"<]*)" pageIdSequenc="([^"<]*)"/>',
        mapping_content)
    pageformat_check = re.search(
        r'<pageList IDprefix="([^"<]*)" chapterRestart="([^"<]*)" chapterPageIDPrefix="([^"<]*)" pattern="([^"<]*)" chap_no_roman="([^"<]*)" targetEpubType="([^"<]*)" frontmatterRoman="([^"<]*)" pageIdSequenc="([^"<]*)"/>',
        mapping_content)
    try:
        pageformat = pageformat_check.group(2)
    except:
        errorlog('..', filename, "Error: pagelist is missing in config xml file\n")

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

    pagesquence = pageformat_check.group(8)
    pagenumber = 0
    if pagesquence.upper() == 'YES' or pagesquence.upper() == 'Y' or pagesquence.upper() == 'TRUE':
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
                                                 "Error: incorrect systax in pagelist in config xml file\n")
                                    pagevalue = newpattern
                                    pageid['id'] = f'{prefix}{pagevalue}{pagenumber}'
                                    chapno = temp
                                else:
                                    try:
                                        newpattern = pattern.format(chapprefix=chapprefix, prefix=prefix,
                                                                    chapno=chapno)
                                    except:
                                        errorlog('..', filename,
                                                 "Error: incorrect systax in pagelist in config xml file\n")
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
                                                 "Error: incorrect systax in pagelist in config xml file\n")
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
                                                 "Error: incorrect systax in pagelist in config xml file\n")
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
                                             "Error: incorrect systax in pagelist in config xml file\n")

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
                                             "Error: incorrect systax in pagelist in config xml file\n")

                                pagevalue = f'{newpattern}{pagenumber}'
                                pageid['id'] = f'{prefix}{pagevalue}'
                    with open(file, "w", encoding="UTF-8") as f:
                        f.write(str(htmlObject))

def css_validation(ePub_options, cssfiles):
    with open("CSS_Validation_Report.log", "x", encoding="UTF-8") as css_log:
        pass

def add_to_zip(zip_filename, items_to_add):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for item in items_to_add:
            if os.path.isfile(item):
                # If the item is a file, add it to the ZIP file
                zipf.write(item, os.path.basename(item))
            elif os.path.isdir(item):
                # If the item is a folder, add its contents to the ZIP file
                for root, _, files in os.walk(item):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, item)
                        zipf.write(file_path, os.path.join(os.path.basename(item), arcname))

def epubFileformation(metadetails, filename, ePub_options, mapping_content_path):
    if ePub_options['input_HTMLFolderName'] == "No Folder":
        os.chdir('../..')
    else:
        os.chdir('../../..')
    # shutil.make_archive(filename, "zip", os.getcwd(), "mimetype")
    # shutil.move(os.path.join(os.getcwd(), "META-INF"), f'{filename}.zip')
    # os.chdir('..')

    # List of files and folders to add to the ZIP file
    items_to_add = [f'{filename}/mimetype', f'{filename}/META-INF', f'{filename}/{ePub_options["input_RootFolderName"]}']

    # Name of the ZIP file
    zip_filename = f'{filename}.zip'

    # Call the function to add items to the ZIP file
    add_to_zip(zip_filename, items_to_add)

    os.rename(f'{filename}.zip', f"{metadetails[0]['e-ISBN']}_EPUB.epub")
    epubfile = f"{metadetails[0]['e-ISBN']}_EPUB.epub"
    jar_file = os.path.join(mapping_content_path, "Validation\epubcheck.jar")
    try:
        with open("run.bat", "x", encoding="UTF-8") as bat:
            bat.write(f'java -jar "{jar_file}" "{epubfile}" 2>{metadetails[0]["e-ISBN"]}_EPUB_epubcheck.log')

    except Exception as error:
        meesage_error = CTkMessagebox(title="Error", message=f"Error in ePub Checker: {error}", options=["OK"], justify="center", width=50, height=30, icon="cancel")
        message_info = meesage_error.get()

    try:
        subprocess.call("run.bat", shell=True)
    except Exception as error:
        meesage_error = CTkMessagebox(title="Error", message=f"Error while run ePub Checker: {error}", options=["OK"], justify="center", width=50, height=30, icon="cancel")
        message_info = meesage_error.get()
    os.remove("run.bat")

def linkfiles(chapter_details, possible_chap_lables_sigular, possible_chap_lables_plural, file, lableContent, possible_chap_lables_conjunction, suffix):
    withchapterName = True
    figur_length = len(chapter_details)
    for details in chapter_details:
        for n in range(1, figur_length):
            if details[1].rstrip(".:") == chapter_details[n][1].rstrip(".:"):
                withchapterName = False
                break
        if not withchapterName:
            break
    if not suffix:
        for details in chapter_details:
            for lable in possible_chap_lables_sigular:
                new_label = re.escape(lable)
                pattern = re.compile(fr'({new_label}( | ){details[1].rstrip(".:")}\b)')
                if withchapterName:
                    if file == details[0]:
                        lableContent = pattern.sub(fr'<a href="#{details[2]}">\1</a>', lableContent)
                elif not withchapterName and file == details[0]:
                    lableContent = pattern.sub(fr'<a href="#{details[2]}">\1</a>', lableContent)
                elif not withchapterName:
                    lableContent = pattern.sub(fr'<a href="{details[0]}#{details[2]}">\1</a>', lableContent)
            for pluralword in possible_chap_lables_plural:
                for conjunction in possible_chap_lables_conjunction:
                    new_pluralword = re.escape(pluralword)
                    new_conjunction = re.escape(conjunction)
                    for detail1 in chapter_details:
                        pattern = re.compile(
                            fr'({new_pluralword}( | ){details[1].rstrip(".:")}\b)(<\/\w+>)*( )*({new_conjunction})( )*(<\w+>|<\w+[^<]+>)*({detail1[1]}\b)')
                        if withchapterName:
                            if file == details[0]:
                                if file == detail1[0]:
                                    lableContent = pattern.sub(
                                        fr'<a href="#{details[2]}">\1</a>\3\4\5\6\7<a href="#{detail1[2]}">\8</a>',
                                        lableContent)
                                else:
                                    lableContent = pattern.sub(
                                        fr'<a href="#{details[2]}">\1</a>\4\5\6\7\8<a href="{detail1[0]}#{detail1[2]}">\8</a>',
                                        lableContent)
                            else:
                                lableContent = pattern.sub(
                                    fr'<a href="{details[0]}#{details[2]}">\1</a>\3\4\5\6\7<a href="{detail1[0]}#{detail1[2]}">\8</a>',
                                    lableContent)
                        elif not withchapterName and file == details[0] and file == detail1[0]:
                            lableContent = pattern.sub(
                                fr'<a href="#{details[2]}">\1</a>\3\4\5\6\7<a href="#{detail1[2]}">\8</a>',
                                lableContent)
    else:
        for details in chapter_details:
            for lable in possible_chap_lables_sigular:
                new_label = re.escape(lable)
                pattern = re.compile(fr'({new_label}( | ){details[1].rstrip(".:")}\b([A-Za-z]*))')
                if withchapterName:
                    if file == details[0]:
                        lableContent = pattern.sub(fr'<a href="#{details[2]}">\1</a>', lableContent)
                elif not withchapterName and file == details[0]:
                    lableContent = pattern.sub(fr'<a href="#{details[2]}">\1</a>', lableContent)
                elif not withchapterName:
                    lableContent = pattern.sub(fr'<a href="{details[0]}#{details[2]}">\1</a>', lableContent)
            for pluralword in possible_chap_lables_plural:
                for conjunction in possible_chap_lables_conjunction:
                    new_pluralword = re.escape(pluralword)
                    new_conjunction = re.escape(conjunction)
                    for detail1 in chapter_details:
                        pattern = re.compile(
                            fr'({new_pluralword}( | ){details[1].rstrip(".:")}\b([A-Za-z]*))(<\/\w+>)*( )*({new_conjunction})( )*(<\w+>|<\w+[^<]+>)*({detail1[1]}([A-Za-z]*))')
                        if withchapterName:
                            if file == details[0]:
                                if file == detail1[0]:
                                    lableContent = pattern.sub(
                                        fr'<a href="#{details[2]}">\1</a>\4\5\6\7\8<a href="#{detail1[2]}">\9</a>',
                                        lableContent)
                                else:
                                    lableContent = pattern.sub(
                                        fr'<a href="#{details[2]}">\1</a>\4\5\6\7\8<a href="{detail1[0]}#{detail1[2]}">\9</a>',
                                        lableContent)
                            else:
                                lableContent = pattern.sub(
                                    fr'<a href="{details[0]}#{details[2]}">\1</a>\4\5\6\7\8<a href="{detail1[0]}#{detail1[2]}">\9</a>',
                                    lableContent)
                        elif not withchapterName and file == details[0] and file == detail1[0]:
                            lableContent = pattern.sub(
                                fr'<a href="#{details[2]}">\1</a>\4\5\6\7\8<a href="#{detail1[2]}">\9</a>',
                                lableContent)
    return lableContent

def tablelink_process(lableContent, link_lable_info, lang, file, table_details):
    possible_tab_lables_sigular = link_lable_info.find(f"{lang}").find("Table").find("sigular").text.split("|")
    possible_tab_lables_plural = link_lable_info.find(f"{lang}").find("Table").find("plural").text.split("|")
    possible_tab_lables_conjunction = link_lable_info.find(f"{lang}").find("conjunction").text.split("|")
    lableContent = linkfiles(table_details, possible_tab_lables_sigular, possible_tab_lables_plural, file, lableContent,
              possible_tab_lables_conjunction, True)
    return lableContent

def boxlink_process(lableContent, link_lable_info, lang, file, figure_details):
    possible_fig_lables_sigular = link_lable_info.find(f"{lang}").find("Box").find("sigular").text.split("|")
    possible_fig_lables_plural = link_lable_info.find(f"{lang}").find("Box").find("plural").text.split("|")
    possible_fig_lables_conjunction = link_lable_info.find(f"{lang}").find("conjunction").text.split("|")
    lableContent = linkfiles(figure_details, possible_fig_lables_sigular, possible_fig_lables_plural, file, lableContent,
                             possible_fig_lables_conjunction, True)
    return lableContent

def chapterlink_process(lableContent, link_lable_info, lang, file, part_details, chapter_details, appendix_details):
    possible_chap_lables_sigular = link_lable_info.find(f"{lang}").find("chap").find("sigular").text.split("|")
    possible_chap_lables_plural = link_lable_info.find(f"{lang}").find("chap").find("plural").text.split("|")
    possible_part_lables_sigular = link_lable_info.find(f"{lang}").find("Part").find("sigular").text.split("|")
    possible_part_lables_plural = link_lable_info.find(f"{lang}").find("Part").find("plural").text.split("|")
    possible_app_lables_sigular = link_lable_info.find(f"{lang}").find("Appendix").find("sigular").text.split("|")
    possible_app_lables_plural = link_lable_info.find(f"{lang}").find("Appendix").find("plural").text.split("|")
    possible_chap_lables_conjunction = link_lable_info.find(f"{lang}").find("conjunction").text.split("|")
    if chapter_details:
        lableContent = linkfiles(chapter_details, possible_chap_lables_sigular, possible_chap_lables_plural, file, lableContent,
                  possible_chap_lables_conjunction, False)
    if part_details:
        lableContent = linkfiles(part_details, possible_part_lables_sigular, possible_part_lables_plural, file,
                                 lableContent, possible_chap_lables_conjunction, False)
    if appendix_details:
        lableContent = linkfiles(part_details, possible_app_lables_sigular, possible_app_lables_plural, file,
                                 lableContent, possible_chap_lables_conjunction, False)
    return lableContent

def figurelink_process(lableContent, link_lable_info, lang, file, figure_details):
    possible_fig_lables_sigular = link_lable_info.find(f"{lang}").find("Figure").find("sigular").text.split("|")
    possible_fig_lables_plural = link_lable_info.find(f"{lang}").find("Figure").find("plural").text.split("|")
    possible_fig_lables_conjunction = link_lable_info.find(f"{lang}").find("conjunction").text.split("|")
    lableContent = linkfiles(figure_details, possible_fig_lables_sigular, possible_fig_lables_plural, file, lableContent,
                             possible_fig_lables_conjunction, True)
    return lableContent



def indexlink_process(lableContent, page_details, pageIDPrefix):
    lableContent = re.sub(r'\b([0-9])([0-9])([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])([0-9])([0-9])([0-9])\b', fr'<a href="#{pageIDPrefix}\1\2\3\4">\1\2\3\4</a>\5\6\7<a href="#{pageIDPrefix}\8\9\10\11">\8\9\10\11</a>', lableContent)
    lableContent = re.sub(r'\b([0-9])([0-9])([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])([0-9])([0-9])\b', fr'<a href="#{pageIDPrefix}\1\2\3\4">\1\2\3\4</a>\5\6\7<a href="#{pageIDPrefix}\1\8\9\10">\8\9\10</a>', lableContent)
    lableContent = re.sub(r'\b([0-9])([0-9])([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])([0-9])\b',
                          fr'<a href="#{pageIDPrefix}\1\2\3\4">\1\2\3\4</a>\5\6\7<a href="#{pageIDPrefix}\1\2\8\9">\8\9</a>',
                          lableContent)
    lableContent = re.sub(r'\b([0-9])([0-9])([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])\b',
                          fr'<a href="#{pageIDPrefix}\1\2\3\4">\1\2\3\4</a>\5\6\7<a href="#{pageIDPrefix}\1\2\3\8">\8</a>',
                          lableContent)

    lableContent = re.sub(r'\b([0-9])([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])([0-9])([0-9])\b',
                          fr'<a href="#{pageIDPrefix}\1\2\3">\1\2\3</a>\4\5\6<a href="#{pageIDPrefix}\7\8\9">\7\8\9</a>',
                          lableContent)
    lableContent = re.sub(r'\b([0-9])([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])([0-9])\b',
                          fr'<a href="#{pageIDPrefix}\1\2\3">\1\2\3</a>\4\5\6<a href="#{pageIDPrefix}\1\7\8">\7\8</a>',
                          lableContent)
    lableContent = re.sub(r'\b([0-9])([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])\b',
                          fr'<a href="#{pageIDPrefix}\1\2\3">\1\2\3</a>\4\5\6<a href="#{pageIDPrefix}\1\2\7">\7</a>',
                          lableContent)
    lableContent = re.sub(r'\b([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])([0-9])\b',
                          fr'<a href="#{pageIDPrefix}\1\2">\1\2</a>\3\4\5<a href="#{pageIDPrefix}\6\7">\6\7</a>',
                          lableContent)
    lableContent = re.sub(r'\b([0-9])([0-9])(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9])\b',
                          fr'<a href="#{pageIDPrefix}\1\2">\1\2</a>\3\4\5<a href="#{pageIDPrefix}\1\6">\6</a>',
                          lableContent)
    lableContent = re.sub(r'\b([0-9]+)(</[^<]>)*(–|—|−|-)(<[^<]>)*([0-9]+)\b',
                          fr'<a href="#{pageIDPrefix}\1">\1</a>\2\3\4<a href="#{pageIDPrefix}\5">\5</a>',
                          lableContent)
    lableContent = re.sub(r' (\d+)\b', fr' <a href="#{pageIDPrefix}\1">\1</a>', lableContent)

    lableContent = BeautifulSoup(lableContent, 'html.parser')
    page_links = [link for link in lableContent.find_all('a', href=True) if link['href'].startswith(f'#{pageIDPrefix}')]
    for page_link in page_links:
        pagelinkFound = False
        for page_enty in page_details:
            if page_link['href'] == f'#{page_enty[1]}':
                page_link['href'] =  f'{page_enty[0]}#{page_enty[1]}'
                pagelinkFound = True
                break
        if not pagelinkFound:
            page_link.unwrap()
    for page_enty in page_details:
        if not page_enty[2].isdigit():
            for romanpage in lableContent.find_all(text=re.compile(fr'(\b{page_enty[2]}\b)')):
                text = re.sub(fr'(\b{page_enty[2]}\b)', fr'<a href="{page_enty[0]}#{page_enty[1]}">\1</a>', romanpage)
                text = BeautifulSoup(text, 'html.parser')
                romanpage.string.replace_with(text)
    return str(lableContent)

def chapterTOC_process(label_content, for_group, part=True):
    label_content = str(label_content)
    label_content = BeautifulSoup(label_content, 'html.parser')
    link_contents = label_content.find_all("nav")
    for link_content in link_contents:
        paratags = link_content.find_all("p")
        # a_tags = link_content.find_all("a")
        # for a_tag in a_tags:
        #     a_tag.unwrap()
        for para in paratags:
            match_found = False
            full_match_found = False
            for i, (filename, heads) in enumerate(for_group.items()):
                if heads:
                    for j in range(0, len(heads)):
                        if para.text.upper().replace("  ", " ").strip() == heads[j].text.upper().replace("  ", " ").strip():
                            heads[j].string = "matched"
                            if part:
                                atag = label_content.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                            else:
                                atag = label_content.new_tag("a", attrs={"href": f"#{heads[j]['id']}"})
                            full_match_found = True
                            atext = ""
                            for text in para.contents:
                                if hasattr(text, 'name'):
                                    atext += str(text)
                                else:
                                    atext += text
                            atext = BeautifulSoup(atext, 'html.parser')
                            atag.append(atext)
                            para.clear()
                            para.append(atag)
                            break

                if full_match_found:
                    break
            if not full_match_found:
                for i, (filename, heads) in enumerate(for_group.items()):
                    if heads:
                        for j in range(0, len(heads)):
                            toc_texts = re.findall(r'\w+', para.text)
                            head_texts = re.findall(r'\w+', heads[j].text)
                            text_length = len(toc_texts)
                            matched_num = 0
                            head_start = 0
                            head_length = len(head_texts)
                            for text in toc_texts:
                                for num in range(head_start, head_length-1):
                                    if head_texts[num].upper() == text.upper():
                                        matched_num +=1
                                        head_start = num
                                        break

                            if matched_num > 0:
                                matched_percentag = (matched_num/text_length)*100
                            else:
                                matched_percentag = 0
                            if len(toc_texts) <= 2 and len(toc_texts) == len(head_texts) and matched_percentag >= 50:
                                if part:
                                    atag = label_content.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                                else:
                                    atag = label_content.new_tag("a", attrs={"href": f"#{heads[j]['id']}"})
                                heads[j].string = "matched"
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
                                atext = BeautifulSoup(atext, 'html.parser')
                                atag.append(atext)
                                para.clear()
                                para.append(atag)
                                break
                            elif matched_percentag >=70:
                                if part:
                                    atag = label_content.new_tag("a", attrs={"href": f"{filename}#{heads[j]['id']}"})
                                else:
                                    atag = label_content.new_tag("a", attrs={"href": f"#{heads[j]['id']}"})
                                match_found = True
                                heads[j].string = "matched"
                                unwanter_atag = para.find("a")
                                if unwanter_atag:
                                    unwanter_atag.unwrap()
                                atext = ""
                                for text in para.contents:
                                    if hasattr(text, 'name'):
                                        atext += str(text)
                                    else:
                                        atext += text
                                atext = BeautifulSoup(atext, 'html.parser')
                                atag.append(atext)
                                para.clear()
                                para.append(atag)
                                break
                    if match_found:
                        break
    return str(label_content)

def footnote_id_gen(lableContent):
    lableContent = BeautifulSoup(lableContent, 'html.parser')
    foontnote_paras = lableContent.find_all(attrs={"id": "rfn_"})
    footnote_details = []
    n = 1
    for foontnote_para in foontnote_paras:
        foontnote_para["id"] = "rfn_" + f"{n}".zfill(3)
        n +=1
        footcitation = foontnote_para.find("a", attrs={"epub:type": "footnotelink"})
        if footcitation:
            temp = [foontnote_para["id"], footcitation.text]
            footnote_details.append(temp)

    return str(lableContent), footnote_details


def footnote_linkprocess(lableContent, footnote_details, endnote_details, file, notefile):
    lableContent = BeautifulSoup(lableContent, "html.parser")
    n = 1
    if footnote_details:
        for superscript in lableContent.find_all("sup"):
            textsInSup = superscript.find_all(text={re.compile(r'(\d+|\*+)')})
            for text in textsInSup:
                for footnote_detail in footnote_details:
                    if text.text == footnote_detail[1]:
                        id = f'fn_' + f'{n}'.zfill(3)
                        pattern = re.escape(text)
                        new_text = re.sub(pattern,
                                          fr'<a epub:type="noteref" id="{id}" href="#{footnote_detail[0]}">{text}</a>',
                                          text)
                        n += 1
                        reverse_link_para = lableContent.find("p", attrs={'id': footnote_detail[0]})
                        reverse_link = reverse_link_para.find("a", attrs={'epub:type': 'footnotelink'})
                        reverse_link['href'] = f'#{id}'
                        new_text = BeautifulSoup(new_text, 'html.parser')
                        text.string.replace_with(new_text)
                        break
    if endnote_details and not notefile:
        n = 1
        for superscript in lableContent.find_all("sup"):
            textsInSup = superscript.find_all(text={re.compile(r'(\d+|\*+)')})
            for text in textsInSup:
                for endnote_detail in endnote_details:
                    if text.text == endnote_detail[2] and endnote_detail[3] != "done":
                        id = f'en_' + f'{n}'.zfill(3)
                        pattern = re.escape(text)
                        new_text = re.sub(pattern,
                                          fr'<a epub:type="noteref" id="{id}" href="{endnote_detail[0]}#{endnote_detail[1]}">{text}</a>',
                                          text)
                        n += 1

                        new_text = BeautifulSoup(new_text, 'html.parser')
                        text.string.replace_with(new_text)
                        endnote_detail[3] = "done"
                        endnote_detail[4] = id
                        endnote_detail[5] = file
                        break
    for notlined in lableContent.find_all("a", attrs={'href': '#fn_'}):
        notlined.unwrap()
    for notlined in lableContent.find_all("a", attrs={'id': 'ft_1'}):
        notlined.unwrap()
    lableContent = str(lableContent)
    lableContent = lableContent.replace(' epub:type="footnotelink"', "")
    return str(lableContent), endnote_details

def lableCreation(lableContent, link_lable_info, ePub_options, lang, file):
    lableHTML = BeautifulSoup(lableContent, "html.parser")
    possible_fig_lables_sigular = link_lable_info.find(f"{lang}").find("Figure").find("sigular").text.split("|")
    possible_fig_lables_plural = link_lable_info.find(f"{lang}").find("Figure").find("plural").text.split("|")

    possible_tab_lables_sigular = link_lable_info.find(f"{lang}").find("Table").find("sigular").text.split("|")
    possible_tab_lables_plural = link_lable_info.find(f"{lang}").find("Table").find("plural").text.split("|")

    possible_box_lables_sigular = link_lable_info.find(f"{lang}").find("Box").find("sigular").text.split("|")
    possible_box_lables_plural = link_lable_info.find(f"{lang}").find("Box").find("plural").text.split("|")

    figure_tags = lableHTML.find_all("figure")
    table_tags = lableHTML.find_all("table")
    box_tags = lableHTML.find_all("aside")
    figure_info = []
    table_info = []
    box_info = []
    if figure_tags:
        for figure_tag in figure_tags:
            for possible_lable in possible_fig_lables_sigular:
                fig_caption = figure_tag.find('figcaption')
                if fig_caption:
                    figures_label = figure_tag.find('figcaption').find('p')
                    if figures_label:
                        if possible_lable in figures_label.text:
                            tag_string = ""
                            lable = re.escape(possible_lable)
                            pattern = re.compile(fr'((<\w>|<\w([^<])*>)*{lable}( | |-)+([^< ]+)(<\/\w+>)*)')
                            for i, text in enumerate(figures_label.contents):
                                text = str(text)
                                text = pattern.sub(r'<span epub:type="label">\1</span>', text)
                                match = pattern.search(text)
                                if match:
                                    img_tag = figure_tag.find("img")
                                    ordinal = match.group(5)
                                    details = [file, ordinal, img_tag['id']]
                                    figure_info.append(details)
                                tag_string += text
                            tag_string = BeautifulSoup(tag_string, "html.parser")
                            figures_label.clear()
                            figures_label.insert(0, tag_string)
    if table_tags:
        for table_tag in table_tags:
            for possible_lable in possible_tab_lables_sigular:
                tab_caption = table_tag.find('caption')
                if tab_caption:
                    table_label = tab_caption.find('p')
                    if table_label:
                        if possible_lable in table_label.text:
                            tag_string = ""
                            lable = re.escape(possible_lable)
                            pattern = re.compile(fr'((<\w>|<\w([^<])*>)*{lable}( | |-)+([^< ]+)(<\/\w+>)*)')
                            for i, text in enumerate(table_label.contents):
                                text = str(text)
                                text = pattern.sub(r'<span epub:type="label">\1</span>', text)
                                match = pattern.search(text)
                                if match:
                                    ordinal = match.group(5)
                                    details = [file, ordinal, table_tag['id']]
                                    table_info.append(details)
                                tag_string += text
                            tag_string = BeautifulSoup(tag_string, "html.parser")
                            table_label.clear()
                            table_label.insert(0, tag_string)
    if box_tags:
        for box_tag in box_tags:
            for possible_lable in possible_box_lables_sigular:
                box_head = box_tag.find(['h1', "h2", "h3", "h4", "h5", "h6"])
                if box_head:
                    if possible_lable in box_head.text:
                        tag_string = ""
                        lable = re.escape(possible_lable)
                        pattern = re.compile(fr'((<\w>|<\w([^<])*>)*{lable}( | |-)+([^< ]+)(<\/\w+>)*)')
                        for i, text in enumerate(box_head.contents):
                            text = str(text)
                            text = pattern.sub(r'<span epub:type="label">\1</span>', text)
                            match = pattern.search(text)
                            if match:
                                ordinal = match.group(5)
                                details = [file, ordinal, box_tag['id']]
                                box_info.append(details)
                            tag_string += text
                        tag_string = BeautifulSoup(tag_string, "html.parser")
                        box_head.clear()
                        box_head.insert(0, tag_string)
    return lableHTML, figure_info, table_info, box_info


def activelink404_check(lableContent, ePub_options, file, file_order):
    vaildlinks = []
    invalidlinks = []
    vaildlinks_404 = []
    badlinks = []
    badlinks_serverError = []
    lablecontent = BeautifulSoup(lableContent, 'html.parser')
    links = lablecontent.find_all('a')

    for link in links:
        if link.has_attr('href'):
            url = link['href']
            try:
                if url not in file_order and not url.startswith('#'):
                    status = requests.get(url)
                    if status.status_code == 200:
                        vaildlinks.append(url)
                    else:
                        if status.status_code == 404:
                            vaildlinks_404.append(url)
                        elif status.status_code == 400:
                            badlinks.append(url)
                        elif status.status_code == 500:
                            badlinks_serverError.append(url)
                        else:
                            invalidlinks.append(url)
            except:
                invalidlinks.append(url)

    if ePub_options['input_HTMLFolderName'] != 'No Folder':
        filepath = '../../../'
    else:
        filepath = '../../'
    try:
        error_log = open(f"{filepath}URL_Status.log", "x", encoding="UTF-8")
        error_log.close()
    except:
        pass
    with open(f"{filepath}URL_Status.log", "a", encoding="UTF-8") as error_log:
        if vaildlinks or invalidlinks or vaildlinks_404 or badlinks or badlinks_serverError:
            error_log.write(f"\n{file}:")
        if vaildlinks:
            error_log.write(f"\nValid Links:\n------------\n")
            for vaildlink in vaildlinks:
                error_log.write(f'{vaildlink}\n')
        if invalidlinks:
            error_log.write(f"\nInvalid Links:\n--------------\n")
            for invalidlink in invalidlinks:
                error_log.write(f"{invalidlink}\n")
        if vaildlinks_404:
            error_log.write(f"\nLinks with 404 compliance:\n----------------------------\n")
            for vaildlink_404 in vaildlinks_404:
                error_log.write(f"{vaildlink_404}\n")
        if badlinks:
            error_log.write(f"\nInvalid syntax in URL:\n----------------------\n")
            for badlink in badlinks:
                error_log.write(f"{badlink}\n")
        if badlinks_serverError:
            error_log.write(f"\nInternal Server Error in URL:\n----------------------------\n")
            for badlink_serverError in badlinks_serverError:
                error_log.write(f"{badlink_serverError}\n")



def linkProcess(linksOptions, ePub_options, file_order, link_lable_file_info, entity_file, mapping_content):
    web_cleanup = None
    def getting_headings(file_order):
        heading_and_filenames = {}
        for htmlfile in file_order:
            with open(f"{htmlfile}", "r", encoding="UTF-8") as html:
                htmlcontent = BeautifulSoup(html, "html.parser")
            sectiontags_in_html = htmlcontent.find_all("section")
            if htmlfile.endswith(".xhtml") or htmlfile.endswith(".html") or htmlfile.endswith(".htm"):
                for sectiontag_in_html in sectiontags_in_html:
                    headertags = sectiontag_in_html.find_all('header', recursive=False)
                    if headertags:
                        for headertag in headertags:
                            headings = headertag.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                                                          recursive=False)
                            headtext = ""
                            if len(headings) <= 1:
                                head_tag = headings
                            else:
                                for head in headings:
                                    if head.name == 'h2' or head.name == 'h1':
                                        head_tag = Tag(name='h2')
                                    else:
                                        head_tag = Tag(name='new_head')
                                for i, head in enumerate(headings):
                                    for att, value in head.attrs.items():
                                        if i == 0:
                                            if att == 'id':
                                                id = value
                                        head_tag[att] = value
                                    if headtext:
                                        headtext = headtext + " " + head.text
                                    else:
                                        headtext += head.text
                                head_tag.string = headtext
                                head_tag['id'] = id
                                head_tag = [head_tag]
                            if htmlfile in heading_and_filenames:
                                heading_and_filenames[htmlfile].extend(head_tag)
                            else:
                                heading_and_filenames[htmlfile] = head_tag
                    else:
                        headings = sectiontag_in_html.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                                                               recursive=False)
                        if headings:
                            if htmlfile in heading_and_filenames:
                                heading_and_filenames[htmlfile].extend(headings)
                            else:
                                heading_and_filenames[htmlfile] = headings
        return heading_and_filenames

    def web_cleanup_process(lableContent):
        lableContent = re.sub(r'((https?|www)([^<>" ]+)/) ([A-za-z0-9]+)', r"\1\4", lableContent)
        lableContent = re.sub(r'((https?|www)([^<>" ]+)\.) ([a-z0-9]+)', r"\1\4", lableContent)
        lableContent = re.sub(r'((https?|www)([^<>" ]+)_) ([A-za-z0-9]+)', r"\1\4", lableContent)
        lableContent = re.sub(r'((https?|www)([^<>" ]+)\-) ([A-za-z0-9]+)', r"\1\4", lableContent)
        lableContent = re.sub(r'((https?|www)([^<>" ]+)\?) ([A-za-z0-9]+)', r"\1\4", lableContent)
        lableContent = re.sub(r'((https?|www)([^<>" ]+)#) ([A-za-z0-9]+)', r"\1\4", lableContent)
        lableContent = re.sub(r'((https?|www)([^<>" ]+)=) ([A-Za-z0-9]+)', r"\1\4", lableContent)
        return lableContent

    def url_process(lablecontent):
        lablecontent = BeautifulSoup(lablecontent, 'html.parser')
        pattern = re.compile(
            r'(((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#%]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#%])*)')

        for match in lablecontent.find_all(string=pattern):
            urls = re.findall(pattern, match)
            text = match
            for url in urls:
                parent = match.parent
                if parent.name != "a":
                    if "http" in url[0]:
                        text = re.sub(url[0], f'<a href="{url[0]}">{url[0]}</a>', text)
                    elif "@" in url[0]:
                        text = re.sub(url[0], f'<a href="mailto:{url[0]}">{url[0]}</a>', text)
                    else:
                        text = re.sub(url[0], f'<a href="http://{url[0]}">{url[0]}</a>', text)
            text = BeautifulSoup(text, 'html.parser')
            match.replace_with(text)
        return str(lablecontent)

    link_lable_info = BeautifulSoup(link_lable_file_info, "xml")
    lang, lang_code = ePub_options['input_lang'].split("-")
    figure_details = []
    table_details = []
    box_details = []
    chapter_details = []
    part_details = []
    appendix_details = []
    page_details = []
    endnote_details = []
    id_details = []
    chap = 1
    part = 1
    app = 1
    if linksOptions['Web/eMail']:
        meesage_error = CTkMessagebox(title="Clean-up", message="Do want clean-up for Weblink?",
                                    icon="warning", options=["Yes", "No"], justify="center")
        web_cleanup = meesage_error.get()
    for file in file_order:
        with open(file, "r", encoding="UTF-8") as forlink:
            lableContent = forlink.read()
        lableHTML = BeautifulSoup(lableContent, "html.parser")
        lableContent, fig_info, tab_info, box_info = lableCreation(lableContent, link_lable_info, ePub_options, lang, file)
        figure_details.extend(fig_info)
        table_details.extend(tab_info)
        box_details.extend(box_info)
        chapter_tags = lableHTML.find_all("section", attrs={"epub:type": "chapter"})
        part_tags = lableHTML.find_all("section", attrs={"epub:type": "part"})
        appendix_tags = lableHTML.find_all("section", attrs={"epub:type": "appendix"})
        page_tags = lableHTML.find_all(attrs={"epub:type": "pagebreak"})
        ids = lableHTML.find_all(attrs={"id": True})
        endnotes_tags = lableContent.find("section", attrs={"epub:type": "endnotes"})
        if ids:
            for id in ids:
                id_info = [file, id['id']]
                id_details.append(id_info)


        if chapter_tags:
            possible_chap_lables_sigular = link_lable_info.find(f"{lang}").find("chap").find("sigular").text.split("|")
            for chapter in chapter_tags:
                head_label = chapter.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                for chap_label in possible_chap_lables_sigular:
                    if head_label['epub:type'] == "label" or head_label['epub:type'] == "title":
                        match = re.search(fr"({chap_label} )*(\w+)\b", head_label.text)
                    if match:
                        chap_details = [file, f'{match.group(2)}', head_label['id']]
                        chapter_details.append(chap_details)
                        break
        if part_tags:
            possible_part_lables_sigular = link_lable_info.find(f"{lang}").find("Part").find("sigular").text.split("|")
            for part in part_tags:
                head_label = part.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                for part_label in possible_part_lables_sigular:
                    if head_label['epub:type'] == "label" or head_label['epub:type'] == "title":
                        match = re.search(fr"({part_label} )*(\w+)\b", head_label.text)
                    if match:
                        part_info = [file, f'{match.group(2)}', head_label['id']]
                        part_details.append(part_info)
                        break

        if appendix_tags:
            possible_app_lables_sigular = link_lable_info.find(f"{lang}").find("Appendix").find("sigular").text.split("|")
            for app in appendix_tags:
                head_label = app.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                for app_label in possible_app_lables_sigular:
                    if head_label['epub:type'] == "label" or head_label['epub:type'] == "title":
                        match = re.search(fr"({app_label} )*(\w+)\b", head_label.text)
                    if match:
                        appendix_info = [file, f'{match.group(2)}', head_label['id']]
                        appendix_details.append(appendix_info)
                        break
        if page_tags and linksOptions['Index']:
            page_tag_in_mapping = re.search(
                r'<pageList IDprefix="([^"<]*)" chapterRestart="([^"<]*)" chapterPageIDPrefix="([^"<]*)" pattern="([^"<]*)" chap_no_roman="([^"<]*)" targetEpubType="([^"<]*)" frontmatterRoman="([^"<]*)" pageIdSequenc="([^"<]*)"/>',
                mapping_content)
            pageIDPrefix = page_tag_in_mapping.group(1)
            for page_tag in page_tags:
                page_id = [file, page_tag['id'], page_tag['id'].replace(pageIDPrefix, "")]
                page_details.append(page_id)
        if endnotes_tags and linksOptions['Footnotes/Endnotes']:
            endnote_class = link_lable_info.find("endnote").text
            n = 1
            for endnote_para in endnotes_tags.find_all("p", attrs={'class': endnote_class}):
                endnote_para['id'] = 'ren_' + f'{n}'.zfill(3)
                n +=1
                for content in endnote_para.find_all(text={re.compile(r'(\d+)(\.)*')}):
                    if content.strip()[0].isdigit():
                        new_text = re.subn(r'(\d+)(\.)*', rf'<a href="#en_" epub:type="endnotelink">\1</a>\2', content, 1)
                        new_text = BeautifulSoup(new_text[0], 'html.parser')
                        content.string.replace_with(new_text)
                        break
            en_chap = 1
            for endnote_section in endnotes_tags.find_all("section", recursive=False):
                en_chap_no = 'ch_' + f'{en_chap}'.zfill(3)
                endnoteparas = endnote_section.find_all("p")
                for endnotepara in endnoteparas:
                    endnotelink = endnotepara.find("a", attrs={'epub:type': 'endnotelink'})
                    if endnotelink:
                        temp = [file, endnotepara['id'], endnotelink.text.rstrip("."), en_chap_no, "id", "filename"]
                        endnote_details.append(temp)
                en_chap += 1
        with open(file, "w", encoding="UTF-8") as forlink:
            forlink.write(str(lableContent))

    for file in file_order:
        with open(file, "r", encoding="UTF-8") as forlink:
            HTMLContent = forlink.read()
        lableContent = BeautifulSoup(HTMLContent, "html.parser")
        hrefWithouthtmlname = lableContent.select('[href^="#"]')
        if ePub_options['input_xml'] or hrefWithouthtmlname:
            href_without_htmlnames = lableContent.find_all(attrs={"href": True})
            for href_without_htmlname in href_without_htmlnames:
                for id_name in id_details:
                    if id_name[1] == href_without_htmlname['href'].replace("#",""):
                        if file == id_name[0]:
                            href_without_htmlname['href'] = f'#{id_name[1]}'
                        else:
                            href_without_htmlname['href'] = f'{id_name[0]}#{id_name[1]}'
        if linksOptions['Figure']:
            lableContent = figurelink_process(str(lableContent), link_lable_info, lang, file, figure_details)
            lableContent = BeautifulSoup(lableContent, "html.parser")
            figures = lableContent.find_all('figure')
            if figures:
                for fig in figures:
                    span_tag = fig.find('span', attrs={'epub:type': 'label'})
                    if span_tag:
                        a_tag = span_tag.find('a')
                        if a_tag:
                            a_tag.unwrap()
        if linksOptions['Table']:
            lableContent = tablelink_process(str(lableContent), link_lable_info, lang, file, table_details)
            lableContent = BeautifulSoup(lableContent, "html.parser")
            tables = lableContent.find_all('table')
            if tables:
                for table in tables:
                    span_tag = table.find('span', attrs={'epub:type': 'label'})
                    if span_tag:
                        a_tag = span_tag.find('a')
                        if a_tag:
                            a_tag.unwrap()
        toc_htmlfile = lableContent.find("section", attrs={'epub:type': 'toc'})
        breif_htmlfile = lableContent.find("section", attrs={'epub:type': 'brief-toc'})
        figures_htmlfile = lableContent.find("section", attrs={'epub:type': 'loi'})
        tables_htmlfile = lableContent.find("section", attrs={'epub:type': 'lot'})
        index_file = lableContent.find("section", attrs={'epub:type': 'index'})
        lableContent, footnote_details = footnote_id_gen(str(lableContent))
        lableContent = BeautifulSoup(lableContent, "html.parser")
        if not toc_htmlfile and not breif_htmlfile:
            if linksOptions['Chapter']:
                lableContent = chapterlink_process(str(lableContent), link_lable_info, lang, file, part_details, chapter_details, appendix_details)
                lableContent = BeautifulSoup(lableContent, "html.parser")
                forchap = lableContent.find('section', attrs={"epub:type": 'chapter'})
                forpart = lableContent.find('section', attrs={"epub:type": 'part'})
                forapp = lableContent.find('section', attrs={"epub:type": 'appendix'})
                if forchap:
                    h_tag = forchap.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    a_tag = h_tag.find("a")
                    if a_tag and "#sec_" in a_tag['href']:
                        a_tag.unwrap()
                elif forpart:
                    h_tag = forpart.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    a_tag = h_tag.find("a")
                    if a_tag and "#sec_" in a_tag['href']:
                        a_tag.unwrap()
                elif forapp:
                    h_tag = forapp.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    a_tag = h_tag.find("a")
                    if a_tag and "#sec_" in a_tag['href']:
                        a_tag.unwrap()
        if linksOptions['Box']:
            lableContent = boxlink_process(str(lableContent), link_lable_info, lang, file, box_details)
            lableContent = BeautifulSoup(lableContent, "html.parser")
            asides = lableContent.find_all('aside')
            if asides:
                for aside in asides:
                    span_tag = aside.find('span', attrs={'epub:type': 'label'})
                    if span_tag:
                        a_tag = span_tag.find('a')
                        if a_tag:
                            a_tag.unwrap()
        if linksOptions['Chap/Part TOC']:
            part_file = lableContent.find("section", attrs={'epub:type': 'part'})
            nav_tags = lableContent.find_all("nav")
            headings_files = getting_headings(file_order)
            if part_file and nav_tags:
                lableContent = chapterTOC_process(lableContent, headings_files)
                lableContent = BeautifulSoup(lableContent, "html.parser")
            elif nav_tags:
                temp_file_array = [file]
                headings_files = getting_headings(temp_file_array)
                lableContent = chapterTOC_process(lableContent, headings_files, False)
                lableContent = BeautifulSoup(lableContent, "html.parser")
        if linksOptions['Footnotes/Endnotes']:
            endnotes = lableContent.find("section", attrs={"epub:type": "endnotes"})
            lableContent, endnote_details = footnote_linkprocess(str(lableContent), footnote_details, endnote_details, file, endnotes)
            lableContent = BeautifulSoup(lableContent, "html.parser")
            endnotes = lableContent.find("section", attrs={"epub:type": "endnotes"})
            if endnotes:
                for endnote_detail in endnote_details:
                    if endnote_detail[3] == "done":
                        reverse_link_para = lableContent.find("p", attrs={'id': endnote_detail[1]})
                        reverse_link = reverse_link_para.find("a", attrs={'epub:type': 'endnotelink'})
                        reverse_link['href'] = f'{endnote_detail[5]}#{endnote_detail[4]}'
                for unwanted_link in endnotes.find_all("a", attrs={'href': '#en_'}):
                    unwanted_link.unwrap()
                lableContent = str(lableContent).replace(' epub:type="endnotelink"', "")
                lableContent = BeautifulSoup(lableContent, 'html.parser')
        if linksOptions['Web/eMail']:
            if web_cleanup.get() == "Yes":
                lableContent = web_cleanup_process(str(lableContent))
            lableContent = url_process(str(lableContent))
            lableContent = BeautifulSoup(lableContent, 'html.parser')
        if linksOptions['Index'] and index_file:
            lableContent = indexlink_process(str(lableContent), page_details, pageIDPrefix)
            lableContent = BeautifulSoup(lableContent, "html.parser")
        if linksOptions["Valid/Invalid/404 Complaince"]:
            activelink404_check(str(lableContent), ePub_options, file, file_order)
        title_tag = lableContent.find("title")
        a_tags_in_title = title_tag.find_all('a')
        for a_in_tile in a_tags_in_title:
            a_in_tile.unwrap()
        with open(file, "w", encoding="UTF-8") as forlink:
            forlink.write(str(lableContent))


def entityConvertions(file_order, ePub_options, entity_file, file_name):
    if ePub_options["input_EntityType"] == "Decimal":
        entity_choice = 4
    elif ePub_options["input_EntityType"] == "Hexa-Decimal":
        entity_choice = 5
    elif ePub_options["input_EntityType"] == "SGML":
        entity_choice = 6
    elif ePub_options["input_EntityType"] == "UTF-8":
        entity_choice = 0
    if ePub_options['input_HTMLFolderName'] != 'No Folder':
        error_log_path = f'../../../'
    else:
        error_log_path = f'../../'
    for file in file_order:
        file_alllowed = [".html", ".xhtml", ".htm", ".ncx", ".opf"]
        filename, ext_file = os.path.splitext(file)
        for ext in file_alllowed:
            if ext == ext_file:
                if entity_choice != 0:
                    Entity_Toggle.entity_replace(file, entity_choice, entity_file, error_log_path, file_name)
def epub2_creation(file_order):
    remove_tags = ['header', 'figcaption','col', 'colgroup',]
    rename_tags = [['section','div'],['figure', 'div'], ['aside', 'div']]
    for htmlfile in file_order:
        with open(htmlfile, 'r', encoding='UTF-8') as html:
            reading_content = html.read()
        old_doctype = '<!DOCTYPE html>'
        new_doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">'
        reading_content = reading_content.replace(old_doctype, new_doctype)
        reading_content = re.sub(r' epub:type="([^"]*)"', '', reading_content, flags=re.IGNORECASE)
        reading_content = re.sub(r' role="([^"]*)"', '', reading_content, flags=re.IGNORECASE)
        for rename_tag in rename_tags:
            reading_content = reading_content.replace(f'<{rename_tag[0]}', f'<{rename_tag[1]}')

        html_content = BeautifulSoup(reading_content, 'html.parser')

        for remove_tag in remove_tags:
            unwanted_tags = html_content.find_all(remove_tag)
            for unwanted_tag in unwanted_tags:
                unwanted_tag.unwrap()
        with open(htmlfile, 'w', encoding='UTF-8') as html:
            html.write(str(html_content))

def epub_accessible(file_order, epubRole_info):
    sectiontags = ['section', 'aside', 'article', 'div']
    section = 1
    aside = 1
    article = 1
    div = 1
    head = 1
    epub_role_xml = Et.fromstring(epubRole_info)
    epub_role_pairs = epub_role_xml.findall("pair")
    for htmlfile in file_order:
        with open(htmlfile, 'r', encoding='UTF-8') as html:
            html_cotnent = BeautifulSoup(html, 'html.parser')

        sectiontags_in_html = html_cotnent.find_all(sectiontags)
        for sectiontag_in_html in sectiontags_in_html:
            headertag = sectiontag_in_html.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', "header"],
                                                     recursive=False)
            if headertag:
                if headertag.name == 'header':
                   headertags = headertag.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=False)
                else:
                    headertags = headertag
                if headertags:
                    if headertags.has_attr('id'):
                        sectiontag_in_html['aria-labelledby'] = headertags['id']
                    else:
                        headertags['id'] = 'aria-head' + f'{head}'.zfill(3)
                        sectiontag_in_html['aria-labelledby'] = headertags['id']
            else:
                if not sectiontag_in_html.has_attr('aria-label'):
                    if sectiontag_in_html.name == "section":
                        sectiontag_in_html['aria-label'] = 'Section ' + f'{section}'.zfill(3)
                        section += 1
                    elif sectiontag_in_html.name == "aside":
                        sectiontag_in_html['aria-label'] = 'Case Study ' + f'{aside}'.zfill(3)
                        aside += 1
                    elif sectiontag_in_html.name == "article":
                        sectiontag_in_html['aria-label'] = 'Article ' + f'{article}'.zfill(3)
                        article += 1
                    elif sectiontag_in_html.name == "div":
                        sectiontag_in_html['aria-label'] = 'Division ' + f'{div}'.zfill(3)
                        div += 1

        for epubtype in html_cotnent.find_all(attrs={"epub:type": True}):
            for epub_role_pair in epub_role_pairs:
                epub_type_in_pair = epub_role_pair.find("epub_type").text
                if epubtype['epub:type'] == epub_type_in_pair:
                    epub_role_in_pair = epub_role_pair.find("role").text
                    epubtype['role'] = epub_role_in_pair
                    break



        with open(htmlfile, 'w', encoding='UTF-8') as html:
            html.write(str(html_cotnent))

def ePub_Creation(inputfiles, ePub_options, mapping_content, entity_file, split_info, heading_filename_info,
                  metadetails, navItemfile_info, linksOptions, link_lable_file_info, epubRole_info):
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



        try:
            mimetype = open(f"{filename}/mimetype", "x", encoding="UTF-8")
            mimetype.close()
        except:
            pass
        mimetype = open(f"{filename}/mimetype", "w", encoding="UTF-8")
        mimetype.write("application/epub+zip")
        mimetype.close()

        if ePub_options["input_CSSFilesPath"]:
            Check_CSSFiles = get_all_files_and_dirs(ePub_options["input_CSSFilesPath"])
            if Check_CSSFiles:
                if ePub_options['input_CSSFolderName'] != "No Folder":
                    os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_CSSFolderName']}")
                if ePub_options['input_CSSFolderName'] != "No Folder":
                    shutil.copytree(ePub_options['input_CSSFilesPath'],
                                    f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_CSSFolderName']}",
                                    dirs_exist_ok=True)
                else:
                    shutil.copytree(ePub_options['input_CSSFilesPath'],
                                    f"{filename}/{ePub_options['input_RootFolderName']}", dirs_exist_ok=True)

        if ePub_options['input_HTMLFolderName'] != "No Folder":
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_HTMLFolderName']}")
            shutil.copy2(os.path.join(mapping_content_path, "00_Cover.xhtml"),
                         f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_HTMLFolderName']}")
        else:
            shutil.copy2(os.path.join(mapping_content_path, "00_Cover.xhtml"),
                         f"{filename}/{ePub_options['input_RootFolderName']}/")
        if ePub_options['input_ImageFolderName'] != "No Folder":
            os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_ImageFolderName']}")

            shutil.copy2(ePub_options['input_CoverImagePath'], f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_ImageFolderName']}")
        else:
            shutil.copy2(ePub_options['input_CoverImagePath'],
                         f"{filename}/{ePub_options['input_RootFolderName']}/")

        if ePub_options['input_ImageFilesPath']:
            if ePub_options['input_ImageFolderName'] != "No Folder":
                shutil.copytree(ePub_options['input_ImageFilesPath'],
                            f"{filename}/{ePub_options['input_RootFolderName']}/{ePub_options['input_ImageFolderName']}", dirs_exist_ok=True)
            else:
                shutil.copytree(ePub_options['input_ImageFilesPath'],
                                f"{filename}/{ePub_options['input_RootFolderName']}/", dirs_exist_ok=True)

        if ePub_options['input_FontFilesPath']:
            allowed_fonts = [".ttf", ".otf", ".WOFF", ".WOFF2"]
            Check_FontsFiles = get_all_files_and_dirs(ePub_options['input_FontFilesPath'])
            if Check_FontsFiles:
                os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/Fonts")
                shutil.copytree(ePub_options['input_FontFilesPath'],
                                f"{filename}/{ePub_options['input_RootFolderName']}/Fonts", dirs_exist_ok=True)

        if ePub_options['input_JSFilesPath']:
            Check_JSFiles = get_all_files_and_dirs(ePub_options['input_JSFilesPath'])
            if Check_JSFiles:
                os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/script")
                shutil.copytree(ePub_options['input_JSFilesPath'],
                                f"{filename}/{ePub_options['input_RootFolderName']}/script", dirs_exist_ok=True)

        if ePub_options['input_AudioFilesPath']:
            allowed_audios = [".mp3", ".mp4"]
            Check_MediaFiles = get_all_files_and_dirs(ePub_options['input_AudioFilesPath'])
            if Check_MediaFiles:
                os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/Media")
                shutil.copytree(ePub_options['input_AudioFilesPath'],
                                f"{filename}/{ePub_options['input_RootFolderName']}/Media", dirs_exist_ok=True)

        if ePub_options['input_AudioScriptFilesPath']:
            allowed_audioscripts = [".smil"]
            Check_TranscriptFiles = get_all_files_and_dirs(ePub_options['input_AudioScriptFilesPath'])
            if Check_TranscriptFiles:
                os.mkdir(f"{filename}/{ePub_options['input_RootFolderName']}/Transcript")
                shutil.copytree(ePub_options['input_AudioScriptFilesPath'],
                                f"{filename}/{ePub_options['input_RootFolderName']}/Transcript", dirs_exist_ok=True)

        try:
            pageIDgenration(file, mapping_content, ePub_options, filename, split_info)
        except Exception as error:
            meesage_error = CTkMessagebox(title="Info", message=f"{error}", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()

        try:
            file_order = file_split(file, ePub_options, mapping_content, split_info, heading_filename_info)
        except:
            meesage_error = CTkMessagebox(title="Error", message="File name or ePub Type not defined in Split.xml file", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()


        with open("00_Cover.xhtml", "r", encoding="UTF-8") as cover_file:
            coverhtml_contnet = cover_file.read()
        coverhtml = BeautifulSoup(coverhtml_contnet, "html.parser")
        headtag = coverhtml.find("head")
        htmltag = coverhtml.find("html")
        htmltag['lang'] = langCode
        htmltag['xml:lang'] = langCode

        if ePub_options["input_CSSFilesPath"]:
            if ePub_options['input_HTMLFolderName'] != "No Folder":
                if ePub_options['input_CSSFolderName'] != "No Folder":
                    cssfiles = get_all_files_and_dirs(f"../{ePub_options['input_CSSFolderName']}")
                else:
                    cssfiles = get_all_files_and_dirs(f"..")
            else:
                if ePub_options['input_CSSFolderName'] != "No Folder":
                    cssfiles = get_all_files_and_dirs(f"{ePub_options['input_CSSFolderName']}")
                else:
                    cssfiles = get_all_files_and_dirs(".")
            for css in cssfiles:
                if css.endswith(".css"):
                    linktag = coverhtml.new_tag("link")
                    linktag["rel"] = "stylesheet"
                    linktag["type"] = "text/css"
                    linktag["href"] = css.replace("\\", "/")
                    headtag.append(linktag)
        coverimage = coverhtml.find("img")
        coverfilename = os.path.basename(ePub_options['input_CoverImagePath'])
        coverimage['id'] = "cover"
        if ePub_options['input_HTMLFolderName'] != "No Folder":
            if ePub_options['input_ImageFolderName'] != "No Folder":
                coverimage['src'] = f"../{ePub_options['input_ImageFolderName']}/{coverfilename}"
            else:
                coverimage['src'] = f"../{coverfilename}"
        else:
            if ePub_options['input_ImageFolderName'] != "No Folder":
                coverimage['src'] = f"{ePub_options['input_ImageFolderName']}/{coverfilename}"
            else:
                coverimage['src'] = f"{coverfilename}"

        with open("00_Cover.xhtml", "w", encoding="UTF-8") as cover_file:
            cover_file.write(str(coverhtml))

        try:
            file_order = opfFileCreation(ePub_options, metadetails, filename, file_order, entity_file, navItemfile_info)
        except Exception as error:
            meesage_error = CTkMessagebox(title="Info", message=f"OPF Creation: {error}", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
        try:
            navFileCreation(ePub_options, metadetails, file_order, mapping_content, navItemfile_info, filename)
        except Exception as error:
            meesage_error = CTkMessagebox(title="Info", message=f"NAV Creation: {error}", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
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
        try:
            linkProcess(linksOptions, ePub_options, file_order, link_lable_file_info, entity_file, mapping_content)
        except Exception as error:
            meesage_error = CTkMessagebox(title="Info", message=f"Link Process: {error}", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
        try:
            if ePub_options['input_epub_version'] == 'ePub 2':
                epub2_creation(file_order)
        except Exception as error:
            meesage_error = CTkMessagebox(title="Info", message=f"ePub2 Creation: {error}", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
        try:
            if ePub_options['input_epub_structure'] == 'Accessible':
                epub_accessible(file_order, epubRole_info)
        except Exception as error:
            meesage_error = CTkMessagebox(title="Info", message=f"Package Creation: {error}", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
        entityConvertions(file_order, ePub_options, entity_file, filename)
    return filename

def call_backfiles(field):
    global cssfiles_path
    cssfiles_path = select_files(field)


def select_Path(field):
    selectPath = tk.filedialog.askdirectory()
    field.delete(0, "end")
    field.insert(0, selectPath)
    field.focus()
    return selectPath


def select_files(field):
    selectPath = tk.filedialog.askopenfilenames(filetypes=[("All files", "*.*")])
    field.delete(0, "end")
    field.insert(0, selectPath)
    field.focus()
    return selectPath


def select_file(field, file_type):
    selectPath = tk.filedialog.askopenfilename(filetypes=[*file_type, ("All files", "*.*")])
    field.delete(0, "end")
    field.insert(0, selectPath)
    field.focus_set()
    return selectPath

def input_file_select(fields, file_type, buttons):
    selectPath = tk.filedialog.askopenfilename(filetypes=[*file_type, ("All files", "*.*")])
    inputPath.delete(0, "end")
    inputPath.insert(0, selectPath)
    input_file_path, input_file_name = os.path.split(selectPath)
    for field, value in fields.items():
        field.configure(state="normal")
        field.delete(0, "end")
    if input_file_path:
        for field, value in fields.items():
            field_path = os.path.join(input_file_path, value)
            field.delete(0, "end")
            if value == "COVER":
                field_path = os.path.join(field_path, "cover.jpg")
            elif value == "META":
                field_path = os.path.join(field_path, "meta_data.xlsx")
            field.insert(0, field_path)
            field.configure(state="disabled")
        for button in buttons:
            button.configure(state="disabled")
    else:
        for field, value in fields.items():
            field.delete(0, "end")
            field.configure(state="normal")
        for button in buttons:
            button.configure(state="normal")
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

def rename_tag(inputfiles, mapping_content):

    rename_tags = re.findall('<rename_tag xpath="([^"]*)" old_tag="([^"]*)" new_tag="([^"]*)" new_attrb="([^"]*)" new_attrb_value="([^"]*)" remove_attribs="([^"]*)" rename_old_attrib="([^"]*)" rename_new_attrib="([^"]*)"/>', mapping_content,
                          flags=re.IGNORECASE)

    for file in inputfiles:
        with open(file, "r", encoding="UTF-8") as f:
            content = f.read()
            xml_content = BeautifulSoup(content, 'xml')
        for match in rename_tags:
            xpath, old_tag = match[0], match[1]
            new_tag, new_attribs, new_attrb_values = match[2], match[3].split("|"), match[4].split("|")
            remove_attribs = match[5].split("|")
            rename_old_attrib, rename_new_attrib = match[6], match[7]
            if old_tag and not xpath:
                old_tag = old_tag.replace("\[", '[')
                old_tag = old_tag.replace("\]", ']')
                old_tag = old_tag.replace("'", '"')
                rename_tag_secletion = xml_content.select(old_tag)
            elif old_tag and xpath:
                xpath = xpath.replace("\[", '[')
                xpath = xpath.replace("\]", ']')
                xpath = xpath.replace("'", '"')
                xpath = xpath.replace('\\', ">")
                xpath = xpath.replace('/', ">")
                xpath = xpath.replace('|', ">")
                old_tag = f'{xpath}>{old_tag}'
                rename_tag_secletion = xml_content.select(old_tag)

            for rename_tag in rename_tag_secletion:
                rename_tag.name = new_tag
                if new_attribs and new_attrb_values:
                    for attib, value in zip(new_attribs, new_attrb_values):
                        if attib:
                            rename_tag[f'{attib}'] = value
                if rename_old_attrib:
                    if rename_tag.has_attr(rename_old_attrib):
                        rename_tag[rename_new_attrib] = rename_tag.attrs.pop(rename_old_attrib)
                if remove_attribs:
                    for remove_attrib in remove_attribs:
                        if remove_attrib:
                            del rename_tag[remove_attrib]


        with open(file, "w", encoding="UTF-8") as f:
            xml_content = str(xml_content)
            f.write(xml_content)
def delete_tag(inputfiles, mapping_content):
    del_tags = re.findall('<delete_tag xpath="([^"]*)" tag_name="([^"]*)" delete_content="([^"]*)"/>', mapping_content, flags=re.IGNORECASE)
    for file in inputfiles:
        with open(file, "r", encoding="UTF-8") as f:
            content = f.read()
            xml_content = BeautifulSoup(content, 'xml')
        for del_tag in del_tags:
            xpath = del_tag[0]
            del_tag_name = del_tag[1]
            del_content = del_tag[2].upper()
            if del_tag_name and not xpath:
                del_tag_name = del_tag_name.replace("\[", '[')
                del_tag_name = del_tag_name.replace("\]", ']')
                del_tag_name = del_tag_name.replace("'", '"')
                del_tag_name = del_tag_name
                delete_tag_secletion = xml_content.select(del_tag_name)
            elif del_tag_name and xpath:
                xpath = xpath.replace("\[", '[')
                xpath = xpath.replace("\]", ']')
                xpath = xpath.replace("'", '"')
                xpath = xpath.replace('\\', ">")
                xpath = xpath.replace('/', ">")
                xpath = xpath.replace('|', ">")
                del_tag_name = f'{xpath}>{del_tag_name}'
                delete_tag_secletion = xml_content.select(del_tag_name)
            elif xpath:
                xpath = xpath.replace("\[", '[')
                xpath = xpath.replace("\]", ']')
                xpath = xpath.replace("'", '"')
                xpath = xpath.replace('\\', ">")
                xpath = xpath.replace('/', ">")
                xpath = xpath.replace('|', ">")
                del_tag_name = xpath
                delete_tag_secletion = xml_content.select(del_tag_name)
            for delete_tag in delete_tag_secletion:
                if del_content == "YES":
                    delete_tag.extract()
                elif del_content == "NO":
                    delete_tag.unwrap()

        with open(file, "w", encoding="UTF-8") as f:
            xml_content = str(xml_content)
            xml_content = xml_content.replace("epub_type=", "epub:type=")
            f.write(xml_content)
# Prgram Start Here
# __________________
# global alpha_num
# alpha_num = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L', 13: 'M', 14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V', 23: 'W', 24: 'X', 25: 'Y', 26: 'Z'}
path = os.getcwd()
mapping_content_path = os.path.join(path, "Support")
os.chdir(mapping_content_path)
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
ImageFolderName_list = gui_data_root.find("ImagesFolderName").text.split(",")
project_confi_file = Et.parse("project_confi.xml")
project_confi_root = project_confi_file.getroot()
project_list = project_confi_root.findall("publisher")


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

with open("epubType_ePubRole.xml", "r", encoding="UTF-8") as role:
    epubRole_info = role.read()

def conversion(epubOptions):
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

    linksOptions = {"Figure": figurelink.get(), "Table": tablelink.get(), "Chapter": chapterlink.get(),
                    "Box": boxlink.get(), "Chap/Part TOC": ChapTOClink.get(),
                    "Footnotes/Endnotes": footnotelink.get(),
                    "Web/eMail": weblink.get(), "Index": indexlink.get(),
                    "Valid/Invalid/404 Complaince": web_link404.get()}
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
        submitButton.configure(state="normal")
        meesage_error = CTkMessagebox(title="Error", message="\"entity.ini\" is not found in Support folder", options=["OK"], justify="center", width=50, height=30, icon="cancel")
        meesage_info = meesage_error.get()
    if epubOptions['input_checkHyphen']:
        try:
            language, language_code = epubOptions['input_lang'].split("-")
            exception_filename = f"{language.lower()}.ini"
            exception_file = open(os.path.join(mapping_content_path, exception_filename), "r", encoding="utf8")
        except:
            meesage_error = CTkMessagebox(title="Error", message=f"\"{exception_filename}\" is not found in Support folder", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
    try:
        mapping_file = open(os.path.join(mapping_content_path, f"{mappping_doc_name}"), "r", encoding="UTF-8")
    except:
        submitButton.configure(state="normal")
        meesage_error = CTkMessagebox(title="Error", message=f"{mappping_doc_name} is missing!, \n Check Support folders and Project Confic XML file", options=["OK"],
                      justify="center",  width=50, height=30,  icon="cancel")
        meesage_info = meesage_error.get()
    mapping_content = mapping_file.read()
    mapping_content = mapping_content.replace("[", "\[")
    mapping_content = mapping_content.replace("]", "\]")
    mapping_file.close()



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


    try:
        metadata_exel = pandas.read_excel(epubOptions['input_MetaExcel'], header=0,
                                          sheet_name=f'{epubOptions["input_publisher"]}')
        isJobPresent = jobnoChecking(epubOptions, metadata_exel)
    except:
        meesage_error = CTkMessagebox(title="Error", message="Meta excel Sheet name ", options=["OK"], justify="center", width=50, height=30, icon="cancel")
        meesage_info = meesage_error.get()
        submitButton.configure(state="normal")
    if not isJobPresent:
        meesage_error = CTkMessagebox(title="Error", message="Job no. is missing in Metadata excel", options=["OK"], justify="center", width=50, height=30, icon="cancel")
        meesage_info = meesage_error.get()
        submitButton.configure(state="normal")
    elif isJobPresent:
        metadetails = metadata_exel.loc[metadata_exel['Job No'] == epubOptions['input_jobno']]
        metadetails = metadetails.to_dict('records')
        if pandas.isna(metadetails[0]['Title']):
            meesage_error = CTkMessagebox(title="Error", message="Book Title. is missing in Metadata excel", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif pandas.isna(metadetails[0]['Author']):
            meesage_error = CTkMessagebox(title="Error", message="Auther name(s) are missing in Metadata excel", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif pandas.isna(metadetails[0]['e-ISBN']):
            meesage_error = CTkMessagebox(title="Error", message="e-ISBN is missing in Metadata excel", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif pandas.isna(metadetails[0]['Publisher']):
            meesage_error = CTkMessagebox(title="Error", message="Publisher is missing in Metadata excel", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif pandas.isna(metadetails[0]['Pages']):
            meesage_error = CTkMessagebox(title="Error", message="Page count is missing in Metadata excel", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif pandas.isna(metadetails[0]['Copyrights']):
            meesage_error = CTkMessagebox(title="Error", message="Copyright information is missing in Metadata excel", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        else:
            try:
                os.mkdir("Output")
            except FileExistsError:
                try:
                    shutil.rmtree("Output")
                    os.mkdir("Output")
                except:
                    meesage_error = CTkMessagebox(title="Info", message=f"Problem with creating Output folder", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
            try:
                if xhtml_validation(input_htmlfile):
                    outputPath = os.path.join(path, "Output")
                    shutil.copy2(user_inputfile, outputPath)
                else:
                    try:
                        os.mkdir("Invalid_file")
                        meesage_error = CTkMessagebox(title="Error", message="Invalid HTML File, Please check the error Report", options=["OK"], justify="center", width=50, height=30, icon="cancel")
                        meesage_info = meesage_error.get()
                        submitButton.configure(state="normal")
                    except:
                        meesage_error = CTkMessagebox(title="Error", message="Invalid HTML File, Problem with Creating Folder", options=["OK"], justify="center", width=50, height=30, icon="cancel")
                        meesage_info = meesage_error.get()
                        submitButton.configure(state="normal")
                    errorfile_path = os.path.join(path, "Invalid_file")
                    shutil.copy2(user_inputfile, errorfile_path)

            except:
                meesage_error = CTkMessagebox(title="Info", message=f"{input_htmlfile} is already exit!", options=["OK"], justify="center", width=50, height=30)
                meesage_info = meesage_error.get()
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
                try:
                    pre_replace(inputfiles, mapping_content)
                    progress_bar.set(.1)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Pre Cleanup: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    rename_tag(inputfiles, mapping_content)
                    delete_tag(inputfiles, mapping_content)
                    tag_groupping(inputfiles, mapping_content, True)
                    tag_nested(inputfiles, mapping_content)
                    progress_bar.set(.15)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Tag Grupping and Nesting: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    text_movement(inputfiles, mapping_content, link_lable_file_info, linksOptions)

                    progress_bar.set(.4)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Text Movment: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    tag_groupping(inputfiles, mapping_content)
                    progress_bar.set(.45)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Groupping: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    listing(inputfiles, mapping_content)
                    progress_bar.set(.5)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"List Format: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    tag_mapping(inputfiles, mapping_content)
                    progress_bar.set(.55)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Tag Mapping: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
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
                    progress_bar.set(.6)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Hyphen Check: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    list_tagcleaup(inputfiles, mapping_content)
                    progress_bar.set(.65)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"List Cleanup: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    post_replace(inputfiles, mapping_content)
                    progress_bar.set(.7)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Post Cleanup: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    filename = ePub_Creation(inputfiles, epubOptions, mapping_content, entity_file, split_info, heading_filename_info,
                                  metadetails, navItemfile_info, linksOptions, link_lable_file_info, epubRole_info)
                    progress_bar.set(.85)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"Package Creation: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
                try:
                    epubFileformation(metadetails, filename, epubOptions, mapping_content_path)
                    progress_bar.set(1)
                    current_value = progress_bar.get()
                    progress_bar.update_idletasks()
                    progress_bar_value.configure(text=f'{int(current_value * 100)}%')
                    progress_bar_value.update_idletasks()
                except Exception as error:
                    meesage_error = CTkMessagebox(title="Info", message=f"ePub Creation: {error}", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    submitButton.configure(state="normal")
            meesage_error = CTkMessagebox(title="Info", message="ePub Converted Sucessfully!", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")


def onselect():
    global input_filetype
    if xmlinput:
        input_filetype = [("XML files", "*.xml"), ("XHTML files", "*.xhtml"), ("HTML files", "*.html")]
    else:
        input_filetype = [("HTML files", "*.html"), ("XHTML files", "*.xhtml")]
def dowload_excel():
    excel_loc = f"{path}/Support/Meta_Template.xlsx"
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="Meta_Template.xlsx",
                                             filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
    shutil.copyfile(excel_loc, file_path)
    meesage_error = CTkMessagebox(title="Info", message="The template file has been downloaded.", options=["OK"], justify="center", width=50, height=30)
    meesage_info = meesage_error.get()
def newProject():
    input_lang, input_epub_version, input_epub_structure = lang_info.get(), ePub_version_info.get(), ePub_type_info.get()
    input_opfName, input_NCXName, input_HTMLFileName, input_EntityType, input_FileSplit, input_footnoteMovement, input_Navigation = OpfName_info.get(), ncx_file_info.get(), HTML_file_info.get(), entity_type_info.get(), fileSplit_info.get(), footnoteMovement_info.get(), Navigation_info.get()
    input_RootFolderName, input_HTMLFolderName, input_CSSFolderName, input_ImageFolderName = root_folder_info.get(), HTML_folder_info.get(), CSS_folder_info.get(), Image_folder_info.get()

    def createProject():
        global new_projectname
        new_projectname = name_field.get()
        if new_projectname == "":
            meesage_error = CTkMessagebox(title="Info", message=f"Please enter project name!", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
        else:
            if os.path.exists(name_mapping_field.get()):
                if os.path.exists(os.path.join(mapping_content_path, os.path.basename(name_mapping_field.get()))):
                    meesage_error = CTkMessagebox(title="Error", message="This mapping document already exit!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
                    meesage_info = meesage_error.get()
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
                    new_ImageFolderName = Et.SubElement(new_element, "ImagesFolderName")
                    new_ImageFolderName.text = input_ImageFolderName
                    new_mappingDoc = Et.SubElement(new_element, "mappingDoc")


                    new_link_set = Et.SubElement(new_element, "Links")
                    new_figlink = Et.SubElement(new_link_set, "Figure")
                    if figurelink.get():
                        new_figlink.text = "Yes"
                    else:
                        new_figlink.text = "No"
                    new_tablink = Et.SubElement(new_link_set, "Table")
                    if tablelink.get():
                        new_tablink.text = "Yes"
                    else:
                        new_tablink.text = "No"

                    new_footnotelink = Et.SubElement(new_link_set, "Footnote")
                    if footnotelink.get():
                        new_footnotelink.text = "Yes"
                    else:
                        new_footnotelink.text = "No"

                    new_chapterlink = Et.SubElement(new_link_set, "Chapter_Part")
                    if chapterlink.get():
                        new_chapterlink.text = "Yes"
                    else:
                        new_chapterlink.text = "No"

                    new_boxlink = Et.SubElement(new_link_set, "Box")
                    if boxlink.get():
                        new_boxlink.text = "Yes"
                    else:
                        new_boxlink.text = "No"

                    new_chapTOClink = Et.SubElement(new_link_set, "Chap_Part_Toc")
                    if ChapTOClink.get():
                        new_chapTOClink.text = "Yes"
                    else:
                        new_chapTOClink.text = "No"

                    new_indexlink = Et.SubElement(new_link_set, "Index")
                    if indexlink.get():
                        new_indexlink.text = "Yes"
                    else:
                        new_indexlink.text = "No"

                    new_weblink = Et.SubElement(new_link_set, "Web_Email")
                    if weblink.get():
                        new_weblink.text = "Yes"
                    else:
                        new_weblink.text = "No"

                    new_web404link = Et.SubElement(new_link_set, "Validation")
                    if web_link404.get():
                        new_web404link.text = "Yes"
                    else:
                        new_web404link.text = "No"
                    new_mappingDoc.text = os.path.basename(name_mapping_field.get())
                    project_confi_root.append(new_element)
                    os.chdir(path)
                    project_confi_file.write("Support/project_confi.xml")
                    gui_data_file.write("Support/gui_confi.xml")
                    meesage_error = CTkMessagebox(title="Info", message="New project created Sucessfully!", options=["OK"], justify="center", width=50, height=30)
                    meesage_info = meesage_error.get()
                    new_gui.destroy()
                else:
                    meesage_error = CTkMessagebox(title="Error", message="Please choose valid xml file!", options=["OK"],
                                  justify="center", width=50, height=30, icon="cancel")
                    meesage_info = meesage_error.get()
                    new_gui.focus_set()
            else:
                meesage_error = CTkMessagebox(title="Error", message="Please choose valid mapping document!", options=["OK"],
                              justify="center",  width=50, height=30,  icon="cancel")
                meesage_info = meesage_error.get()
                new_gui.focus_set()

    new_gui = ct.CTkToplevel(uiWindow)
    sub_gui = GUI(new_gui, 350, 180)
    new_gui.title("Project Name")
    name_lable = ct.CTkLabel(new_gui, text="New Project Name:", pady=10)
    name_field = ct.CTkEntry(new_gui)
    new_gui.deiconify()
    name_mapping = ct.CTkLabel(new_gui, text="Mapping Document:", pady=10)
    name_mapping_field = ct.CTkEntry(new_gui)
    name_mapping_button = ct.CTkButton(new_gui, text="...", width=30,
                                       command=lambda: select_file(name_mapping_field, [("xml file", "*.xml")]))

    name_lable.grid(row=0, column=0, padx=10, pady=10)
    name_field.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="w")
    name_mapping.grid(row=1, column=0, padx=10, pady=10)
    name_mapping_field.grid(row=1, column=1, padx=10, pady=10, sticky="w")
    name_mapping_button.grid(row=1, column=2, sticky="w")

    submitButton = ct.CTkButton(new_gui, text="Create", command=createProject)
    CancelButton = ct.CTkButton(new_gui, text="Cancel", command=new_gui.withdraw)
    submitButton.grid(row=2, column=0, padx=3, pady=8)
    CancelButton.grid(row=2, column=1, pady=8)
    subwarning_label = ct.CTkLabel(new_gui, text_color="red", text="", padx=10)
    subwarning_label.grid(row=3, column=0, columnspan=3, padx=3, pady=5)
    new_gui.focus()

def progress_update():
    progress_bar.grid(row=1, column=0, columnspan=2, pady=5)
    progress_bar_value.grid(row=1, column=2, pady=5)
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
        "input_ImageFolderName": Image_folder_info.get(),
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
        "input_checkHyphen": hyphen.get(),
        "input_xml": xmlinput.get()
    }
    user_inputfile = inputPath.get()
    path, input_htmlfile = os.path.split(user_inputfile)
    if not user_inputfile:
        meesage_error = CTkMessagebox(title="Info", message=f"Please select input file!", options=["OK"], justify="center", width=50, height=30)
        meesage_info = meesage_error.get()
    else:
        try:
            os.chdir(path)
        except:
            meesage_error = CTkMessagebox(title="Info", message=f"Invalid Path!", options=["OK"], justify="center", width=50, height=30)
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
            path = ""
            inputPath.delete(0, 'end')
        if not job_no_filed.get():
            meesage_error = CTkMessagebox(title="Error", message="Enter Job no.", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif not os.path.exists(epubOptions['input_CoverImagePath']):
            meesage_error = CTkMessagebox(title="Error", message="Cover image is missing!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif not os.path.exists(epubOptions['input_MetaExcel']):
            meesage_error = CTkMessagebox(title="Error", message="Meta Excel is Missing!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif not os.path.exists(epubOptions['input_CSSFilesPath']):
            meesage_error = CTkMessagebox(title="Error", message="CSS folder is Missing!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif not os.path.exists(epubOptions['input_ImageFilesPath']):
            meesage_error = CTkMessagebox(title="Error", message="IMG folder is Missing!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif not os.path.exists(epubOptions['input_FontFilesPath']):
            meesage_error = CTkMessagebox(title="Error", message="FONTS folder is Missing!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif not os.path.exists(epubOptions['input_JSFilesPath']):
            meesage_error = CTkMessagebox(title="Error", message="JS folder is Missing!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        elif not os.path.exists(epubOptions['input_AudioFilesPath']):
            meesage_error = CTkMessagebox(title="Error", message="MEDIA folder is Missing!", options=["OK"], justify="center", width=50, height=30, icon="cancel")
            meesage_info = meesage_error.get()
            submitButton.configure(state="normal")
        else:
            thread1 = threading.Thread(target=conversion(epubOptions))
            thread1.start()
            def update():
                if thread1.is_alive():
                    submitButton.configure(state="disabled")
                else:
                    submitButton.configure(state="normal")
                    progress_bar.grid_forget()
                    progress_bar_value.grid_forget()

        update()


def on_select(event):
    for child in project_list:
        for subchild in child:
            if event == subchild.text:
                for item in child:
                    if item.tag == "Language":
                        lang_info.set(item.text)
                        lang_filed.configure(state="disabled")
                    elif item.tag == "epubVersion":
                        ePub_version_info.set(item.text)
                        ePub_version_filed.configure(state="disabled")
                    elif item.tag == "ePubStructure":
                        ePub_type_info.set(item.text)
                        ePub_type_filed.configure(state="disabled")
                    elif item.tag == "OpfName":
                        OpfName_info.set(item.text)
                        opf_file_filed.configure(state="disabled")
                    elif item.tag == "HTMLFileName":
                        HTML_file_info.set(item.text)
                        HTML_file_filed.configure(state="disabled")
                    elif item.tag == "NCXName":
                        ncx_file_info.set(item.text)
                        ncx_file_filed.configure(state="disabled")
                    elif item.tag == "EntityType":
                        entity_type_info.set(item.text)
                        entity_type_filed.configure(state="disabled")
                    elif item.tag == "fileSplit":
                        fileSplit_info.set(item.text)
                        fileSplit_filed.configure(state="disabled")
                    elif item.tag == "RootFolderName":
                        root_folder_info.set(item.text)
                        root_folder_filed.configure(state="disabled")
                    elif item.tag == "HTMLFolderName":
                        HTML_folder_info.set(item.text)
                        HTML_folder_filed.configure(state="disabled")
                    elif item.tag == "CSSFolderName":
                        CSS_folder_info.set(item.text)
                        CSS_folder_filed.configure(state="disabled")
                    elif item.tag == "ImagesFolderName":
                        Image_folder_info.set(item.text)
                        Image_folder_filed.configure(state="disabled")
                    elif item.tag == "footnoteMovement":
                        footnoteMovement_info.set(item.text)
                        footnoteMovement_filed.configure(state="disabled")
                    elif item.tag == "Navigation":
                        Navigation_info.set(item.text)
                        Navigation_filed.configure(state="disabled")
                    elif item.tag == "Links":
                        for linkitem in item:
                            if linkitem.tag == "Figure":
                                if linkitem.text.upper() == "YES":
                                    figurelink.set(1)
                                    figlink_checkbox.configure(state="disabled")
                                else:
                                    figurelink.set(0)
                                    figlink_checkbox.configure(state="normal")

                            elif linkitem.tag == "Table":
                                if linkitem.text.upper() == "YES":
                                    tablelink.set(1)
                                    tablink_checkbox.configure(state="disabled")
                                else:
                                    tablelink.set(0)
                                    tablink_checkbox.configure(state="normal")
                            elif linkitem.tag == "Footnote":
                                if linkitem.text.upper() == "YES":
                                    footnotelink.set(1)
                                    fnlink_checkbox.configure(state="disabled")
                                else:
                                    footnotelink.set(0)
                                    fnlink_checkbox.configure(state="normal")
                            elif linkitem.tag == "Chapter_Part":
                                if linkitem.text.upper() == "YES":
                                    chapterlink.set(1)
                                    chaplink_checkbox.configure(state="disabled")
                                else:
                                    chapterlink.set(0)
                                    chaplink_checkbox.configure(state="normal")
                            elif linkitem.tag == "Box":
                                if linkitem.text.upper() == "YES":
                                    boxlink.set(1)
                                    boxlink_checkbox.configure(state="disabled")
                                else:
                                    boxlink.set(0)
                                    boxlink_checkbox.configure(state="normal")
                            elif linkitem.tag == "Chap_Part_Toc":
                                if linkitem.text.upper() == "YES":
                                    ChapTOClink.set(1)
                                    ChapTOClink_checkbox.configure(state="disabled")
                                else:
                                    ChapTOClink.set(0)
                                    ChapTOClink_checkbox.configure(state="normal")
                            elif linkitem.tag == "Index":
                                if linkitem.text.upper() == "YES":
                                    indexlink.set(1)
                                    indexlink_checkbox.configure(state="disabled")
                                else:
                                    indexlink.set(0)
                                    indexlink_checkbox.configure(state="normal")
                            elif linkitem.tag == "Web_Email":
                                if linkitem.text.upper() == "YES":
                                    weblink.set(1)
                                    weblink_checkbox.configure(state="disabled")
                                else:
                                    weblink.set(0)
                                    weblink_checkbox.configure(state="normal")
                            elif linkitem.tag == "Validation":
                                if linkitem.text.upper() == "YES":
                                    web_link404.set(1)
                                    web_link404_checkbox.configure(state="disabled")
                                else:
                                    web_link404.set(0)
                                    web_link404_checkbox.configure(state="normal")
                    elif item.tag == "includeFigureInNav":
                        if item.text.upper() == "YES":
                            figureInclude.set(1)
                            figureInclude_checkbox.configure(state="disabled")
                        else:
                            figureInclude.set(0)
                            figureInclude_checkbox.configure(state="normal")
                    elif item.tag == "includeTableInNav":

                        if item.text.upper() == "YES":
                            tableInclude.set(1)
                            tableInclude_checkbox.configure(state="disabled")
                        else:
                            tableInclude.set(0)
                            tableInclude_checkbox.configure(state="normal")

            elif event == "Common":
                lang_filed.configure(state="normal")
                ePub_version_filed.configure(state="normal")
                ePub_type_filed.configure(state="normal")
                opf_file_filed.configure(state="normal")
                HTML_file_filed.configure(state="normal")
                ncx_file_filed.configure(state="normal")
                entity_type_filed.configure(state="normal")
                fileSplit_filed.configure(state="normal")
                root_folder_filed.configure(state="normal")
                HTML_folder_filed.configure(state="normal")
                CSS_folder_filed.configure(state="normal")
                Image_folder_filed.configure(state="normal")
                footnoteMovement_filed.configure(state="normal")
                Navigation_filed.configure(state="normal")
                tableInclude_checkbox.configure(state="normal")
                figureInclude_checkbox.configure(state="normal")

def on_version(event):
    if event == "ePub 2":
        ePub_type_filed.configure(state="disabled")
        ePub_type_info.set("")
    elif event == "ePub 3":
        ePub_type_filed.configure(state="normal")
        ePub_type_info.set("Semantic")

def checkbox_event():
    global input_filetype
    value = xmlinput.get()
    if value == "1":
        input_filetype = [("XML files", "*.xml"), ("XHTML files", "*.xhtml"), ("HTML files", "*.html")]
    else:
        input_filetype = [("HTML files", "*.html"), ("XHTML files", "*.xhtml")]




uiWindow = ct.CTk(fg_color=("#ebebeb", "black"))
gui = GUI(uiWindow, 650, 330)
uiWindow.title("Epub Conversion Tool - Version 2.0.0")
icon = PhotoImage(file=f"{path}/Support/icon.png")
excel_icon = ct.CTkImage(Image.open(f"{path}/Support/excel-download-icon.gif"), size=(20,20))
uiWindow.iconphoto(True, icon)
ct.set_appearance_mode("dark")
ct.set_default_color_theme("dark-blue")

heading = ct.CTkLabel(uiWindow, text="HTML to ePub", font=("Arial Black", 20), justify="center", corner_radius=14, padx=20, pady=10, width=630)
heading.pack()
tab_veiw = ct.CTkTabview(uiWindow, height=200, fg_color=("#ebebeb", "black"))
Common_frame = ct.CTkFrame(uiWindow, fg_color=("#ebebeb", "black"))
tab_veiw.pack()
Common_frame.pack()
input_filetype = [("HTML files", "*.html"), ("XHTML files", "*.xhtml")]
tab_1 = tab_veiw.add("Input")
tab_2 = tab_veiw.add("Meta Info")
tab_3 = tab_veiw.add("Folder Option")
tab_4 = tab_veiw.add("Links")
tab_5 = tab_veiw.add("Media Files")
tab_6 = tab_veiw.add("Others")

# Tab 5 Content
css_path = ct.CTkLabel(tab_5, text="CSS:")
css_path_filed = ct.CTkEntry(tab_5)
css_selectPath = ct.CTkButton(tab_5, text="...", command=lambda: select_Path(css_path_filed), width=20, height=3)
cover_path = ct.CTkLabel(tab_5, text="Cover Image*:", text_color="red")
cover_path_filed = ct.CTkEntry(tab_5)
cover_selectPath = ct.CTkButton(tab_5, text="...", command=lambda: select_file(cover_path_filed, [("jpeg files","*.jpg"),("PNG files", "*.png")]), width=20, height=3)
image_path = ct.CTkLabel(tab_5, text="Images:")
image_path_filed = ct.CTkEntry(tab_5)
image_selectPath = ct.CTkButton(tab_5, text="...", command=lambda: select_Path(image_path_filed), width=20, height=3)
font_path = ct.CTkLabel(tab_5, text="Fonts:")
font_path_filed = ct.CTkEntry(tab_5)
font_selectPath = ct.CTkButton(tab_5, text="...", command=lambda: select_Path(font_path_filed), width=20, height=3)

js_path = ct.CTkLabel(tab_5, text="JS:")
js_path_filed = ct.CTkEntry(tab_5)
js_selectPath = ct.CTkButton(tab_5, text="...", command=lambda: select_Path(js_path_filed), width=20, height=3)

audio_path = ct.CTkLabel(tab_5, text="Audios/Vidoes:")
audio_path_filed = ct.CTkEntry(tab_5)
audio_selectPath = ct.CTkButton(tab_5, text="...", command=lambda: select_Path(audio_path_filed), width=20, height=3)

audioScript_path = ct.CTkLabel(tab_5, text="Audio Script:")
audioScript_filed = ct.CTkEntry(tab_5)
audioScript_selectpath = ct.CTkButton(tab_5, text="...", command=lambda: select_Path(audioScript_filed), width=20, height=3)

meta_exel = ct.CTkLabel(tab_5, text="Meta Excel*:", text_color="red")
meta_exel_filed = ct.CTkEntry(tab_5)
meta_exel_selectPath = ct.CTkButton(tab_5, text="...",
                                 command=lambda: select_file(meta_exel_filed, [("Excel file", "*.xlsx")]), width=20, height=3)

excel_temlate = ct.CTkButton(tab_5, image=excel_icon, text="", command=dowload_excel, width=20, height=20)

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
js_path.grid(row=0, column=3, pady=3, padx=3, sticky="e")
js_path_filed.grid(row=0, column=4, pady=3, padx=8)
js_selectPath.grid(row=0, column=5, padx=8, sticky="w")
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

# Tab 1 content
inputLable = ct.CTkLabel(tab_1, text="Enter path: ", pady=10)
inputPath = ct.CTkEntry(tab_1, placeholder_text="Enter Path")
manutary_fields = {css_path_filed: "CSS", cover_path_filed: "COVER", image_path_filed: "IMG", font_path_filed: "FONTS", js_path_filed: "JS", audio_path_filed: "MEDIA", audioScript_filed: "MEDIA", meta_exel_filed: "META"}
manutary_field_buttons = [css_selectPath, cover_selectPath, image_selectPath, font_selectPath, js_selectPath, audio_selectPath, audioScript_selectpath, meta_exel_selectPath]
input_selectPath = ct.CTkButton(tab_1, text="...", command=lambda: input_file_select(manutary_fields, input_filetype, manutary_field_buttons), width=30, height=5)
xmlinput = ct.StringVar()
xmlinput_checkbox = ct.CTkCheckBox(tab_1, text="XML input", command=checkbox_event,
                                     variable=xmlinput, onvalue=1, offvalue=0, checkbox_width=18, checkbox_height=18)
publisher_lable = ct.CTkLabel(tab_1, text="Publisher: ")
publisher_info = ct.StringVar()
publisher_info.set("Common")
publisher_filed = ct.CTkComboBox(tab_1, values=PublisherName_list, variable=publisher_info, command=on_select)
job_no = ct.CTkLabel(tab_1, text="Job No*:", text_color="red")
job_no_filed = ct.CTkEntry(tab_1)

# Tab 1 grid System
inputLable.grid(row=0, column=0, sticky="e", pady=10)
inputPath.grid(row=0, column=1, sticky="w", padx=8, pady=10)
input_selectPath.grid(row=0, column=2, padx=3, sticky="w", pady=10)
xmlinput_checkbox.grid(row=0, column=3, padx=3, sticky="w", pady=10)
publisher_lable.grid(row=1, column=0, pady=10, padx=3, sticky="e")
publisher_filed.grid(row=1, column=1, pady=10, padx=8, sticky="w")
job_no.grid(row=2, column=0, pady=3, padx=10, sticky="e")
job_no_filed.grid(row=2, column=1, pady=10, padx=8, sticky="w")

# Tab 2 Content
lang = ct.CTkLabel(tab_2, text="Language:")
lang_info = ct.StringVar()
lang_info.set(Language_list[0])
lang_filed = ct.CTkComboBox(tab_2, values=Language_list, variable=lang_info)
ePub_version = ct.CTkLabel(tab_2, text="ePub Version:")
ePub_version_info = ct.StringVar()
ePub_version_info.set(epubVersion_list[0])
ePub_version_filed = ct.CTkComboBox(tab_2, values=epubVersion_list, variable=ePub_version_info, command=on_version)
ePub_type = ct.CTkLabel(tab_2, text="ePub Structure:")
ePub_type_info = ct.StringVar()
ePub_type_info.set(ePubStructure_list[0])
ePub_type_filed = ct.CTkComboBox(tab_2, values=ePubStructure_list, variable=ePub_type_info)
HTML_file = ct.CTkLabel(tab_2, text="HTML File Name:")
HTML_file_info = ct.StringVar()
HTML_file_info.set(HTMLFileName_list[0])
HTML_file_filed = ct.CTkComboBox(tab_2, values=HTMLFileName_list, variable=HTML_file_info)
entity_type = ct.CTkLabel(tab_2, text="Entity Type:")
entity_type_info = ct.StringVar()
entity_type_info.set(EntityType_list[0])
entity_type_filed = ct.CTkComboBox(tab_2, values=EntityType_list, variable=entity_type_info)
fileSplit = ct.CTkLabel(tab_2, text="File Split:")
fileSplit_info = ct.StringVar()
fileSplit_info.set(fileSplit_list[0])
fileSplit_filed = ct.CTkComboBox(tab_2, values=fileSplit_list, variable=fileSplit_info)
footnoteMovement = ct.CTkLabel(tab_2, text="Footnote Movement:")
footnoteMovement_info = ct.StringVar()
footnoteMovement_info.set(footnoteMovement_list[0])
footnoteMovement_filed = ct.CTkComboBox(tab_2, values=footnoteMovement_list, variable=footnoteMovement_info)
Navigation = ct.CTkLabel(tab_2, text="Navigation:")
Navigation_info = ct.StringVar()
Navigation_info.set(Navigation_list[0])
Navigation_filed = ct.CTkComboBox(tab_2, values=Navigation_list, variable=Navigation_info)


# Tab 2 Grid System
lang.grid(row=0, column=0, pady=3, padx=3, sticky="e")
lang_filed.grid(row=0, column=1, pady=3, padx=8, sticky="w")
ePub_version.grid(row=1, column=0, pady=3, padx=3, sticky="e")
ePub_version_filed.grid(row=1, column=1, pady=3, padx=8, sticky="w")
ePub_type.grid(row=2, column=0, pady=3, padx=3, sticky="e")
ePub_type_filed.grid(row=2, column=1, pady=3, padx=8, sticky="w")

HTML_file.grid(row=3, column=0, pady=3, padx=3, sticky="e")
HTML_file_filed.grid(row=3, column=1, pady=3, padx=8)
entity_type.grid(row=0, column=2, pady=3, padx=3, sticky="e")
entity_type_filed.grid(row=0, column=3, pady=3, padx=8)
fileSplit.grid(row=1, column=2, pady=3, padx=3, sticky="e")
fileSplit_filed.grid(row=1, column=3, pady=3, padx=8)
footnoteMovement.grid(row=2, column=2, pady=3, padx=3, sticky="e")
footnoteMovement_filed.grid(row=2, column=3, pady=3, padx=8)
Navigation.grid(row=3, column=2, pady=3, padx=3, sticky="e")
Navigation_filed.grid(row=3, column=3, pady=3, padx=8)



# Tab 3 Conent
root_folder = ct.CTkLabel(tab_3, text="Root Folder Name:")
root_folder_info = ct.StringVar()
root_folder_info.set(RootFolderName_list[0])
root_folder_filed = ct.CTkComboBox(tab_3, values=RootFolderName_list, variable=root_folder_info)
HTML_folder = ct.CTkLabel(tab_3, text="HTML Folder Name:")
HTML_folder_info = ct.StringVar()
HTML_folder_info.set(HTMLFolderName_list[0])
HTML_folder_filed = ct.CTkComboBox(tab_3, values=HTMLFolderName_list, variable=HTML_folder_info)
CSS_folder = ct.CTkLabel(tab_3, text="CSS Folder Name:")
CSS_folder_info = ct.StringVar()
CSS_folder_info.set(CSSFolderName_list[0])
CSS_folder_filed = ct.CTkComboBox(tab_3, values=CSSFolderName_list, variable=CSS_folder_info)

Image_folder = ct.CTkLabel(tab_3, text="Image Folder Name:")
Image_folder_info = ct.StringVar()
Image_folder_info.set(ImageFolderName_list[0])
Image_folder_filed = ct.CTkComboBox(tab_3, values=ImageFolderName_list, variable=Image_folder_info)

opf_file = ct.CTkLabel(tab_3, text="OPF File Name:")
OpfName_info = ct.StringVar()
OpfName_info.set(OpfName_list[0])
opf_file_filed = ct.CTkComboBox(tab_3, values=OpfName_list, variable=OpfName_info)
ncx_file = ct.CTkLabel(tab_3, text="NCX File Name:")
ncx_file_info = ct.StringVar()
ncx_file_info.set(NCXName_list[0])
ncx_file_filed = ct.CTkComboBox(tab_3, values=NCXName_list, variable=ncx_file_info, )

root_folder.grid(row=0, column=0, pady=3, padx=3, sticky="e")
root_folder_filed.grid(row=0, column=1, pady=3, padx=8)
HTML_folder.grid(row=1, column=0, pady=3, padx=3, sticky="e")
HTML_folder_filed.grid(row=1, column=1, pady=3, padx=8)
CSS_folder.grid(row=2, column=0, pady=3, padx=3, sticky="e")
CSS_folder_filed.grid(row=2, column=1, pady=3, padx=8)
Image_folder.grid(row=0, column=2, pady=3, padx=3, sticky="e")
Image_folder_filed.grid(row=0, column=3, pady=3, padx=8)
opf_file.grid(row=1, column=2, pady=3, padx=3, sticky="e")
opf_file_filed.grid(row=1, column=3, pady=3, padx=8)
ncx_file.grid(row=2, column=2, pady=3, padx=3, sticky="e")
ncx_file_filed.grid(row=2, column=3, pady=3, padx=8)



# Tab 4 Conentent
figurelink = ct.BooleanVar()
figlink_checkbox = ct.CTkCheckBox(tab_4, text="Figure", variable=figurelink, checkbox_width=18, checkbox_height=18)
tablelink = ct.BooleanVar()
tablink_checkbox = ct.CTkCheckBox(tab_4, text="Table", variable=tablelink, checkbox_width=18, checkbox_height=18)
footnotelink = ct.BooleanVar()
fnlink_checkbox = ct.CTkCheckBox(tab_4, text="Footnotes", variable=footnotelink, checkbox_width=18, checkbox_height=18)
chapterlink = ct.BooleanVar()
chaplink_checkbox = ct.CTkCheckBox(tab_4, text="Chapter/Part", variable=chapterlink, checkbox_width=18, checkbox_height=18)
boxlink = ct.BooleanVar()
boxlink_checkbox = ct.CTkCheckBox(tab_4, text="Box", variable=boxlink, checkbox_width=18, checkbox_height=18)
ChapTOClink = ct.BooleanVar()
ChapTOClink_checkbox = ct.CTkCheckBox(tab_4, text="Chapter/Part TOC", variable=ChapTOClink, checkbox_width=18, checkbox_height=18)
weblink = ct.BooleanVar()
weblink_checkbox = ct.CTkCheckBox(tab_4, text="Web/eMail", variable=weblink, checkbox_width=18, checkbox_height=18)
indexlink = ct.BooleanVar()
indexlink_checkbox = ct.CTkCheckBox(tab_4, text="Index", variable=indexlink, checkbox_width=18, checkbox_height=18)
web_link404 = ct.BooleanVar()
web_link404_checkbox = ct.CTkCheckBox(tab_4, text="Valid/Invalid Weblink", variable=web_link404, checkbox_width=18, checkbox_height=18)

# Tab 4 Grid System
figlink_checkbox.grid(row=0, column=0, sticky="w", pady=5)
tablink_checkbox.grid(row=1, column=0, sticky="w", pady=5)
fnlink_checkbox.grid(row=2, column=0, sticky="w", pady=5)
chaplink_checkbox.grid(row=0, column=1, sticky="w", pady=5, padx=10)
boxlink_checkbox.grid(row=1, column=1, sticky="w", pady=5, padx=10)
ChapTOClink_checkbox.grid(row=2, column=1, sticky="w", pady=5, padx=10)
indexlink_checkbox.grid(row=0, column=2, sticky="w", pady=5)
weblink_checkbox.grid(row=1, column=2, sticky="w", pady=5)
web_link404_checkbox.grid(row=2, column=2, sticky="w", pady=5)





# Tab 6 Content
hyphen = ct.BooleanVar()
hyphen_checkbox = ct.CTkCheckBox(tab_6, text="Hyphen Check", variable=hyphen, checkbox_height=18, checkbox_width=18)
tableInclude = ct.BooleanVar()
tableInclude_checkbox = ct.CTkCheckBox(tab_6, text="Tables in Nav", variable=tableInclude, checkbox_height=18, checkbox_width=18)
figureInclude = ct.BooleanVar()
figureInclude_checkbox = ct.CTkCheckBox(tab_6, text="Figures in Nav", variable=figureInclude, checkbox_height=18, checkbox_width=18)
pageOffset = ct.CTkLabel(tab_6, text="Page offset: ")
pageOffset_filed = ct.CTkEntry(tab_6, width=50)
pageOffset_filed.insert(0, "0")

hyphen_checkbox.grid(row=0, column=0, sticky="w", pady=5)
tableInclude_checkbox.grid(row=1, column=0, sticky="w", pady=5)
figureInclude_checkbox.grid(row=2, column=0, sticky="w", pady=5)
pageOffset.grid(row=0, column=1, sticky="e", rowspan=3, padx=10)
pageOffset_filed.grid(row=0, column=2, sticky="e", rowspan=3, padx=5)

def switch_event():
    ct.set_appearance_mode(switch_var.get())

submitButton = ct.CTkButton(Common_frame, text="Process", command=progress_update)
copyofProjectButton = ct.CTkButton(Common_frame, text="Copy/New Project", command=newProject)
CancelButton = ct.CTkButton(Common_frame, text="Cancel", command=uiWindow.destroy)
progress_bar = ct.CTkProgressBar(Common_frame, orientation="horizontal", determinate_speed=0.1, width=290)
switch_var = ct.StringVar(value="dark")
switch = ct.CTkSwitch(Common_frame, text="Dark Mode", command=switch_event,
                                 variable=switch_var, onvalue="dark", offvalue="light")
progress_bar.grid_forget()
progress_bar_value = ct.CTkLabel(Common_frame, text="")
progress_bar_value.grid_forget()
submitButton.grid(row=0, column=0, padx=3, pady=10)
copyofProjectButton.grid(row=0, column=1, padx=3, pady=10)
CancelButton.grid(row=0, column=2, pady=10)
switch.grid(row=1, column=3, pady=10)


uiWindow.mainloop()
