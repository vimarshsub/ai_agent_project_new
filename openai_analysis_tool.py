import base64
import os
from io import BytesIO
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file.")

class OpenAIDocumentAnalysisTool:
    def __init__(self):
        if not OPENAI_API_KEY:
            print("Error: OPENAI_API_KEY is not set.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
                # A simple test, like listing models, could be done here if needed
                # self.client.models.list() 
            except Exception as e:
                print(f"Error initializing OpenAI client: {e}")
                self.client = None
        self.model = "gpt-4o-mini" # Using the specified GPT-4o model

    def _convert_pdf_to_base64_images(self, pdf_path, max_pages=5):
        """Converts PDF pages to a list of base64 encoded image strings. Returns list or error string."""
        base64_images = []
        try:
            # Check if poppler is installed and accessible by pdf2image
            # This is a common point of failure if dependencies are missing
            try:
                info = pdfinfo_from_path(pdf_path, poppler_path=None) # Use system poppler
                actual_max_pages = min(info["Pages"], max_pages)
            except Exception as pe:
                # If pdfinfo fails, it might indicate poppler issues or bad PDF
                print(f"Could not get PDF info (possibly poppler issue or invalid PDF): {pe}")
                # Fallback to trying to convert without knowing total pages, up to max_pages
                actual_max_pages = max_pages 
                # It might be better to return an error here if pdfinfo fails, as conversion will likely also fail.
                # return f"Error: Could not process PDF info for {os.path.basename(pdf_path)}. Ensure poppler-utils is installed and PDF is valid."

            if actual_max_pages == 0:
                return f"Error: PDF file {os.path.basename(pdf_path)} appears to have 0 pages or could not be read."

            images = convert_from_path(pdf_path, first_page=1, last_page=actual_max_pages, poppler_path=None)
            
            for i, image in enumerate(images):
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                base64_images.append(img_str)
                print(f"Converted page {i+1} of PDF 	'{os.path.basename(pdf_path)}	' to image.")
            
            if not base64_images:
                 return f"Error: Could not convert any pages from PDF: {os.path.basename(pdf_path)}. The PDF might be empty, corrupted, or password-protected."
            return base64_images

        except Exception as e:
            # Catching specific pdf2image errors could be more granular
            error_msg = f"Error converting PDF 	'{os.path.basename(pdf_path)}	' to images: {str(e)}. Check if poppler-utils is installed and the PDF is valid."
            print(error_msg)
            return error_msg

    def analyze_document_content(self, pdf_path, analysis_type="summarize", custom_prompt=None, max_pages_to_analyze=5):
        """
        Analyzes the content of a PDF document by converting its pages to images and sending them to OpenAI.
        Returns the analysis result from OpenAI, or an error message string.
        """
        if not self.client:
            return "Error: OpenAI client not initialized. Check API key and configuration."

        if not pdf_path or not isinstance(pdf_path, str):
            return "Error: Invalid PDF path provided for analysis."
        if not os.path.exists(pdf_path):
            return f"Error: PDF file not found at path: {pdf_path}"
        if not pdf_path.lower().endswith(".pdf"):
            return f"Error: File 	'{os.path.basename(pdf_path)}	' is not a PDF. Only PDF analysis is supported."

        print(f"Starting analysis for PDF: {os.path.basename(pdf_path)}, type: {analysis_type}, max pages: {max_pages_to_analyze}")
        conversion_result = self._convert_pdf_to_base64_images(pdf_path, max_pages=max_pages_to_analyze)

        if isinstance(conversion_result, str) and conversion_result.startswith("Error:"):
            return conversion_result # Propagate error from conversion
        
        base64_images = conversion_result

        if not base64_images:
            # This case should be caught by the error string check above, but as a safeguard:
            return "Error: No images were generated from the PDF for analysis."

        if custom_prompt:
            prompt_text = custom_prompt
        elif analysis_type == "summarize":
            prompt_text = "Summarize the content of this document based on the provided pages. Provide a concise overview."
        elif analysis_type == "extract_action_items":
            prompt_text = "Extract all action items, deadlines, and responsible individuals/teams mentioned in this document based on the provided pages. If none, state that clearly."
        elif analysis_type == "sentiment":
            prompt_text = "Analyze the overall sentiment of this document based on the provided pages. Is it positive, negative, or neutral? Explain briefly."
        else:
            prompt_text = f"Analyze the content of this document based on the provided pages. The user requested analysis type: 	'{analysis_type}	'."

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                ]
            }
        ]
        for b64_img in base64_images:
            messages[0]["content"].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_img}",
                        "detail": "low" # Use low detail for potentially faster processing and lower cost if high res not needed
                    }
                }
            )
        
        try:
            print(f"Sending {len(base64_images)} image(s) from 	'{os.path.basename(pdf_path)}	' to OpenAI for 	'{analysis_type}	' analysis...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000, # Adjust as needed
                timeout=60 # Added timeout
            )
            analysis_result = response.choices[0].message.content
            print(f"Analysis received from OpenAI for {os.path.basename(pdf_path)}.")
            return analysis_result
        except Exception as e:
            error_msg = f"Error during OpenAI API call for 	'{os.path.basename(pdf_path)}	': {str(e)}"
            print(error_msg)
            return error_msg

# Example Usage (for testing purposes, will be removed or commented out)
if __name__ == '__main__':
    analyzer = OpenAIDocumentAnalysisTool()
    if not analyzer.client:
        print("OpenAI Analysis Tool could not be initialized. Exiting tests.")
        exit()

    sample_pdf_path = "/home/ubuntu/ai_agent_project/sample_test.pdf" 

    if not os.path.exists(sample_pdf_path):
        try:
            from fpdf import FPDF 
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="This is page 1 of a sample PDF for testing OpenAI analysis.", ln=1, align="C")
            pdf.cell(200, 10, txt="The overall mood is optimistic about future projects.", ln=1, align="L")
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Page 2: Action Item - Review Q3 budget by next Friday. Responsible: Finance Team.", ln=1, align="L")
            pdf.cell(200, 10, txt="Another task: Prepare presentation for Monday meeting. Assigned to: Marketing Dept.", ln=1, align="L")
            pdf.output(sample_pdf_path, "F")
            print(f"Created dummy PDF: {sample_pdf_path}")
        except ImportError:
            print("Please install fpdf2 to create a dummy PDF for testing: pip install fpdf2")
            exit()
        except Exception as e:
            print(f"Error creating dummy PDF: {e}")
            exit()

    if os.path.exists(sample_pdf_path):
        print(f"\n--- Analyzing PDF: {os.path.basename(sample_pdf_path)} ---")
        
        summary = analyzer.analyze_document_content(sample_pdf_path, analysis_type="summarize", max_pages_to_analyze=2)
        print(f"\nSummary:\n{summary}")

        action_items = analyzer.analyze_document_content(sample_pdf_path, analysis_type="extract_action_items", max_pages_to_analyze=2)
        print(f"\nAction Items:\n{action_items}")

        sentiment = analyzer.analyze_document_content(sample_pdf_path, analysis_type="sentiment", max_pages_to_analyze=2)
        print(f"\nSentiment:\n{sentiment}")

        # Test with a non-PDF file
        non_pdf_path = "/home/ubuntu/ai_agent_project/test.txt"
        with open(non_pdf_path, "w") as f:
            f.write("This is a test text file.")
        print(f"\n--- Analyzing Non-PDF: {os.path.basename(non_pdf_path)} ---")
        non_pdf_analysis = analyzer.analyze_document_content(non_pdf_path)
        print(f"\nNon-PDF Analysis Result:\n{non_pdf_analysis}")
        os.remove(non_pdf_path)

        # Test with a non-existent file
        print(f"\n--- Analyzing Non-Existent File ---")
        non_existent_analysis = analyzer.analyze_document_content("/tmp/non_existent_sample.pdf")
        print(f"\nNon-Existent File Analysis Result:\n{non_existent_analysis}")

        # Clean up dummy PDF after tests
        # os.remove(sample_pdf_path)
        # print(f"\nRemoved dummy PDF: {sample_pdf_path}")
    else:
        print(f"Test PDF not found: {sample_pdf_path}. Skipping example usage.")


