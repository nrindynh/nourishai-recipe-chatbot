## Project Information

NourishAI was developed as part of the **CUHK DSPS3803 AI for Social Good Project**.

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


https://github.com/arham-kk/recipe-chatbot/assets/108623726/98e19fd0-39df-428d-afff-968e665b2888


## How it Works

1. The user inputs time available (minutes), number of people, experience level, diet preference and list of available ingredients (comma-separated) into the provided textbox.
2. The system generates custom prompts using the provided ingredients.
3. OpenAI's text generation model generates recipe suggestions based on the prompts.
4. The suggested recipes are displayed in the output textbox.

## Usage

1. Install the required dependencies by running the following command --> `pip install gradio openai`
2. Set up your OpenAI API credentials by replacing `YOUR_API_KEY` with your actual API key in the code
3. Run the application by executing the following command --> `python.app`
4. Access the application by opening the provided URL in your web browser.


