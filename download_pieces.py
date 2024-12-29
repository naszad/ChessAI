import os
import requests
from pathlib import Path
from PIL import Image
import io

# Create pieces directory if it doesn't exist
pieces_dir = Path("pieces")
pieces_dir.mkdir(exist_ok=True)

# Dictionary mapping piece symbols to their info (url and filename)
PIECE_INFO = {
    # White pieces
    'K': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wk.png', 'filename': 'KING_WHITE.png'},
    'Q': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wq.png', 'filename': 'QUEEN_WHITE.png'},
    'R': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wr.png', 'filename': 'ROOK_WHITE.png'},
    'B': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wb.png', 'filename': 'BISHOP_WHITE.png'},
    'N': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wn.png', 'filename': 'KNIGHT_WHITE.png'},
    'P': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wp.png', 'filename': 'PAWN_WHITE.png'},
    # Black pieces
    'k': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bk.png', 'filename': 'KING_BLACK.png'},
    'q': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bq.png', 'filename': 'QUEEN_BLACK.png'},
    'r': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/br.png', 'filename': 'ROOK_BLACK.png'},
    'b': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bb.png', 'filename': 'BISHOP_BLACK.png'},
    'n': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bn.png', 'filename': 'KNIGHT_BLACK.png'},
    'p': {'url': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bp.png', 'filename': 'PAWN_BLACK.png'},
}

def download_piece_images():
    # Set up headers for the request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.chess.com/',
    }
    
    print("Downloading chess piece images...")
    session = requests.Session()
    session.headers.update(headers)
    
    # First, verify all existing files
    existing_files = []
    for piece_info in PIECE_INFO.values():
        output_path = pieces_dir / piece_info['filename']
        if output_path.exists():
            existing_files.append(piece_info['filename'])
    
    if existing_files:
        print(f"Found existing pieces: {', '.join(existing_files)}")
        print("Deleting existing files to ensure fresh download...")
        for filename in existing_files:
            (pieces_dir / filename).unlink()
    
    for piece_symbol, piece_info in PIECE_INFO.items():
        url = piece_info['url']
        filename = piece_info['filename']
        output_path = pieces_dir / filename
        
        print(f"\nProcessing {filename}:")
        print(f"URL: {url}")
        print(f"Output path: {output_path}")
        
        try:
            # Download PNG with proper headers
            print(f"Downloading {filename}...")
            response = session.get(url)
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                # Try to open and process the image
                img = Image.open(io.BytesIO(response.content))
                print(f"Image mode: {img.mode}, Size: {img.size}")
                
                # Ensure image has alpha channel
                if img.mode != 'RGBA':
                    print(f"Converting {img.mode} to RGBA")
                    img = img.convert('RGBA')
                
                # Resize while maintaining aspect ratio
                img.thumbnail((80, 80), Image.Resampling.LANCZOS)
                print(f"Resized to: {img.size}")
                
                # Create new image with alpha channel
                new_img = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
                
                # Paste resized image in center
                x = (80 - img.width) // 2
                y = (80 - img.height) // 2
                new_img.paste(img, (x, y), img)
                
                # Save with transparency
                new_img.save(output_path, 'PNG')
                print(f"Successfully saved {filename}")
            else:
                print(f"Failed to download {filename} (Status code: {response.status_code})")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Verify final results
    print("\nFinal verification:")
    missing_pieces = []
    for piece_info in PIECE_INFO.values():
        output_path = pieces_dir / piece_info['filename']
        if not output_path.exists():
            missing_pieces.append(piece_info['filename'])
    
    if missing_pieces:
        print(f"Warning: Missing pieces: {', '.join(missing_pieces)}")
    else:
        print("All pieces downloaded successfully!")

if __name__ == "__main__":
    download_piece_images() 