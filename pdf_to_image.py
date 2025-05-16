#!/usr/bin/env python3
"""
PDF to Image Converter Script

This script converts PDF files to images for AI analysis.
It uses the pdf2image library to convert PDFs to PNG images.
"""

import os
import sys
import argparse
from pdf2image import convert_from_path
import requests
import json
import base64

def convert_pdf_to_images(pdf_path, output_dir, dpi=300, fmt='png'):
    """
    Convert a PDF file to images.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Directory to save the images
        dpi (int): DPI for the output images
        fmt (str): Format for the output images (png, jpg, etc.)
    
    Returns:
        list: List of paths to the generated images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the base name of the PDF file without extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    base_name = base_name.replace(" ", "_")
    
    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=dpi)
    
    # Save images
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"{base_name}_page_{i+1}.{fmt}")
        image.save(image_path, fmt.upper())
        image_paths.append(image_path)
        print(f"Saved {image_path}")
    
    return image_paths

def analyze_image_with_openai(image_path, api_key):
    """
    Analyze an image using OpenAI's GPT-4 Vision API.
    
    Args:
        image_path (str): Path to the image file
        api_key (str): OpenAI API key
    
    Returns:
        dict: Analysis results from the API
    """
    # Read the image file and encode it as base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o-mini",  # Using GPT-4o mini as specified
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this image and describe what you see. Identify any text, forms, or structured content. Suggest how this content might be used or improved."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return {"error": response.text}

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to images and analyze with OpenAI')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output-dir', default='converted_images', help='Directory to save the images')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for the output images')
    parser.add_argument('--format', default='png', help='Format for the output images')
    parser.add_argument('--analyze', action='store_true', help='Analyze the images with OpenAI')
    parser.add_argument('--api-key', help='OpenAI API key')
    
    args = parser.parse_args()
    
    # Convert PDF to images
    image_paths = convert_pdf_to_images(args.pdf_path, args.output_dir, args.dpi, args.format)
    
    # Analyze images if requested
    if args.analyze:
        if not args.api_key:
            print("Error: API key is required for analysis")
            sys.exit(1)
        
        print("\nAnalyzing images with OpenAI...")
        for image_path in image_paths:
            print(f"\nAnalyzing {image_path}...")
            result = analyze_image_with_openai(image_path, args.api_key)
            
            # Save analysis result to a text file
            result_path = f"{os.path.splitext(image_path)[0]}_analysis.json"
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Print the analysis result
            if "error" not in result:
                print("\nAnalysis result:")
                print(result["choices"][0]["message"]["content"])
            else:
                print(f"Error: {result['error']}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
