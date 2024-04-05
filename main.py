import requests
import xml.etree.ElementTree as ET
import csv
import os
import sys
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedStyle
from tkinter import messagebox
import pandas as pd
import re
import yaml
from tkinter import font
import tkinter.font as font


def extract_dimensions(text):
  dimensions = re.finditer(
      r'(\d+(?:[.,]\d+)?)[*/-](\d+(?:[.,]\d+)?)(?:[*/-](\d+(?:[.,]\d+)?))?(?:\s*[,;]+\s*|\s*$)',
      text)
  dimension_str = ""
  for match in dimensions:
    length = match.group(1).replace(',', '.')
    width = match.group(2).replace(',', '.')
    height = match.group(3).replace(',', '.') if match.group(3) else '0'
    dimension_str += f"length:{length};width:{width};height:{height}\n"
  return dimension_str


def get_category_path(category_id, root):
  category_path = []
  while category_id is not None:
    category_elem = root.find(f".//category[@id='{category_id}']")
    category_name = category_elem.text
    category_path.append(category_name)
    category_id = category_elem.get('parentId')
  category_path.reverse()
  return '/'.join(category_path)


def process_link():
  link_url = entry.get()
  if link_url:
    try:
      response = requests.get(link_url)
      response.raise_for_status()
      xml_data = response.content.decode('utf-8')

      root = ET.fromstring(xml_data)

      data = []
      for offer_elem in root.findall('.//offer'):
        offer_id = offer_elem.get('id')
        offer_data = {'id': offer_id}
        category_id = offer_elem.find('.//categoryId').text
        if category_id:
          category_path = get_category_path(category_id, root)
          offer_data = {'id': offer_id, 'category_path': category_path}
        for category_elem in offer_elem:
          category_name = category_elem.tag
          category_value = category_elem.text
          offer_data[category_name] = category_value

        link_elems = offer_elem.findall('.//link')
        links = "///".join(link_elem.text for link_elem in link_elems)
        offer_data['links'] = links

        picture_elems = offer_elem.findall('.//picture')
        pictures = "///".join(picture_elem.text
                              for picture_elem in picture_elems)
        offer_data['pictures'] = pictures

        param_elems = offer_elem.findall('.//param')
        params = {
            param_elem.get('name'): param_elem.text
            for param_elem in param_elems
        }
        offer_data.update(params)

        data.append(offer_data)

      save_path = os.path.expanduser('~/Documents/CSV')
      os.makedirs(save_path, exist_ok=True)

      file_path = os.path.join(save_path, 'data.csv')

      category_names = set()
      for row in data:
        category_names.update(row.keys())

      for row in data:
        if 'description' in row:
          if row['description']:
            paragraphs = row['description'].split('\n')
            paragraphs = ['<p>' + p + '</p>' for p in paragraphs if p.strip()]
            row['description'] = '<br>'.join(paragraphs)

        if 'dimension' in row:
          if row['dimension']:
            row['dimension'] = extract_dimensions(row['dimension'])

      with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file,
                                fieldnames=sorted(category_names),
                                delimiter=';')
        writer.writeheader()
        writer.writerows(data)

      messagebox.showinfo(
          "Success",
          "CSV успешно сохранен в файле data.csv, в ~/Documents/CSV с кодировкой UTF-8"
      )
    except:
      messagebox.showerror("Error", "Произошла ошибка при обработке ссылки")


def paste_from_clipboard():
  link_url = window.clipboard_get()
  entry.delete(0, tk.END)
  entry.insert(0, link_url)


# Создание корневого окна
window = tk.Tk()
window.title("GreenData")

# Установка темы
style = ThemedStyle(window)
style.set_theme("equilux")

font_url = "https://fonts.googleapis.com/css2?family=Kalnia:wght@100&display=swap"
font.families()
kalnia_font = font.Font(family='Kalnia', size=12)

main_frame = ttk.Frame(window, padding=20)
main_frame.pack(expand=True, fill=tk.BOTH)

label = ttk.Label(main_frame,
                  text="Введите ссылку для обработки:",
                  font=kalnia_font)
label.pack(pady=10)

window.geometry("600x280")

entry = ttk.Entry(main_frame, width=50, font=kalnia_font)
entry.pack()

process_button = ttk.Button(main_frame, text="Начать", command=process_link)
process_button.pack(pady=10)

paste_button = ttk.Button(main_frame,
                          text="Вставить из буфера обмена",
                          command=paste_from_clipboard)
paste_button.pack(pady=10)

signature_label = ttk.Label(main_frame,
                            text="Made by Asbjorn\\Version 0.8",
                            font=("Helvetica", 7))
signature_label.pack(side=tk.RIGHT, pady=(10, 20), anchor=tk.SE, padx=10)

window.mainloop()
