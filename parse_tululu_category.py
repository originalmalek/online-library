from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import re
import os
from environs import Env
import json
from pathvalidate import sanitize_filename
from time import sleep
from main import check_for_redirects, parse_book_page, download_txt_book, download_book_image
from main import save_books_file


def main():
    url = 'https://tululu.org/'
    category_id = 'l55'
    category_url = urljoin(url, category_id)
    category_page = 1

    books = {}

    env = Env()
    env.read_env()

    books_folder = env('BOOKS_FOLDER')
    books_images_folder = env('BOOKS_IMAGES_FOLDER')
    books_file_name = env('BOOKS_FILE_NAME')

    os.makedirs(books_folder, exist_ok=True)
    os.makedirs(books_images_folder, exist_ok=True)

    while category_page < 2:

        response = requests.get(f'{category_url}/{category_page}')

        soup = BeautifulSoup(response.text, 'lxml')

        on_page_books_selector = 'div#content table.d_book'
        on_page_books = soup.select(on_page_books_selector)

        for book in on_page_books:
            book_id = re.search('\d+', book.select_one('a')['href'])[0]
            payload = {'id': book_id}
            book_download_url = urljoin(url, 'txt.php')
            book_url = urljoin(url, f'b{book_id}/')

            try:
                response_book = requests.get(book_download_url, params=payload)
                response_book.raise_for_status()

                response_page = requests.get(book_url)
                response_page.raise_for_status()

                check_for_redirects(response_book)
                check_for_redirects(response_page)

                book = parse_book_page(response_page)

                download_txt_book(response_book, book['book_name'], book_id, books_folder)
                download_book_image(book['book_image_url'], books_images_folder, book_url)
                print(book_id)
                books[book_id] = book

            except requests.ConnectionError:
                print('Ошибка соединения, следующая попытка через 60 секунд')
                sleep(60)
                continue

            except requests.HTTPError:
                print(f'Книги с id {book_id} или описания к ней не существует')

        category_page += 1

    save_books_file(books_file_name, books)

if __name__ == '__main__':
    main()
