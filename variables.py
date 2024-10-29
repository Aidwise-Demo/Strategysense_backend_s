import anthropic
from dotenv import load_dotenv
import motor.motor_asyncio
import os

# Load environment variables from .env file
load_dotenv()

claude_client =anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY_AIDWISE'))

MONGO_URI = os.getenv('MONGO_URI_AIDWISE_DEMO')
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = mongo_client.ClaudeDataExtractor 
collection = db.Uploaded_Files
collection1 = db.Pages
collection2 = db.Processing
collection3 = db.Page_Data

process_clients = []
extract_clients = []

def initialize_project_info():
  project_info = {
      'File_Name': '',
      'Image_String': '',
      'Project_Name': '',
      'Context': '',
      'Overview': '',
      'Owner': '',
      'Stakeholders': '',
      'Status': '',
      'Initiative_Details': '',
      'List_of_Sub_Initiatives': '',
      'Interdependencies': '',
      'Risks_and_Mitigations': '',
      'Key_Performance_Indicators': '',
      'Budget': '',
      'Summary':'',
      'Path': '',
      'DB_Id': 'None',
      'Skip': True,
      'Extracted': 'No'
  }
  return project_info
class Prompts:
    prompts = {
    'Project_Name': "From the above Image, state the Name of the Project, It should be Text With the Biggest Font. Do not output any other sentences.",
    'Context': "From the above Image, give the Strategic Objectives and Strategic Programs in key:value pair(Strategic objective: value,Strategic Program: value), in '|' separated format. Do not output any other sentences.",
    'Overview': "From the above Image, give the info in (Program/Initiative) Overview section in key: value pairs, in '|' separated format one after the other.Do not include owners. Do not output any other sentences.",
    'Owner': """
        Please carefully examine the image and extract the following information:
        - The names of the Program Sponsors 
        - The names of the Project Managers
        There may be multiple Program Sponsors and/or Project Managers listed.
        Output the information you extract in the following format:
        Program Sponsors: <name(s)> | Project Managers: <name(s)>  
        Use the exact keys "Program Sponsors" and "Project Managers". If there are multiple values for a key, separate them with commas. Do not output any other text besides these key:value pairs separated by a '|' character.""",
    'Stakeholders': "From the above Image, give the name of all the stakeholders in '|' separated format. Do not output any other sentences.",
    'Status': "From the above Image, give the current status of the project. Do not output any other sentences.",
    'Initiative_Details': "From the above Image, give the Information of Initiative Details section in key:value pairs(Initiative description: values ,Key deliverables: values), in'|' separated format one after the other. Even if 'Key deliverables' are seperated in points, use '|' to separate them. Give the names of the subsections inside 'Initiative Details' section only . 'Initiative Details' is not a subsection. Do not Include 'List of Sub-Initiatives'. Do not output any other sentences.",
    'List_of_Sub_Initiatives': "From the given image, if the section 'List of Sub-Initiatives' is present, state the information in that section in '|' separated format. If the section is not present, output 'Not Found' concisely without using any other sentences, without any additional text/sentence before or after.",
    'Interdependencies': "From the above image, only give the Information in Interdependencies section in '|' separated format (do not use '\n'). First, give the names of the columns. Do not include risks. Do not output any other sentences.",
    'Risks_and_Mitigations': "From the above Image, give the Risk then it's Impact Level in '|' separated format only(no newline). First give the names of the columns. Recheck the Last Impact level. Do not output any other sentences.",
    'Key_Performance_Indicators': """From the above image, state all the Key Performance Indicators(KPI), followed by the targets(in Year:Value pairs, separately) of each KPI in JSON. Separate the KPI's into Main KPI and Support KPI. Check the LAST KPI again, Do not miss it. If no Support KPI is found, maintain the structure of the JSON and mimic the previous KPI's and output 'Not Found' in value fields. Do not output any other sentences.
    Example JSON Structure: - 
    "Key_Performance_Indicators": [
    {
      "kpi_type": "Main KPI",
      "data": [
        {
          "KPI": "Early detection of common cancers \u2013 Breast",
          "Targets": {
            "2024": "80.5%",
            "2025": "83%",
            "2026": "85.5%"
          }
        },
        {
          "KPI": "Early detection of common cancers \u2013 Colorectal",
          "Targets": {
            "2024": "44.5%",
            "2025": "47%",
            "2026": "49.5%"
          }
        },
        {
          "KPI": "Early detection of common cancers \u2013 Cervical",
          "Targets": {
            "2024": "68.5%",
            "2025": "71%",
            "2026": "73.5%"
          }
        },
        {
          "KPI": "Prevalence of adult obesity",
          "Targets": {
            "2024": "23.4%",
            "2025": "21.4%",
            "2026": "19.4%"
          }
        },
        {
          "KPI": "Prevalence of childhood obesity",
          "Targets": {
            "2024": "17.80%",
            "2025": "16.8%",
            "2026": "15.80%"
          }
        }
      ]
    },
    {
      "kpi_type": "Support KPI",
      "data": [
        {
          "KPI": "% Establish screening coverage",
          "Targets": {
            "2024": "7%",
            "2025": "7%",
            "2026": "7%"
          }
        }
      ]
    }
  ]
  Make sure outputted JSON is in the correct format and doesnt have any extra fields""",
    'Budget': "From the above Image, state the Budget of the Project. Output 'Not Present' if the Budget is not found. Do not output any other sentences.",
    'Summary': "From the above Image, give a comprehensive summary of all the text in the Image."
    }
    # 'Key_Performance_Indicators': """From the above Image, give the Key Performance Indicators(KPI), followed by the targets of each KPI followed by the next KPI in JSON. Seperate the KPI's into Main KPI and Support KPI. 'Support KPI' is not a KPI. Make sure to give the targets of the Last Main KPI. Do not output any other sentences.""",
    # 'List_of_Sub_Initiatives': "From the above Image, state the Information in the 'List of Sub-Initiatives' section in '|' separated format. Only Say 'Not Present' Only if the section is not found and Do not output any other sentences before or after 'Not Present'. Even if they are seperated in points, use '|' to separate them. 'Key Outcomes/Deliverables' should not be included. Do not output any other sentences.",
    # prompt_Project_Name = "From the above Image, state the Name of the Project, It should be Text With the Biggest Font. Do not output any other sentences."
    # prompt_Objective = "From the above Image, give the Strategic Objectives and Strategic Programs in comma separated format. Do not output any other sentences."
    # prompt_Overview = "From the above Image, give the info in Program Overview section in comma separated format one after the other. Do not output any other sentences."
    # prompt_Owner = "From the above Image, give the name of Program Sponsors, and Project Managers (Might be Multiple for each) in comma separated format. Do not output any other sentences. "
    # prompt_Stakeholder = "From the above Image, give the name of all the stakeholders in comma separated format. Do not output any other sentences."
    # prompt_Status = "From the above Image, give the current status of the project. Do not output any other sentences."
    # prompt_Initiative = "From the above Image, give the Information in Initiative Details section in '|' separated format one after the other.Give the names of the subsections.Do not output any other sentences."
    # prompt_Interdep = "From the above Image, give the Information in Interdepencies section in '|' separated format.First give the names of the subsections.Do not output any other sentences."
    # prompt_Risk = "From the above Image, give the Risk then it's Impact Level in comma separated format.Recheck the Last Impact level.Do not output any other sentences."
    # prompt_KPI = """From the above Image, give the Key Peformance Indicators(KPI), followed by the targets of each KPI followed by the next KPI in comma separated format.
    #                 Seperate the KPI's into Main KPI and Support KPI.
    #                 'Support KPI' is not a KPI.
    #                 Make sure to give the targets of the Last Main KPI.
    #                 Do not output any other sentences."""
    # prompt_Budget = "From the above Image, state the Budget of the Project. Output 'Not Present' if the Budget is not found. Do not output any other sentences."
    # prompt_Milestones = "From the above Image, state the Milestones of the Project in '|' separated format. Do not output any other sentences."
    # Do Not change the prompts below
    prompt_Milestones_check = "Does this image contain a 'MILESTONES' section containing outcomes and with weights. Answer with 'Yes' or 'No' only."
    prompt_check = "Does this image contain 'CONTENTS'. Answer with 'Yes' or 'No' Only. Do not include periods in your answer."
    prompt_blank = "Is this Image blank or not? Answer with 'Yes' or 'No' Only. Do not include periods in your answer."
    charter_check = "Does this image appear to be an initiative charter for a project. An Initiative charter contains fields like Risks, KPI, Owners, Stakeholders.Answer with 'Yes' or 'No' Only. Do not include periods in your answer."