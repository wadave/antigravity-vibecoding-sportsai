from PIL import Image, ImageDraw, ImageFont
import os

def generate_architecture_diagram(output_path="architecture.png"):
    img = Image.new('RGB', (800, 600), color=(30, 30, 30))
    d = ImageDraw.Draw(img)
    
    # Define colors
    bg_color = (30, 30, 30)
    box_color = (50, 50, 50)
    text_color = (255, 255, 255)
    arrow_color = (100, 100, 100)
    
    # Draw boxes
    # Frontend
    d.rectangle([50, 250, 200, 350], fill=box_color, outline=text_color)
    d.text((75, 290), "React Frontend", fill=text_color)
    
    # Backend
    d.rectangle([300, 250, 450, 350], fill=box_color, outline=text_color)
    d.text((325, 290), "FastAPI Backend", fill=text_color)
    
    # GCS
    d.rectangle([550, 150, 700, 250], fill=box_color, outline=text_color)
    d.text((575, 190), "GCS Bucket", fill=text_color)
    
    # Gemini
    d.rectangle([550, 350, 700, 450], fill=box_color, outline=text_color)
    d.text((575, 390), "Gemini AI", fill=text_color)
    
    # Draw arrows
    d.line([200, 300, 300, 300], fill=arrow_color, width=5) # Frontend to Backend
    d.line([450, 300, 550, 200], fill=arrow_color, width=5) # Backend to GCS
    d.line([450, 300, 550, 400], fill=arrow_color, width=5) # Backend to Gemini
    
    img.save(output_path)

if __name__ == "__main__":
    generate_architecture_diagram()
