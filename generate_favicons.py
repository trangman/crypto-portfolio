from PIL import Image, ImageDraw
import os

def generate_favicons():
    # Ensure static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')

    # Create a blue chart icon
    def create_icon(size):
        # Create a new image with a transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate dimensions
        padding = size // 8
        bar_width = (size - (padding * 5)) // 3
        
        # Draw three bars in blue
        blue = (41, 68, 151)  # #294497
        
        # First (shortest) bar
        x1 = padding
        y1 = size - padding - (size // 3)
        draw.rectangle([x1, y1, x1 + bar_width, size - padding], fill=blue)
        
        # Second (medium) bar
        x2 = x1 + bar_width + padding
        y2 = size - padding - (size // 2)
        draw.rectangle([x2, y2, x2 + bar_width, size - padding], fill=blue)
        
        # Third (tallest) bar
        x3 = x2 + bar_width + padding
        y3 = size - padding - (size // 1.5)
        draw.rectangle([x3, y3, x3 + bar_width, size - padding], fill=blue)
        
        return img

    # Generate regular favicon (32x32)
    favicon = create_icon(32)
    favicon.save('static/favicon.png')

    # Generate Apple Touch Icon (180x180)
    apple_icon = create_icon(180)
    apple_icon.save('static/apple-touch-icon.png')

if __name__ == '__main__':
    generate_favicons() 