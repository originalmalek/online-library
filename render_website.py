import argparse
import json
import os
import shutil
from environs import Env
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import grouper, chunked


def render_page(book_image_folder, books, chunked_books, page_number, site_directory, page_quantity):
    template = env.get_template('template.html')

    rendered_page = template.render(
        books=books,
        book_image_folder=book_image_folder,
        chunked_books=chunked_books,
        page_quantity=page_quantity,
        page_number=page_number,
    )
    with open(f'{site_directory}/index{page_number}.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


def on_reload():
    render_pages(books_file_name, book_image_folder, site_directory)


def render_pages(books_file_name, book_image_folder, site_directory):
    books_file_name = os.path.join(destination_folder, books_file_name)

    with open(books_file_name, "r") as my_file:
        books_json = my_file.read()

    books = json.loads(books_json)

    chunked_books = list(chunked(grouper(books, 2, incomplete='fill', fillvalue='0'), 5))
    page_quantity = len(chunked_books)
    for page_number, books_group in enumerate(chunked_books, start=1):
        render_page(book_image_folder, books, books_group, page_number, site_directory, page_quantity)


def parse_arguments():
    parser = argparse.ArgumentParser(description='''Программа генерации веб сайта с книгами''')
    parser.add_argument('-sd', '--site_directory',
                        help='путь к каталогу с результатами парсинга: картинкам, книгам, JSON',
                        type=str,
                        default='site')
    parser.add_argument('-bd', '--books_directory',
                        help='путь к каталогу с результатами парсинга: картинкам, книгам, JSON',
                        type=str,
                        default='books')
    parser.add_argument('-jn', '--json_name',
                        help='Указать своё имя к *.json файлу с результатами',
                        type=str,
                        default='books.json')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()

    env = Env()
    env.read_env()
    books_file_name = args.json_name
    site_directory = args.site_directory
    destination_folder = args.books_directory
    book_image_folder = './images'
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    shutil.copytree('resources', f'{site_directory}/resources', dirs_exist_ok = True)
    shutil.copytree(f'{destination_folder}/images', f'{site_directory}/images', dirs_exist_ok=True)
    shutil.copytree(f'{destination_folder}/books', f'{site_directory}/books', dirs_exist_ok=True)

    on_reload()

    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root=f'{site_directory}')
