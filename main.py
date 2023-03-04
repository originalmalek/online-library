import argparse
import json
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from environs import Env
from pathvalidate import sanitize_filename


def check_for_redirects(response):
	if response.history:
		raise requests.HTTPError


def parse_book_page(book_id):


	response = requests.get(f'https://tululu.org/b{book_id}/')
	response.raise_for_status()

	soup = BeautifulSoup(response.text, 'lxml')

	book_name = sanitize_filename(soup.find('h1').text.split('::')[0].strip())
	book_author = sanitize_filename(soup.find('h1').text.split('::')[1].strip())
	book_image_url = soup.find('div', class_='bookimage').find('img')['src']
	book_comments = soup.find_all('div', class_='texts')
	book_genres = soup.find('span', class_='d_book').find_all('a')

	comments = [book_comment.find('span').text for book_comment in book_comments]
	genres = [book_genre.text for book_genre in book_genres]

	return {'book_name': book_name,
	        'book_author': book_author,
	        'book_image_url': book_image_url,
	        'book_comments': comments,
	        'book_genres': genres}


def download_txt_book(response, book_name, book_id, books_folder):
	file_name = f'{book_id}. {book_name}.txt'

	with open(os.path.join(books_folder, file_name), 'wb') as file:
		file.write(response.content)


def download_book_image(book_image_url, books_images_folder, url):
	image_name = os.path.basename(book_image_url)

	if os.path.exists(f'{books_images_folder}/{image_name}'):
		return False

	full_image_url = urljoin(url, book_image_url)

	response = requests.get(full_image_url)
	response.raise_for_status()

	with open(os.path.join(books_images_folder, image_name), 'wb') as file:
		file.write(response.content)


def save_books_file(books_file_name, books):
	with open(books_file_name, 'w') as fp:
		json.dump(books, fp, ensure_ascii=False)


def main():
	parser = argparse.ArgumentParser(description='''Программа для скачивания книг и информации о них с сайта 
		                                             https://tululu.org/ ''')

	parser.add_argument('-s', '--start_id', help='Номер первой книги парсинга', type=int)
	parser.add_argument('-e', '--end_id', help='Номер последней книги парсинга', type=int)
	args = parser.parse_args()

	books = {}
	start_id = args.start_id
	end_id = args.end_id

	env = Env()
	env.read_env()

	books_folder = env('BOOKS_FOLDER')
	books_images_folder = env('BOOKS_IMAGES_FOLDER')
	books_file_name = env('BOOKS_FILE_NAME')

	os.makedirs(books_folder, exist_ok=True)
	os.makedirs(books_images_folder, exist_ok=True)

	url = 'https://tululu.org/'

	for book_id in range(start_id, end_id + 1):
		payload = {'id': book_id}
		book_download_url = urljoin(url, 'txt.php')

		response = requests.get(book_download_url, params=payload)

		try:
			check_for_redirects(response)

			book = parse_book_page(book_id)

			download_txt_book(response, book['book_name'], book_id, books_folder)
			download_book_image(book['book_image_url'], books_images_folder, url)

			books[book_id] = book

		except requests.exceptions.HTTPError as err:
			print('Книги с таким id не существует')

		save_books_file(books_file_name, books)


if __name__ == '__main__':
	main()
