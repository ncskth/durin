"""Loads saved Durin data from .npz, pickle, or gzip files."""

from pathlib import Path
import argparse
import pickle
import gzip
import numpy as np


def load_pz(path: Path):
	with path.open("rb") as file_handle:
		magic = file_handle.read(2)

	if magic == b"PK":
		return np.load(path, allow_pickle=True)

	with path.open("rb") as file_handle:
		try:
			return pickle.load(file_handle)
		except Exception:
			pass

	try:
		with gzip.open(path, "rb") as file_handle:
			return pickle.load(file_handle)
	except Exception:
		pass

	try:
		return np.load(path, allow_pickle=True)
	except Exception as err:
		raise ValueError(f"Formato non supportato o file corrotto: {path}") from err


def describe(obj):
	print(f"Tipo principale: {type(obj).__name__}")

	if isinstance(obj, dict):
		print(f"Chiavi ({len(obj)}):")
		for key, value in obj.items():
			print(f"  - {key}: {type(value).__name__}")
		return

	if isinstance(obj, np.lib.npyio.NpzFile):
		keys = list(obj.files)
		print(f"Array in NPZ ({len(keys)}):")
		for key in keys:
			arr = obj[key]
			print(f"  - {key}: shape={arr.shape}, dtype={arr.dtype}")
		return

	if isinstance(obj, np.ndarray):
		print(f"shape={obj.shape}, dtype={obj.dtype}")
		return

	if isinstance(obj, (list, tuple)):
		print(f"Elementi: {len(obj)}")
		if len(obj) > 0:
			print(f"Tipo primo elemento: {type(obj[0]).__name__}")


def print_array_preview(arr: np.ndarray, head: int = 10):
	print("\n--- Preview dati ---")
	if arr.size == 0:
		print("Array vuoto")
		return

	rows = min(head, len(arr))

	if arr.dtype.names is not None:
		print(f"Prime {rows} righe:")
		for idx, row in enumerate(arr[:rows]):
			values = ", ".join(f"{name}={row[name]}" for name in arr.dtype.names)
			print(f"  [{idx}] {values}")

		print("\nStatistiche campi:")
		for name in arr.dtype.names:
			field = arr[name]
			if np.issubdtype(field.dtype, np.number):
				print(
					f"  - {name}: min={field.min()}, max={field.max()}, mean={field.mean():.4f}"
				)
			else:
				print(f"  - {name}: tipo non numerico ({field.dtype})")
	else:
		print(f"Prime {rows} righe:")
		print(arr[:rows])
		if np.issubdtype(arr.dtype, np.number):
			print(
				f"\nStatistiche: min={arr.min()}, max={arr.max()}, mean={arr.mean():.4f}"
			)


def main():
	parser = argparse.ArgumentParser(description="Legge un file .pz (pickle, anche compresso)")
	parser.add_argument("file", nargs="?", default="/home/agata/Documents/kth/durin/sparse_data.npz", help="Percorso file .npz/.pz")
	parser.add_argument("--key", default="sparse_data", help="Chiave array nel file NPZ")
	parser.add_argument("--head", type=int, default=10, help="Numero di righe da mostrare")
	args = parser.parse_args()

	file_path = Path(args.file)
	if not file_path.exists():
		raise FileNotFoundError(f"File non trovato: {file_path}")

	data = load_pz(file_path)
	print(f"File letto: {file_path}")
	describe(data)

	if isinstance(data, np.lib.npyio.NpzFile):
		if args.key in data.files:
			selected_array = data[args.key]
		else:
			first_key = data.files[0]
			print(f"\nChiave '{args.key}' non trovata, uso '{first_key}'")
			selected_array = data[first_key]

		print_array_preview(selected_array, args.head)
		data.close()
	elif isinstance(data, np.ndarray):
		print_array_preview(data, args.head)


if __name__ == "__main__":
	main()