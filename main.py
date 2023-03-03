import requests
import os
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from urllib.parse import urljoin
from environs import Env


def check_for_redirects(response):
    if response.status_code != 200:
        raise requests.HTTPError


def get_book_info(book_id):
    comments = []
    genres = []
    response = requests.get(f'https://tululu.org/b{book_id}/')
    # response = requests.get(f'https://tululu.org/b10/')
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')

    book_name = sanitize_filename(soup.find('h1').text.split('::')[0].strip())
    book_author = sanitize_filename(soup.find('h1').text.split('::')[1].strip())
    book_image_url = soup.find('div', class_='bookimage').find('img')['src']
    book_comments = soup.find_all('div', class_='texts')
    book_genres = soup.find('span', class_='d_book').find_all('a')

    for book_comment in book_comments:
        comments.append(book_comment.find('span').text)

    for book_genre in book_genres:
        genres.append(book_genre.text)
    print(book_name)
    print(genres)
    return {'book_name': book_name,
            'book_author': book_author,
            'book_image_url': book_image_url,
            'book_comments': book_comments,
            'book_genres': book_genres}


def download_book(response, book_name, book_id, books_folder):
    file_name = f'{book_id}. {book_name}.txt'

    with open(os.path.join(books_folder, file_name), 'wb') as file:
        file.write(response.content)


def download_book_image(book_image_url, books_images_folder, url):
    image_name = os.path.basename(book_image_url)
    print(image_name)
    if os.path.exists(f'{books_images_folder}/{image_name}'):
        return False

    full_image_url = urljoin(url, book_image_url)

    response = requests.get(full_image_url)
    response.raise_for_status()

    with open(os.path.join(books_images_folder, image_name), 'wb') as file:
        file.write(response.content)


def download_book_data(url, book_id, books_folder, books_images_folder):
    url = url + str(book_id)
    response = requests.get(url, allow_redirects=False)

    try:
        check_for_redirects(response)
    except requests.HTTPError:
        return False

    book_info = get_book_info(book_id)

    # download_book(response, book_info['book_name'], book_id, books_folder)

    # download_book_image(book_info['book_image_url'], books_images_folder, url)


def download_books(url: str, start_id: int, end_id: int,
                   books_folder: str, books_images_folder: str):
    for book_id in range(start_id, end_id + 1):
        download_book_data(url, book_id, books_folder, books_images_folder)


if __name__ == '__main__':
    env = Env()
    env.read_env()

    books_folder = env('BOOKS_FOLDER')
    books_images_folder = env('BOOKS_IMAGES_FOLDER')

    os.makedirs(books_folder, exist_ok=True)
    os.makedirs(books_images_folder, exist_ok=True)

    url = 'https://tululu.org/txt.php?id='
    download_books(url, 1, 10, books_folder, books_images_folder)

