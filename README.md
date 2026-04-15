## Project Description

NourishAI is an AI-powered recipe chatbot developed for the **CUHK DSPS3803 AI for Social Good Project**. 

The system allows users to input ingredients, cooking constraints (such as time and difficulty), and dietary preferences to generate personalised recipe suggestions. It leverages the **DeepSeek API** for intelligent response generation and uses **Gradio** to provide an interactive web-based interface.

The project was built by extending an existing open-source repository and transforming it into a fully functional prototype, including backend logic, prompt engineering, API integration, and user interface design.

## Team Members

- Yiu Ka Ying (1155176884)
- Zhu Chenyi (1155188073)
- Wong Pak Hei (1155194968)
- Nurin Diyanah Binte Awaludin (1155264290)

## Credits

This project is based on:
https://github.com/arham-kk/recipe-chatbot

Original author: arham-kk  
This version includes additional modifications and improvements.

## My Contributions
Led the end-to-end development of the working prototype, including:

- Designed the overall system architecture of the chatbot application using Python
- Integrated the DeepSeek API to enable intelligent recipe querying and response generation
- Developed the core chatbot logic, including prompt handling and response processing
- Built the user interface using Gradio to create an interactive and user-friendly experience
- Adapted and extended the base repository into a fully functional application
- Implemented data handling for recipe inputs and outputs
- Conducted testing, debugging, and iterative improvements to enhance usability and performance

# Recipe Suggestions Chatbot

This project utilizes DeepSeek API to suggest recipes based on a list of ingredients & prefrences provided by the user.


https://github.com/user-attachments/assets/04dc3989-1452-4b98-aaad-4cb99871041d



## How it Works

1. The user inputs time available (minutes), number of people, experience level, diet preference and list of available ingredients (comma-separated) into the provided textbox.
2. The system generates custom prompts using the provided ingredients.
3. OpenAI's text generation model generates recipe suggestions based on the prompts.
4. The suggested recipes are displayed in the output textbox.

## Usage

### 1. Clone the repository
```bash
git clone https://github.com/nrindynh/nourishai-recipe-chatbot.git
cd nourishai-recipe-chatbot
```

### 2. Set up a virtual environment
Create a virtual environment:
```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

### 3. Install dependencies
If you have a `requirements.txt` file:
```bash
pip install -r requirements.txt
```

If not, install manually:
```bash
pip install gradio python-dotenv requests
```

### 4. Configure environment variables
Create a `.env` file in the root directory and add your DeepSeek API key:
```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 5. Run the application
```bash
python app.py
```

### 6. Access the application
After running the script, a local Gradio URL will be displayed in the terminal (e.g., `http://127.0.0.1:7860`). Open this link in your browser to use the chatbot.

### 7. Interact with the chatbot
1. Enter the following inputs:
   - Time available (minutes)
   - Number of people
   - Cooking experience level
   - Dietary preference
   - Available ingredients (comma-separated)
2. Submit the form
3. The system will:
   - Generate a structured prompt based on your inputs
   - Send the request to the DeepSeek API
   - Receive a generated recipe response
4. The recipe output will be displayed in the interface, including:
   - Ingredients
   - Step-by-step instructions
3. Run the application by executing the following command --> `python.app`
4. Access the application by opening the provided URL in your web browser.


