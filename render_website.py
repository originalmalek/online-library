from livereload import Server, shell
import json
from environs import Env
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_page(books_file_name, book_image_folder):
    with open(books_file_name, "r") as my_file:
        books_json = my_file.read()

    books = json.loads(books_json)
    print(books)
    template = env.get_template('template.html')

    rendered_page = template.render(
        books = books,
        book_image_folder = book_image_folder
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


def on_reload():
    render_page(books_file_name, book_image_folder)


if __name__ == '__main__':
    env = Env()
    env.read_env()
    books_file_name = env('BOOKS_FILE_NAME')
    book_image_folder = env('BOOKS_IMAGES_FOLDER')
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    on_reload()
    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')
