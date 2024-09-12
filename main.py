import os
import time
import logging
import traceback
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import yaml
import urllib3
import json
import google.generativeai as genai
import requests
from urllib3.exceptions import InsecureRequestWarning
import ssl
from data_collector import DataCollector  # Add this import

# Add this at the beginning of your script to suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    with open('config.yaml', 'r') as config_file:
        return yaml.safe_load(config_file)

with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

genai.configure(api_key=config['gemini']['api_key'])

# Test the Gemini model
try:
    model = genai.GenerativeModel(config['gemini']['model'])
    response = model.generate_content("Hello, world!")
    logging.info(f"Test Gemini response: {response.text}")
except Exception as e:
    logging.error(f"Error testing Gemini model: {str(e)}")
    logging.debug(f"Error details: {traceback.format_exc()}")

def create_agents():
    gemini_config = {
        "model": config['gemini']['model'],
        "api_key": config['gemini']['api_key'],
        "api_type": config['gemini']['api_type']
    }

    user_proxy = UserProxyAgent(
        name="Human",
        system_message="A human user interacting with AI agents to analyze WiFi network data.",
        human_input_mode="ALWAYS",
        code_execution_config={
        "work_dir": "coding",
            "use_docker": False
        }  # Disable code execution
    )

    network_analyst = AssistantAgent(
        name="NetworkAnalyst",
        system_message="You analyze network data and provide recommendations based on the given prompt.",
        llm_config=gemini_config
    )

    return user_proxy, network_analyst

def run_group_chat():
    config = load_config()
    data_collector = DataCollector(config)
    
    try:
        logging.info("Starting data collection")
        data_collector.collect_data()
        logging.info("Data collection completed successfully")
    except Exception as e:
        logging.error(f"Error during data collection: {str(e)}")
        return f"Data collection failed: {str(e)}"

    logging.info("Creating agents")
    user_proxy, network_analyst = create_agents()
    logging.info("Agents created successfully")

    # Generate context for the static prompt
    logging.info("Generating static prompt")
    with open('device_config.json', 'r') as f:
        devices = json.load(f)
    
    num_devices = len(devices)
    num_aps = sum(1 for device in devices if device.get('type') == 'uap')

    static_prompt = f"""
    Analyze the UniFi network data and provide optimization recommendations based on the following context:

    Network Context:
    - This is a UniFi network with {num_devices} total devices, including {num_aps} access points.
    - We want to optimize the network's performance.
    - The following data files are available for analysis:
      1. device_config.json: Contains configuration details of all network devices.
      2. performance_data.json: Includes daily site performance statistics.
      3. wifi_scans.json: Contains WLAN configuration data.
      4. rf_environment.json: Provides RF environment data for access points.
      5. client_devices.json: Lists all client devices connected to the network.
      6. historical_data.json: Contains hourly site statistics for the past 7 days.
      7. channel_utilization.json: Provides channel utilization data.

    Please provide a comprehensive analysis of the network, including:
    1. Overall network health and performance
    2. Identification of potential issues or bottlenecks
    3. Recommendations for optimizing WiFi coverage and performance
    4. Suggestions for improving channel utilization and reducing interference
    5. Any other insights or recommendations based on the provided data

    Here are the data files:

    <<<device_config.json>>>
    {json.dumps(json.load(open('device_config.json', 'r')), separators=(',', ':'))}

    <<<performance_data.json>>>
    {json.dumps(json.load(open('performance_data.json', 'r')), separators=(',', ':'))}

    <<<wifi_scans.json>>>
    {json.dumps(json.load(open('wifi_scans.json', 'r')), separators=(',', ':'))}

    <<<rf_environment.json>>>
    {json.dumps(json.load(open('rf_environment.json', 'r')), separators=(',', ':'))}

    <<<client_devices.json>>>
    {json.dumps(json.load(open('client_devices.json', 'r')), separators=(',', ':'))}

    <<<historical_data.json>>>
    {json.dumps(json.load(open('historical_data.json', 'r')), separators=(',', ':'))}

    <<<channel_utilization.json>>>
    {json.dumps(json.load(open('channel_utilization.json', 'r')), separators=(',', ':'))}
    """
    logging.info("Static prompt generated")
    #logging.info(static_prompt)
    # Start the conversation with NetworkAnalyst
    logging.info("Generating initial analysis")
    try:
        # analysis_response = network_analyst.generate_reply(user_proxy, static_prompt)
        analysis_response = user_proxy.initiate_chat(network_analyst, message=static_prompt)
        logging.info(f"Initial analysis generated successfully. Response length: {len(analysis_response)}")
        if not analysis_response.strip():
            logging.warning("Initial analysis response is empty")
        logging.debug(f"Raw response: {analysis_response}")
    except Exception as e:
        logging.error(f"Error generating initial analysis: {str(e)}")
        logging.debug(f"Error details: {traceback.format_exc()}")
        return f"Initial analysis failed: {str(e)}"

    print("\nInitial analysis:")
    print(analysis_response)

    # Allow for follow-up questions directly with NetworkAnalyst
    while True:
        user_input = user_proxy.get_user_input("Enter your question: ")
        if user_input.lower() == 'exit':
            break
        
        if user_input:
            logging.info("Generating response to user question")
            try:
                response = network_analyst.generate_reply(user_proxy, user_input)
                logging.info(f"Response generated successfully. Response length: {len(response)}")
                if not response.strip():
                    logging.warning("Response is empty")
                logging.debug(f"Raw response: {response}")
            except Exception as e:
                logging.error(f"Error generating response: {str(e)}")
                logging.debug(f"Error details: {traceback.format_exc()}")
                print(f"Error generating response: {str(e)}")
                continue

            print("\nNetworkAnalyst's response:")
            print(response)

    return "Analysis completed."

# Main execution
if __name__ == "__main__":
    try:
        analysis_result = run_group_chat()
        print("\nAnalysis result:")
        print(analysis_result)
    except Exception as e:
        logging.error(f"An error occurred during execution: {str(e)}")
        logging.debug(f"Error details: {traceback.format_exc()}")



