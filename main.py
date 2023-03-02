import requests
import os


def download_book(url, book_id):
    url = url + str(book_id)

    response = requests.get(url)
    response.raise_for_status()

    filename = f'book{book_id}.txt'
    with open(f'books/{filename}', 'wb') as file:
        file.write(response.content)

def downolad_books(url, start_id: int, end_id: int):
    for book_id in range(start_id, end_id + 1):
        download_book(url, book_id)


if __name__ == '__main__':
    url = 'https://tululu.org/txt.php?id='
    downolad_books(url, 1, 10)

