import argparse
import json
import os
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from environs import Env
from pathvalidate import sanitize_filename


def check_for_redirects(response):
    if response.history:
        raise requests.HTTPError


def parse_book_page(page_response):
    soup = BeautifulSoup(page_response.text, 'lxml')

    book_name, book_author = soup.select_one('h1').text.split('::')
    book_name = sanitize_filename(book_name.strip())
    book_author = sanitize_filename(book_author.strip())
    book_image_url_selector = 'div.bookimage img'
    book_comments_selector = 'div.texts span.black'
    book_genres_selector = 'span.d_book a'
    book_image_url = soup.select_one(book_image_url_selector)['src']
    book_image_name = os.path.basename(book_image_url)
    book_comments = soup.select(book_comments_selector)
    book_genres = soup.select(book_genres_selector)

    comments = [book_comment.text for book_comment in book_comments]
    genres = [book_genre.text for book_genre in book_genres]

    return {'book_name': book_name,
            'book_image_name': book_image_name,
            'book_author': book_author,
            'book_image_url': book_image_url,
            'book_comments': comments,
            'book_genres': genres}


def download_txt_book(response, book_name, book_id, books_folder):
    file_name = f'{book_id}. {book_name}.txt'

    with open(os.path.join(books_folder, file_name), 'wb') as file:
        file.write(response.content)

    return file_name

def download_book_image(book_image_url, books_images_folder, url):
    image_name = os.path.basename(book_image_url)

    full_image_url = urljoin(url, book_image_url)

    response = requests.get(full_image_url)
    response.raise_for_status()

    with open(os.path.join(books_images_folder, image_name), 'wb') as file:
        file.write(response.content)


def save_books_file(books_file_name, books):
    with open(books_file_name, 'w') as fp:
        json.dump(books, fp, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description='''Программа для скачивания книг и информации
													о них с сайта https://tululu.org/''')

    parser.add_argument('-s', '--start_id', help='Номер первой книги парсинга', type=int, default=1)
    parser.add_argument('-e', '--end_id', help='Номер последней книги парсинга', type=int, default=10)
    args = parser.parse_args()

    books = {}
    book_id = args.start_id
    end_id = args.end_id

    env = Env()
    env.read_env()

    books_folder = env('BOOKS_FOLDER')
    books_images_folder = env('BOOKS_IMAGES_FOLDER')
    books_file_name = env('BOOKS_FILE_NAME')

    os.makedirs(books_folder, exist_ok=True)
    os.makedirs(books_images_folder, exist_ok=True)

    url = 'https://tululu.org/'

    while book_id <= end_id:
        payload = {'id': book_id}
        book_download_url = urljoin(url, 'txt.php')
        book_url = urljoin(url, f'b{book_id}/')

        try:
            book_response = requests.get(book_download_url, params=payload)
            book_response.raise_for_status()

            page_response = requests.get(book_url)
            page_response.raise_for_status()

            check_for_redirects(book_response)
            check_for_redirects(page_response)

            book = parse_book_page(page_response)

            download_txt_book(book_response, book['book_name'], book_id, books_folder)
            book_name = download_txt_book(book_response,
                                                book['book_name'],
                                                book_id, books_folder)

            books[book_id] = book
            books[book_id]['book_name'] = book_name

        except requests.ConnectionError:
            print('Ошибка соединения, следующая попытка через 60 секунд')
            sleep(60)
            continue

        except requests.HTTPError:
            print(f'Книги с id {book_id} или описания к ней не существует')

        book_id += 1

    save_books_file(books_file_name, books)


if __name__ == '__main__':
    main()
