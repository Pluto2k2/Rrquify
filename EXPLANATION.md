# Code Explanation

The Requify classifier is built using Python and the `customtkinter` library for the user interface. Here is a brief overview of the main components:

1. **User Interface (`main.py`)**
   - Built with `customtkinter` for a modern, dark/light mode compatible desktop experience.
   - Contains three main tabs: Classify (single requirement), Batch (file upload), and Statistics (data visualization).
   - Uses `tkinter` threads to keep the UI responsive while making API calls.

2. **Classification Logic**
   - The app uses the Groq API to query the Llama 3.3 70B model.
   - We define multiple prompt strategies (Zero-Shot, Few-Shot) in the `PROMPTS` dictionary.
   - The `classify_requirement` function handles the API request, passing the selected prompt and the user's text to the model.
   - The model is instructed to return only the category label (e.g., "F", "PE", "SE"), which is then mapped back to a full description.

3. **Batch Processing & Statistics**
   - Batch processing reads `.csv` or `.txt` files and processes each line/row sequentially.
   - Results are stored in memory and can be exported as a new `.csv` file.
   - The Statistics tab reads the session history to generate a distribution chart using a standard `tkinter.Canvas`.

4. **Environment Variables**
   - API keys are loaded securely from a `.env` file using `python-dotenv`. This keeps the API key out of the source code.
