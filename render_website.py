from livereload import Server, shell
import json
from environs import Env
from jinja2 import Environment, FileSystemLoader, select_autoescape
from more_itertools import grouper, chunked
import os


def render_page(book_image_folder, books, chunked_books, page_number, site_directory, page_quantity):
    template = env.get_template('template.html')

    rendered_page = template.render(
        books = books,
        book_image_folder = book_image_folder,
        chunked_books = chunked_books,
        page_quantity = page_quantity,
        page_number = page_number,
    )
    print(page_quantity)
    with open(f'{site_directory}/index{page_number}.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


def on_reload():
    render_pages(books_file_name, book_image_folder, site_directory)


def render_pages(books_file_name, book_image_folder, site_directory):
    with open(books_file_name, "r") as my_file:
        books_json = my_file.read()

    books = json.loads(books_json)

    chunked_books = list(chunked(grouper(books, 2, incomplete='fill', fillvalue='0'), 5))
    page_quantity = len(chunked_books)
    print()
    print(page_quantity)
    for page_number, books_group in enumerate(chunked_books, start=1):
        render_page(book_image_folder, books, books_group, page_number, site_directory, page_quantity)



if __name__ == '__main__':
    env = Env()
    env.read_env()
    books_file_name = env('BOOKS_FILE_NAME')
    book_image_folder = env('BOOKS_IMAGES_FOLDER')
    site_directory = env('SITE_DIRECTORY')
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    os.makedirs(site_directory, mode=0o777, exist_ok=True)

    on_reload()
    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')
