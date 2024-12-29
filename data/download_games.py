import requests
import os
import zstandard as zstd
import chess.pgn
import io
from tqdm import tqdm
import argparse
from datetime import datetime, timedelta
import glob
import sys
import humanize

def download_file(url, output_path, chunk_size=8192):
    """Download a file with progress bar."""
    try:
        print(f"\n>>> Attempting to download from: {url}")
        
        # First check if the file exists on the server
        response = requests.head(url)
        if response.status_code == 404:
            print(f"[ERROR] File not found on server (404 error)")
            return False
        elif response.status_code != 200:
            print(f"[ERROR] Server returned status code: {response.status_code}")
            return False
        
        # File exists, proceed with download
        print(f"[OK] File found! Starting download...")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        if total_size == 0:
            print("[WARN] Warning: Content length is 0, file might be empty")
            return False
        
        print(f"[INFO] File size: {humanize.naturalsize(total_size, binary=True)}")
        progress_bar = tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            desc="Downloading",
            bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )
        
        with open(output_path, 'wb') as f:
            for data in response.iter_content(chunk_size=chunk_size):
                size = f.write(data)
                progress_bar.update(size)
        
        progress_bar.close()
        
        # Verify file was downloaded correctly
        if os.path.getsize(output_path) != total_size:
            print(f"[ERROR] Downloaded file size ({humanize.naturalsize(os.path.getsize(output_path), binary=True)}) doesn't match expected size ({humanize.naturalsize(total_size, binary=True)})")
            os.remove(output_path)
            return False
        
        print(f"[OK] Download completed successfully: {output_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error downloading file: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def process_games(input_file, output_file, min_elo=2000, max_games=None):
    """Process games from a PGN file, filtering by Elo rating."""
    print(f"\n[INFO] Processing games (min Elo: {min_elo})...")
    games_processed = 0
    games_kept = 0
    start_time = datetime.now()
    buffer_size = 1024 * 1024  # 1MB buffer
    
    try:
        total_size = os.path.getsize(input_file)
        
        with open(output_file, 'w', buffering=buffer_size) as outfile:
            with open(input_file, buffering=buffer_size) as infile:
                pbar = tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc="Processing games",
                    bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                    mininterval=1.0
                )
                
                game_reader = chess.pgn.read_game
                
                while True:
                    try:
                        current_pos = infile.tell()
                        game = game_reader(infile)
                        if game is None:
                            break
                        
                        games_processed += 1
                        new_pos = infile.tell()
                        pbar.update(new_pos - current_pos)
                        
                        headers = game.headers
                        try:
                            white_elo = int(headers.get("WhiteElo", "0"))
                            black_elo = int(headers.get("BlackElo", "0"))
                            
                            if white_elo >= min_elo and black_elo >= min_elo:
                                print(game, file=outfile, end="\n\n", flush=False)
                                games_kept += 1
                                
                                if max_games and games_kept >= max_games:
                                    break
                        except ValueError:
                            continue
                        
                        if games_processed % 5000 == 0:
                            elapsed = datetime.now() - start_time
                            rate = games_processed / elapsed.total_seconds()
                            pbar.set_postfix({
                                'Games': f'{games_processed:,}',
                                'Kept': f'{games_kept:,}',
                                'Rate': f'{rate:.1f} games/s'
                            }, refresh=True)
                    except Exception as e:
                        print(f"\n[WARN] Error processing game: {e}")
                        continue
                
                pbar.close()
        
        elapsed = datetime.now() - start_time
        rate = games_processed / elapsed.total_seconds()
        kept_ratio = (games_kept / games_processed * 100) if games_processed > 0 else 0
        
        print(f"\n[OK] Processing complete:")
        print(f"[INFO] Statistics:")
        print(f"  * Total games processed: {games_processed:,}")
        print(f"  * Games kept: {games_kept:,} ({kept_ratio:.1f}%)")
        print(f"  * Processing time: {humanize.naturaldelta(elapsed)}")
        print(f"  * Processing rate: {rate:.1f} games/s")
        
        return games_kept > 0
    except Exception as e:
        print(f"\n[ERROR] Error during processing: {str(e)}")
        return False

def estimate_bytes_for_games(file_path, num_games=10000):
    """Estimate the file size needed for the specified number of games."""
    try:
        total_size = os.path.getsize(file_path)
        
        # Sample the first 1000 games to get average game size
        games_read = 0
        bytes_read = 0
        
        with open(file_path) as f:
            while games_read < 1000:
                start_pos = f.tell()
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                end_pos = f.tell()
                bytes_read += (end_pos - start_pos)
                games_read += 1
        
        if games_read == 0:
            return total_size
        
        avg_bytes_per_game = bytes_read / games_read
        estimated_size = int(avg_bytes_per_game * num_games * 1.1)  # Add 10% buffer
        
        # Don't return larger than file size
        return min(estimated_size, total_size)
    except Exception as e:
        print(f"[WARN] Error estimating file size: {e}")
        return total_size

def truncate_file(input_path, output_path, max_size):
    """Copy the first max_size bytes from input to output."""
    try:
        with open(input_path, 'rb') as infile, open(output_path, 'wb') as outfile:
            outfile.write(infile.read(max_size))
        return True
    except Exception as e:
        print(f"[ERROR] Error truncating file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download and process chess games")
    parser.add_argument('--download', action='store_true',
                        help='Download the latest database')
    parser.add_argument('--month', type=str,
                        help='Specific month to download (YYYY-MM format)')
    parser.add_argument('--output-dir', type=str, default='.',
                        help='Directory to save the processed files')
    parser.add_argument('--min-elo', type=int, default=2000,
                        help='Minimum Elo rating for games')
    parser.add_argument('--max-games', type=int, default=None,
                        help='Maximum number of games to keep')
    args = parser.parse_args()
    
    print("\n=== Lichess Game Downloader and Processor ===")
    print("============================================")
    
    os.makedirs(args.output_dir, exist_ok=True)
    compressed_path = os.path.join(args.output_dir, "lichess_games.pgn.zst")
    raw_path = os.path.join(args.output_dir, "lichess_games_raw.pgn")
    filtered_path = os.path.join(args.output_dir, "lichess_games_filtered.pgn")
    
    if args.download:
        # Construct URL based on month
        if args.month:
            url = f"https://database.lichess.org/standard/lichess_db_standard_rated_{args.month}.pgn.zst"
            if not download_file(url, compressed_path):
                # Try the previous month if current month fails
                date = datetime.strptime(args.month, "%Y-%m")
                prev_date = (date.replace(day=1) - timedelta(days=1))
                prev_month = prev_date.strftime("%Y-%m")
                print(f"\n[WARN] Trying previous month: {prev_month}")
                url = f"https://database.lichess.org/standard/lichess_db_standard_rated_{prev_month}.pgn.zst"
                if not download_file(url, compressed_path):
                    print("[ERROR] Failed to download database")
                    return
        else:
            # Try current month, then previous month
            current = datetime.now()
            success = False
            for month in [current, current.replace(day=1) - timedelta(days=1)]:
                month_str = month.strftime('%Y-%m')
                print(f"\n[INFO] Trying month: {month_str}")
                url = f"https://database.lichess.org/standard/lichess_db_standard_rated_{month_str}.pgn.zst"
                if download_file(url, compressed_path):
                    success = True
                    break
            
            if not success:
                print("[ERROR] Failed to download database")
                return
        
        # Decompress the database
        print("\n[INFO] Decompressing database...")
        try:
            total_size = os.path.getsize(compressed_path)
            with open(compressed_path, 'rb') as compressed:
                dctx = zstd.ZstdDecompressor()
                with open(raw_path, 'wb') as raw, tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc="Decompressing",
                    bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'
                ) as pbar:
                    # Create a write callback to update the progress bar
                    class CallbackWriter:
                        def __init__(self, file_obj, progress):
                            self.file_obj = file_obj
                            self.progress = progress
                            self.total_written = 0

                        def write(self, data):
                            self.file_obj.write(data)
                            self.total_written += len(data)
                            self.progress.update(len(data))
                            return len(data)

                    writer = CallbackWriter(raw, pbar)
                    dctx.copy_stream(compressed, writer)
            print("[OK] Decompression completed")
            
            if args.max_games:
                print(f"\n[INFO] Truncating file to approximately {args.max_games:,} games...")
                # Create a temporary file for the truncated data
                truncated_path = raw_path + '.truncated'
                estimated_size = estimate_bytes_for_games(raw_path, args.max_games)
                print(f"[INFO] Estimated size needed: {humanize.naturalsize(estimated_size, binary=True)}")
                
                if truncate_file(raw_path, truncated_path, estimated_size):
                    # Replace original file with truncated version
                    os.remove(raw_path)
                    os.rename(truncated_path, raw_path)
                    print(f"[OK] File truncated successfully")
                else:
                    print(f"[WARN] Failed to truncate file, will process entire file")
            
        except Exception as e:
            print(f"[ERROR] Error decompressing database: {e}")
            if os.path.exists(raw_path):
                os.remove(raw_path)
            return
        
        # Process and filter games
        if not process_games(raw_path, filtered_path, args.min_elo, args.max_games):
            print("[ERROR] No games met the filtering criteria")
            return
        
        # Clean up temporary files
        print("\n[INFO] Cleaning up temporary files...")
        os.remove(compressed_path)
        os.remove(raw_path)
        print("[OK] Cleanup completed")
        
    else:
        print("\n[ERROR] No .pgn.zst file found. You can:")
        print("1. Use --download to download the latest database")
        print("2. Specify an input file with --input-file")

if __name__ == "__main__":
    main() 